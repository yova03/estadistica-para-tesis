#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER DE REPOSITORIOS DE DATOS ARQUEOLOGICOS
==============================================
Busca en varios repositorios cientificos a la vez y devuelve una tabla con
todo lo que encuentre: titulo, autores, anio, DOI y enlace. Sirve para armar
el estado de la cuestion de una tesis, ver que datos ya existen sobre una
zona o un periodo, y citar sin inventar referencias.

Sirve cuando hay muchos elementos: recorre la paginacion de cada repositorio
hasta juntar lo que le pidas, sin que tengas que ir uno por uno.

REPOSITORIOS QUE CONSULTA
-------------------------
  zenodo      Zenodo (CERN). Investigacion y datos abiertos. Sin clave.
  dataverse   Harvard Dataverse. Datos de investigacion. Sin clave.
  ariadne     ARIADNE. Agregador europeo de arqueologia: 2,6 millones de
              registros, e indexa a su vez ADS, tDAR y Open Context.
  osf         Open Science Framework. Busca solo en titulos. Sin clave.

Todos responden sin registro ni clave. Los datos son de sus duenos: el
programa solo lee los metadatos que cada repositorio publica.

COMO SE USA
-----------
  Buscar y guardar la tabla:

      python scraper_arqueologia.py "arqueologia Peru" --maximo 100

  Elegir repositorios y anios:

      python scraper_arqueologia.py "ceramica Nasca" -r zenodo,ariadne --desde 2015

  Sin argumentos: modo interactivo, preguntando todo.

      python scraper_arqueologia.py

  Ver todas las opciones:

      python scraper_arqueologia.py --ayuda

QUE PRODUCE
-----------
  Un archivo CSV (que Excel abre directamente) con una fila por hallazgo:

      repositorio, titulo, autores, anio, fecha, tipo, idioma, pais,
      doi, url, materias, descripcion

  Opcionalmente, el JSON crudo de cada repositorio con --json.

LO QUE HAY QUE SABER ANTES DE USARLO
------------------------------------
  **Busca en espanol y en ingles.** Esto no es un adorno: los catalogos de
  ARIADNE y de Zenodo son casi enteros en ingles, y Dataverse hace busquedas
  con OR. Medido el 2026-09-21 con "arqueologia Peru":

      Zenodo .......... 70      (si entiende espanol)
      Dataverse ....... 1451    (pero los primeros son encuestas de papa)
      ARIADNE ......... 0       (exige todas las palabras y en ingles)
      OSF ............. 0       (busca la frase literal en el titulo)

  Con "archaeology Peru", en cambio, todos devuelven arqueologia de verdad.
  Por eso el programa traduce los terminos con un glosario propio y busca
  las dos versiones. Si no quieres, usa --solo-espanol.

  **Corrige el OR de Dataverse y OSF.** Esos dos no saben exigir que
  aparezcan todas las palabras, asi que el programa descarta despues los
  registros que no las tienen. Sin eso, buscar "arqueologia Peru" devuelve
  "Peru Potato Producer Survey". Se puede desactivar con --sin-filtro.

  - Los anios se filtran despues de descargar: si pides desde 2015, el
    programa igual descarga y luego descarta.
  - Se respeta una pausa entre peticiones para no abusar de los servidores.
  - tDAR, ADS y Open Context bloquean el acceso automatico. Por eso no se
    consultan directo: su contenido llega por ARIADNE.

Autor: material de asesoria de tesis. Licencia MIT.
"""

import argparse
import csv
import html
import json
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

VERSION = "2.0"

# Algunos servidores usan certificados que Windows no reconoce desde Python.
_CONTEXTO = ssl.create_default_context()

CABECERAS = {
    "User-Agent": ("ScraperArqueologia/2.0 (busqueda academica; "
                   "contacto a traves del repositorio de GitHub)"),
    "Accept": "application/json",
}

# Tiempo maximo de espera por peticion, en segundos.
ESPERA = 45

# Cuantos resultados se piden por pagina.
TAMANO_PAGINA = 25

# Cuantas veces el maximo se explora como tope cuando hay que descartar
# registros que no cumplen el filtro (evita dar vueltas sin fin).
FACTOR_EXPLORACION = 8


# ============================================================
# 1. UTILIDADES
# ============================================================

def imprimir(texto=""):
    """Muestra en pantalla sin romperse si la consola no admite el caracter."""
    try:
        print(texto)
    except UnicodeEncodeError:
        codificacion = sys.stdout.encoding or "ascii"
        print(texto.encode(codificacion, "replace").decode(codificacion, "replace"))


def limpiar(texto):
    """Quita saltos de linea y espacios de sobra."""
    if texto is None:
        return ""
    return re.sub(r"\s+", " ", str(texto)).strip()


def limpiar_html(texto):
    """Quita las etiquetas y los codigos de HTML.

    Zenodo y ARIADNE devuelven las descripciones con <p>, <br>, &eacute; y
    demas. Sin esto, el CSV sale ilegible en Excel.
    """
    if not texto:
        return ""
    crudo = str(texto)
    crudo = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", crudo,
                   flags=re.S | re.I)
    crudo = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h[1-6]>", " ", crudo, flags=re.I)
    crudo = re.sub(r"<[^>]+>", " ", crudo)
    crudo = html.unescape(crudo)
    return limpiar(crudo)


def doi_limpio(valor):
    """Deja solo el DOI, sin prefijos ni enlaces. Vacio si no es un DOI.

    Hace falta porque los repositorios mezclan cosas distintas en el mismo
    campo: Dataverse manda 'doi:10.7910/DVN/X' y ARIADNE manda un enlace
    interno que no es un DOI.
    """
    texto = limpiar(valor)
    if not texto:
        return ""
    texto = re.sub(r"^https?://(dx\.)?doi\.org/", "", texto, flags=re.I)
    texto = re.sub(r"^doi:\s*", "", texto, flags=re.I)
    return texto if re.match(r"^10\.\d{4,9}/\S+$", texto) else ""


def texto_plano(valor):
    """Convierte lo que venga (texto, lista o diccionario) en un solo texto.

    Hace falta porque cada repositorio devuelve lo mismo de forma distinta:
    ARIADNE manda el titulo como {"text": "...", "language": "en"} y el pais
    como [{"name": "Chile"}]; Zenodo manda los autores como lista de
    diccionarios.
    """
    if valor is None:
        return ""
    if isinstance(valor, str):
        return limpiar(valor)
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, list):
        partes = [texto_plano(v) for v in valor]
        return "; ".join(p for p in partes if p)
    if isinstance(valor, dict):
        for clave in ("text", "name", "prefLabel", "title", "label", "value", "@id"):
            if clave in valor:
                return texto_plano(valor[clave])
        return "; ".join(f"{k}: {texto_plano(v)}"
                         for k, v in valor.items() if texto_plano(v))
    return limpiar(str(valor))


def sin_acentos(texto):
    """Quita tildes y dieresis, para comparar 'arqueologia' con 'arqueología'."""
    descompuesto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def sacar_anio(valor):
    """Extrae un anio de cuatro cifras de una fecha o de un texto."""
    if valor is None:
        return ""
    if isinstance(valor, (int, float)):
        numero = int(valor)
        return numero if 1000 <= numero <= 2200 else ""
    coincidencia = re.search(r"(1[0-9]{3}|20[0-9]{2}|21[0-9]{2})", str(valor))
    return int(coincidencia.group(1)) if coincidencia else ""


def normalizar_doi(doi):
    """Deja el DOI en minusculas y sin el prefijo de enlace, para comparar."""
    if not doi:
        return ""
    texto = str(doi).strip().lower()
    texto = re.sub(r"^https?://(dx\.)?doi\.org/", "", texto)
    texto = re.sub(r"^doi:\s*", "", texto)
    return texto.strip()


def acortar(texto, limite=500):
    texto = limpiar(texto)
    return texto if len(texto) <= limite else texto[:limite].rsplit(" ", 1)[0] + "..."


# ============================================================
# 2. TRADUCCION
#     Los catalogos de arqueologia son casi todos en ingles y las
#     busquedas en espanol devuelven poco o nada. Este glosario cubre los
#     terminos que de verdad se usan en una tesis de arqueologia andina.
# ============================================================

GLOSARIO = {
    # disciplina y oficio
    "arqueologia": "archaeology", "arqueologico": "archaeological",
    "arqueologica": "archaeological", "arqueologo": "archaeologist",
    "arqueologos": "archaeologists", "arqueometria": "archaeometry",
    "prehispanico": "prehispanic", "prehispanica": "prehispanic",
    "prehispanicos": "prehispanic", "antiguo": "ancient", "antigua": "ancient",
    "investigacion": "research", "tesis": "thesis", "datos": "data",
    # materiales y cultura material
    "ceramica": "ceramic", "ceramico": "ceramic", "ceramicas": "ceramics",
    "alfareria": "pottery", "lito": "lithic", "litico": "lithic",
    "liticos": "lithics", "textil": "textile", "textiles": "textiles",
    "tejido": "textile", "metalurgia": "metallurgy", "orfebreria": "goldsmithing",
    "artefacto": "artifact", "artefactos": "artifacts", "industria": "industry",
    "hueso": "bone", "huesos": "bones", "fauna": "fauna", "malacologia": "malacology",
    # sitios y estructuras
    "sitio": "site", "sitios": "sites", "yacimiento": "site",
    "asentamiento": "settlement", "poblado": "village", "vivienda": "dwelling",
    "arquitectura": "architecture", "construccion": "construction",
    "monumento": "monument", "recinto": "enclosure", "plataforma": "platform",
    "tumba": "tomb", "tumbas": "tombs", "entierro": "burial", "entierros": "burials",
    "cementerio": "cemetery", "contexto": "context", "estratigrafia": "stratigraphy",
    # practica arqueologica
    "excavacion": "excavation", "excavaciones": "excavations",
    "prospeccion": "survey", "sondeo": "test pit", "registro": "record",
    "cronologia": "chronology", "datacion": "dating", "fechado": "dating",
    "periodo": "period", "epoca": "period", "horizonte": "horizon",
    "formativo": "formative", "intermedio": "intermediate", "colonial": "colonial",
    # arte y simbolo
    "petroglifo": "petroglyph", "petroglifos": "petroglyphs",
    "geoglifo": "geoglyph", "geoglifos": "geoglyphs",
    "rupestre": "rock art", "iconografia": "iconography", "pintura": "painting",
    "quipu": "khipu", "quipus": "khipu", "ceremonial": "ceremonial",
    # geografia andina
    "valle": "valley", "costa": "coast", "sierra": "highlands",
    "cuenca": "basin", "cerro": "hill", "montana": "mountain",
    "rio": "river", "desierto": "desert", "puna": "puna", "selva": "jungle",
    "andes": "andes", "andino": "andean", "andina": "andean",
    "norte": "north", "sur": "south", "central": "central",
    # ambiente
    "paleoambiente": "paleoenvironment", "clima": "climate",
    "sedimento": "sediment", "vegetacion": "vegetation",
    "agricultura": "agriculture", "alimentacion": "diet",
    # patrimonio
    "patrimonio": "heritage", "museo": "museum", "coleccion": "collection",
    "conservacion": "conservation", "restauracion": "restoration",
    # culturas y lugares
    "inca": "inca", "incas": "inca", "nasca": "nasca", "nazca": "nazca",
    "moche": "moche", "mochica": "moche", "wari": "wari", "huari": "wari",
    "tiahuanaco": "tiwanaku", "tiwanaku": "tiwanaku", "chavin": "chavin",
    "paracas": "paracas", "chimu": "chimu", "cuzco": "cusco", "cusco": "cusco",
    "puno": "puno", "ayacucho": "ayacucho", "trujillo": "trujillo",
}

# Palabras que no aportan nada a la busqueda.
VACIAS = {"de", "del", "la", "el", "los", "las", "un", "una", "unos", "unas",
          "en", "y", "o", "u", "para", "por", "con", "sin", "sobre", "entre",
          "the", "of", "and", "or", "in", "on", "at", "to", "for", "with",
          "a", "an", "from", "by", "data", "datos"}


def traducir(consulta):
    """Traduce al ingles los terminos que conoce y deja el resto igual."""
    partes = []
    for palabra in consulta.split():
        nucleo = palabra.strip(".,;:()\"'")
        clave = sin_acentos(nucleo.lower())
        traduccion = GLOSARIO.get(clave)
        # Si no esta en el glosario, o se traduce a si misma (nombres propios
        # como Nasca, Moche o Inca), se deja como la escribio el usuario.
        partes.append(traduccion if traduccion and traduccion != clave else palabra)
    return " ".join(partes)


def terminos_utiles(consulta):
    """Palabras que si discriminan, sin vacias ni cortas."""
    terminos = []
    for palabra in sin_acentos(consulta.lower()).split():
        limpia = palabra.strip(".,;:()\"'")
        if len(limpia) >= 3 and limpia not in VACIAS:
            terminos.append(limpia)
    return terminos


def coincide(termino, texto):
    """Compara por la raiz de la palabra, para que 'archaeology' encuentre
    'archaeological' y 'ceramica' encuentre 'ceramicas'."""
    raiz = termino[:6] if len(termino) > 6 else termino
    return raiz in texto


def pasa_filtro(registro, conjuntos):
    """Exige que aparezcan TODAS las palabras de alguna de las busquedas.

    Dataverse y OSF no saben hacer esto: buscan con OR. Sin este filtro,
    'arqueologia Peru' devuelve encuestas de papa porque solo coinciden en
    'Peru'. Devuelve True si no hay terminos con los que filtrar.
    """
    utilizables = [c for c in conjuntos if c]
    if not utilizables:
        return True
    texto = sin_acentos(" ".join([
        registro["titulo"], registro["materias"], registro["descripcion"],
        registro["autores"], registro["tipo"], registro["pais"],
    ]).lower())
    return any(all(coincide(t, texto) for t in conjunto) for conjunto in utilizables)


# ============================================================
# 3. RED
# ============================================================

def pedir_json(url, reintentos=3, espera=ESPERA):
    """Pide una URL y devuelve el JSON. Reintenta si el servidor falla."""
    ultimo_error = None
    for intento in range(1, reintentos + 1):
        try:
            peticion = urllib.request.Request(url, headers=CABECERAS)
            with urllib.request.urlopen(peticion, timeout=espera,
                                        context=_CONTEXTO) as respuesta:
                return json.loads(respuesta.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as error:
            ultimo_error = f"HTTP {error.code}"
            if error.code == 429:          # demasiadas peticiones
                time.sleep(5 * intento)
                continue
            if 400 <= error.code < 500:    # error del que no se sale reintentando
                break
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            ultimo_error = type(error).__name__
        except json.JSONDecodeError:
            ultimo_error = "respuesta no valida"
        if intento < reintentos:
            time.sleep(2 * intento)
    raise RuntimeError(f"No se pudo consultar ({ultimo_error}): {url}")


# ============================================================
# 4. ADAPTADORES POR REPOSITORIO
#     Todos devuelven diccionarios con las mismas claves.
#     'preciso' dice si el repositorio ya exige que aparezcan todas las
#     palabras. Si es False, hay que filtrar despues.
# ============================================================

def _registro(repositorio, titulo, autores, fecha, tipo, idioma, pais,
              doi, url, materias, descripcion):
    return {
        "repositorio": repositorio,
        "titulo": limpiar_html(texto_plano(titulo)),
        "autores": limpiar_html(texto_plano(autores)),
        "anio": sacar_anio(texto_plano(fecha)),
        "fecha": texto_plano(fecha),
        "tipo": limpiar_html(texto_plano(tipo)),
        "idioma": texto_plano(idioma),
        "pais": texto_plano(pais),
        "doi": doi_limpio(doi),
        "url": limpiar(url),
        "materias": limpiar_html(texto_plano(materias)),
        "descripcion": acortar(limpiar_html(texto_plano(descripcion)), 600),
    }


def buscar_zenodo(consulta, maximo, recientes, pausa, aviso, filtro):
    """Zenodo. Exige todas las palabras: el filtro no quita nada."""
    base = "https://zenodo.org/api/records"
    terminos = [t for t in consulta.split() if t]
    consulta_api = " AND ".join(terminos) if len(terminos) > 1 else consulta

    registros = []
    pagina = 1
    primera = True
    while len(registros) < maximo:
        parametros = {"q": consulta_api,
                      "size": min(TAMANO_PAGINA, maximo - len(registros)),
                      "page": pagina}
        if recientes:
            parametros["sort"] = "mostrecent"
        datos = pedir_json(base + "?" + urllib.parse.urlencode(parametros))

        if primera:
            aviso(f"    '{consulta_api}': {datos.get('hits', {}).get('total', 0)} coincidencias")
            primera = False

        golpes = datos.get("hits", {}).get("hits", [])
        if not golpes:
            break
        for golpe in golpes:
            meta = golpe.get("metadata", {})
            tipo = meta.get("resource_type") or {}
            registro = _registro(
                "Zenodo", meta.get("title"),
                [c.get("name") for c in meta.get("creators", [])],
                meta.get("publication_date"),
                tipo.get("title") if isinstance(tipo, dict) else tipo,
                "", "",
                golpe.get("doi") or meta.get("doi"),
                golpe.get("links", {}).get("self_html") or golpe.get("doi_url"),
                meta.get("keywords"), meta.get("description"))
            if filtro(registro):
                registros.append(registro)
        pagina += 1
        time.sleep(pausa)
    return registros


def buscar_dataverse(consulta, maximo, recientes, pausa, aviso, filtro):
    """Harvard Dataverse. Busca con OR: hay que filtrar mientras se recorre."""
    base = "https://dataverse.harvard.edu/api/search"
    registros = []
    inicio = 0
    primera = True
    revisados = 0
    descartados = 0
    # Hay que mirar bastantes mas de los que se quieren, porque la mayoria
    # se descarta: Dataverse busca con OR y devuelve mucho que no sirve.
    tope = max(maximo * FACTOR_EXPLORACION, 500)
    while len(registros) < maximo and revisados < tope:
        parametros = {"q": consulta, "type": "dataset",
                      "per_page": 100, "start": inicio}
        if recientes:
            parametros["sort"] = "date"
            parametros["order"] = "desc"
        datos = pedir_json(base + "?" + urllib.parse.urlencode(parametros))

        if primera:
            aviso(f"    '{consulta}': {datos.get('data', {}).get('total_count', 0)} "
                  f"declarados (busca con OR; se revisan y se descartan)")
            primera = False

        items = datos.get("data", {}).get("items", [])
        if not items:
            break
        for item in items:
            registro = _registro(
                "Harvard Dataverse", item.get("name"), item.get("authors"),
                item.get("published_at"), item.get("type"), "", "",
                item.get("global_id"), item.get("url"),
                item.get("subjects") or item.get("keywords"),
                item.get("description") or item.get("citation"))
            if filtro(registro):
                registros.append(registro)
            else:
                descartados += 1
        revisados += len(items)
        inicio += len(items)
        time.sleep(pausa)
    aviso(f"    {len(registros)} utiles de {revisados} revisados "
          f"({descartados} descartados)")
    return registros


def buscar_ariadne(consulta, maximo, recientes, pausa, aviso, filtro):
    """ARIADNE. Exige todas las palabras y en ingles: el filtro no quita nada."""
    base = "https://portal.ariadne-infrastructure.eu/api/search"
    registros = []
    pagina = 1
    primera = True
    while len(registros) < maximo:
        parametros = {"q": consulta,
                      "size": min(TAMANO_PAGINA, maximo - len(registros)),
                      "page": pagina}
        datos = pedir_json(base + "?" + urllib.parse.urlencode(parametros))

        if primera:
            bruto = datos.get("total", 0)
            total = bruto.get("value") if isinstance(bruto, dict) else bruto
            aviso(f"    '{consulta}': {total} coincidencias")
            primera = False

        golpes = datos.get("hits", [])
        if not golpes:
            break
        for golpe in golpes:
            d = golpe.get("data", {})
            materias = [s.get("prefLabel") for s in d.get("ariadneSubject", [])
                        if isinstance(s, dict)] if isinstance(d.get("ariadneSubject"), list) else []
            materias.append(texto_plano(d.get("nativeSubject")))
            registro = _registro(
                "ARIADNE", d.get("title"),
                [c.get("name") for c in d.get("creator", [])]
                if isinstance(d.get("creator"), list) else d.get("creator"),
                d.get("issued") or d.get("wasCreated") or d.get("modified"),
                d.get("resourceType") or d.get("has_type"),
                d.get("language"), d.get("country"),
                d.get("landingPage") or d.get("identifier"),
                d.get("landingPage") or d.get("identifier"),
                materias,
                d.get("description"))
            if filtro(registro):
                registros.append(registro)
        pagina += 1
        time.sleep(pausa)
    return registros


def buscar_osf(consulta, maximo, recientes, pausa, aviso, filtro):
    """OSF. Solo busca en titulos y no cruza palabras: hay que filtrar.

    Por eso se busca con el termino mas largo, que es el mas discriminante,
    y despues se revisa uno por uno.
    """
    base = "https://api.osf.io/v2/nodes/"
    utiles = terminos_utiles(consulta)
    termino = max(utiles, key=len) if utiles else consulta.split()[0]

    registros = []
    pagina = 1
    revisados = 0
    descartados = 0
    tope = max(maximo * FACTOR_EXPLORACION, 500)
    while len(registros) < maximo and revisados < tope:
        parametros = [("filter[title]", termino), ("page[size]", 100),
                      ("page[number]", pagina)]
        if recientes:
            parametros.append(("sort", "-date_created"))
        datos = pedir_json(base + "?" + urllib.parse.urlencode(parametros))

        items = datos.get("data", [])
        if not items:
            break
        for item in items:
            atributos = item.get("attributes", {})
            registro = _registro(
                "OSF", atributos.get("title"), atributos.get("contributors"),
                atributos.get("date_created"), atributos.get("category"), "", "",
                "", (item.get("links") or {}).get("html"),
                atributos.get("tags") or atributos.get("subjects"),
                atributos.get("description"))
            if filtro(registro):
                registros.append(registro)
            else:
                descartados += 1
        revisados += len(items)
        pagina += 1
        time.sleep(pausa)
    aviso(f"    OSF solo busca en titulos; se uso el termino '{termino}': "
          f"{len(registros)} utiles de {revisados} revisados "
          f"({descartados} descartados)")
    return registros


# nombre visible, funcion, y si el repositorio ya exige todas las palabras
REPOSITORIOS = {
    "zenodo": ("Zenodo", buscar_zenodo, True),
    "dataverse": ("Harvard Dataverse", buscar_dataverse, False),
    "ariadne": ("ARIADNE", buscar_ariadne, True),
    "osf": ("OSF", buscar_osf, False),
}


# ============================================================
# 5. RECOLECCION, FILTRADO Y SALIDA
# ============================================================

def recolectar(consulta, nombres, maximo, recientes, pausa, solo_espanol, sin_filtro, callado):
    def aviso(texto):
        if not callado:
            imprimir(texto)

    traduccion = traducir(consulta)
    hay_traduccion = sin_acentos(traduccion.lower()) != sin_acentos(consulta.lower())
    consultas = [consulta]
    if hay_traduccion and not solo_espanol:
        consultas.append(traduccion)

    if hay_traduccion and not solo_espanol and not callado:
        imprimir(f"\n  Busqueda en espanol: {consulta}")
        imprimir(f"  Traduccion aplicada:  {traduccion}")
        imprimir("  Se consultan las dos versiones y se quitan los repetidos."
                 "  (--solo-espanol para evitarlo)")

    conjuntos = [terminos_utiles(c) for c in consultas]

    todos = []
    fallos = []
    for clave in nombres:
        if clave not in REPOSITORIOS:
            fallos.append((clave, "repositorio desconocido"))
            continue
        nombre, funcion, preciso = REPOSITORIOS[clave]
        aviso(f"\n  {nombre}")
        # Los repositorios que ya exigen todas las palabras no necesitan
        # filtro; los que buscan con OR si.
        filtro = (lambda r: True) if (preciso or sin_filtro) \
            else (lambda r: pasa_filtro(r, conjuntos))
        for version in consultas:
            try:
                encontrados = funcion(version, maximo, recientes, pausa, aviso, filtro)
            except Exception as error:      # se sigue con los demas
                aviso(f"    No se pudo consultar con '{version}': {acortar(error, 70)}")
                fallos.append((f"{nombre} ({version})", str(error)))
                continue
            todos.extend(encontrados)

    return todos, fallos


def quitar_duplicados(registros):
    """Quita repetidos por DOI y, si no hay DOI, por titulo normalizado."""
    vistos = set()
    unicos = []
    repetidos = 0
    for r in registros:
        doi = normalizar_doi(r["doi"])
        if doi:
            clave = "doi:" + doi
        else:
            titulo = re.sub(r"[^a-z0-9]+", "",
                            sin_acentos(r["titulo"].lower()))
            clave = "tit:" + titulo if titulo else ""
        if clave and clave in vistos:
            repetidos += 1
            continue
        if clave:
            vistos.add(clave)
        unicos.append(r)
    return unicos, repetidos


def escribir_csv(registros, ruta):
    columnas = ["repositorio", "titulo", "autores", "anio", "fecha", "tipo",
                "idioma", "pais", "doi", "url", "materias", "descripcion"]
    # utf-8-sig: asi Excel abre el archivo con los acentos correctos.
    with open(ruta, "w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        for r in registros:
            escritor.writerow({c: r.get(c, "") for c in columnas})


def escribir_json(registros, ruta):
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(registros, archivo, ensure_ascii=False, indent=2)


def resumen(registros, fallos, callado):
    if callado:
        return
    imprimir()
    imprimir("=" * 70)
    imprimir(f"  RESULTADO: {len(registros)} registros unicos")
    imprimir("=" * 70)

    por_repositorio, por_anio, por_tipo = {}, {}, {}
    con_doi = con_anio = 0
    for r in registros:
        por_repositorio[r["repositorio"]] = por_repositorio.get(r["repositorio"], 0) + 1
        if r["anio"]:
            por_anio[r["anio"]] = por_anio.get(r["anio"], 0) + 1
            con_anio += 1
        if r["tipo"]:
            por_tipo[r["tipo"]] = por_tipo.get(r["tipo"], 0) + 1
        if r["doi"]:
            con_doi += 1

    imprimir("\n  Por repositorio:")
    for nombre, cuantos in sorted(por_repositorio.items(), key=lambda x: -x[1]):
        imprimir(f"    {cuantos:>6}  {nombre}")

    if por_anio:
        imprimir("\n  Por anio (los doce mas frecuentes):")
        for anio, cuantos in sorted(por_anio.items(), key=lambda x: (-x[1], x[0]))[:12]:
            imprimir(f"    {cuantos:>6}  {anio}")
        rango = f"{min(por_anio)} a {max(por_anio)}"
        imprimir(f"    {con_anio} registros con fecha; rango {rango}")

    if por_tipo:
        imprimir("\n  Por tipo de recurso (los diez mas frecuentes):")
        for tipo, cuantos in sorted(por_tipo.items(), key=lambda x: -x[1])[:10]:
            imprimir(f"    {cuantos:>6}  {acortar(tipo, 58)}")

    imprimir(f"\n  Con DOI (citables): {con_doi} de {len(registros)}")

    if fallos:
        imprimir("\n  Consultas que fallaron:")
        for nombre, motivo in fallos:
            imprimir(f"    - {nombre}: {acortar(motivo, 80)}")


def nombre_por_defecto(consulta):
    limpio = sin_acentos(consulta.lower())
    limpio = re.sub(r"[^a-z0-9]+", "_", limpio).strip("_")
    return f"arqueologia_{limpio[:50]}_{datetime.now():%Y%m%d}.csv"


# ============================================================
# 6. MODO INTERACTIVO Y LINEA DE COMANDOS
# ============================================================

def preguntar(texto, defecto=None):
    sufijo = f" [{defecto}]" if defecto is not None else ""
    try:
        respuesta = input(f"  {texto}{sufijo}: ").strip()
    except (EOFError, KeyboardInterrupt):
        imprimir()
        return defecto if defecto is not None else ""
    return respuesta if respuesta else (defecto if defecto is not None else "")


def si_no(texto, defecto="n"):
    respuesta = preguntar(texto + " (s/n)", defecto).strip().lower()
    return respuesta in ("s", "si", "sí", "y", "1")


def modo_interactivo():
    imprimir()
    imprimir("=" * 70)
    imprimir("   SCRAPER DE REPOSITORIOS DE DATOS ARQUEOLOGICOS")
    imprimir(f"   Version {VERSION}  -  no necesita instalar nada")
    imprimir("=" * 70)
    imprimir("\n  Repositorios: " + ", ".join(REPOSITORIOS))
    imprimir("  Escribe la busqueda como en Google: ceramica Nasca")
    imprimir("  El programa la busca en espanol y la traduce al ingles solo.\n")

    consulta = preguntar("Que quieres buscar")
    if not consulta:
        imprimir("  No escribiste nada que buscar.")
        return 1

    try:
        maximo = max(1, int(preguntar("Maximo de registros por repositorio", "50")))
    except ValueError:
        maximo = 50

    repos = preguntar("Repositorios (separados por coma, o 'todos')", "todos")
    nombres = list(REPOSITORIOS) if repos.strip().lower() in ("todos", "all", "") \
        else [r.strip().lower() for r in repos.split(",") if r.strip()]

    def a_entero(valor):
        try:
            return int(valor)
        except (TypeError, ValueError):
            return None

    desde = a_entero(preguntar("Anio desde (vacio = sin limite)", ""))
    hasta = a_entero(preguntar("Anio hasta (vacio = sin limite)", ""))
    solo_espanol = si_no("Buscar solo en espanol (sin traducir)", "n")
    sin_filtro = si_no("Desactivar el filtro de relevancia", "n")
    recientes = si_no("Ordenar por mas recientes en vez de por relevancia", "n")
    salida = preguntar("Archivo de salida", nombre_por_defecto(consulta))

    return ejecutar(consulta, nombres, maximo, desde, hasta, recientes, 1.0,
                    salida, False, False, solo_espanol, sin_filtro)


def ejecutar(consulta, nombres, maximo, desde, hasta, recientes, pausa,
             salida, guardar_json, callado, solo_espanol, sin_filtro):
    inicio = time.time()
    registros, fallos = recolectar(consulta, nombres, maximo, recientes, pausa,
                                   solo_espanol, sin_filtro, callado)

    if desde or hasta:
        antes = len(registros)
        filtrados = []
        for r in registros:
            if not r["anio"]:               # sin fecha: no se descarta por anio
                filtrados.append(r)
                continue
            if desde and r["anio"] < desde:
                continue
            if hasta and r["anio"] > hasta:
                continue
            filtrados.append(r)
        if not callado:
            imprimir(f"\n  Filtro de anios ({desde or 'sin limite'} a "
                     f"{hasta or 'sin limite'}): quedan {len(filtrados)} de {antes}")
        registros = filtrados

    if not registros:
        if not callado:
            imprimir("\n  No se encontro nada.")
            imprimir("  Prueba con menos palabras, en singular, o con el")
            imprimir("  termino en ingles entre comillas: \"archaeology Peru\".")
        return 1

    registros, repetidos = quitar_duplicados(registros)
    if repetidos and not callado:
        imprimir(f"\n  Se quitaron {repetidos} registros repetidos entre repositorios")

    escribir_csv(registros, salida)
    if guardar_json:
        escribir_json(registros, Path(salida).with_suffix(".json"))

    resumen(registros, fallos, callado)

    if not callado:
        imprimir()
        imprimir(f"  Tabla guardada en: {Path(salida).resolve()}")
        if guardar_json:
            imprimir(f"  JSON crudo en:     {Path(salida).with_suffix('.json').resolve()}")
        imprimir(f"  Tardo {time.time() - inicio:.0f} segundos.")
        imprimir()
        imprimir("  Cita cada repositorio que uses, no solo el DOI del registro.")
        imprimir("  Las condiciones de uso son de cada repositorio.")
    return 0


def construir_parser():
    p = argparse.ArgumentParser(
        prog="scraper_arqueologia.py",
        description="Busca metadatos en repositorios de datos arqueologicos "
                    "y los guarda en una tabla CSV.",
        epilog="Sin argumentos entra en modo interactivo.\n"
               "Ejemplo: python scraper_arqueologia.py \"arqueologia Peru\" --maximo 100",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("consulta", nargs="*", help="palabras a buscar")
    p.add_argument("-n", "--maximo", type=int, default=50,
                   help="maximo de registros por repositorio y por idioma "
                        "(por defecto 50)")
    p.add_argument("-r", "--repos", default="zenodo,dataverse,ariadne,osf",
                   help="repositorios separados por coma (por defecto todos)")
    p.add_argument("-o", "--salida", default=None, help="archivo CSV de salida")
    p.add_argument("--desde", type=int, default=None, help="anio minimo")
    p.add_argument("--hasta", type=int, default=None, help="anio maximo")
    p.add_argument("--pausa", type=float, default=1.0,
                   help="segundos entre peticiones (por defecto 1)")
    p.add_argument("--recientes", action="store_true",
                   help="ordenar por fecha en vez de por relevancia")
    p.add_argument("--solo-espanol", action="store_true",
                   help="no traducir la busqueda al ingles")
    p.add_argument("--sin-filtro", action="store_true",
                   help="no descartar los registros que no cumplen la busqueda")
    p.add_argument("--json", action="store_true", dest="guardar_json",
                   help="guardar tambien el JSON crudo")
    p.add_argument("--callado", action="store_true",
                   help="no mostrar el progreso, solo el resumen")
    p.add_argument("-v", "--version", action="version",
                   version=f"scraper_arqueologia.py {VERSION}")
    p.add_argument("--ayuda", action="help",
                   help="mostrar esta ayuda y salir (igual que -h)")
    return p


def main():
    argumentos = sys.argv[1:]
    if not argumentos:
        return modo_interactivo()

    opciones = construir_parser().parse_args(argumentos)
    consulta = " ".join(opciones.consulta).strip()
    if not consulta:
        construir_parser().print_help()
        return 1

    nombres = [r.strip().lower() for r in opciones.repos.split(",") if r.strip()]
    desconocidos = [n for n in nombres if n not in REPOSITORIOS]
    if desconocidos:
        imprimir(f"Repositorio(s) desconocido(s): {', '.join(desconocidos)}")
        imprimir(f"Disponibles: {', '.join(REPOSITORIOS)}")
        return 1

    return ejecutar(consulta, nombres, max(1, opciones.maximo), opciones.desde,
                    opciones.hasta, opciones.recientes, opciones.pausa,
                    opciones.salida or nombre_por_defecto(consulta),
                    opciones.guardar_json, opciones.callado,
                    opciones.solo_espanol, opciones.sin_filtro)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        imprimir("\n  Interrumpido por el usuario.")
        sys.exit(0)
