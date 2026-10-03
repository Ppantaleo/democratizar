# Jerarquía de circuitos electorales — metodología y fuentes

## Objetivo

Construir una jerarquía territorial (nación > provincia > sección > circuito)
con nombres oficiales, para asignar conversaciones de Pol.is a cada nivel de
la plataforma de relevamiento de agenda electoral.

## Fuentes de datos utilizadas

### 1. Padrón Electoral 2017 (CNE) — fuente principal de nombres

- **URL de origen:** https://www.electoral.gob.ar/nuevo/paginas/datos/padrondatos.php
- **Descarga directa:** https://www.electoral.gob.ar/nuevo/paginas/datos/padron_2017.zip
- **Archivo:** `Padron_2017.xlsx` (~6 MB, 1 hoja)
- **Fecha del dato:** 2017 (última versión pública descargable a la fecha de esta investigación)
- **Nivel de detalle original:** mesa de votación (el más granular)
- **Columnas del archivo original:** `distrito`, `nombre_distrito`, `secc`,
  `seccion`, `circu`, `circuito`, `codigo`, `local`, `direccion`, `mesa`,
  `electores`, `Fem`, `Masc`
- **Columnas utilizadas:** `distrito`, `nombre_distrito`, `secc`, `seccion`,
  `circu`, `circuito`, `electores`
- **Columnas descartadas:** `codigo`, `local`, `direccion`, `mesa`, `Fem`,
  `Masc` — nivel escuela/mesa y desagregado por género, fuera de alcance
  del proyecto (el relevamiento se hace desde circuito/localidad hacia
  arriba, no por mesa ni por establecimiento)

### 2. GeoServer / WFS de la CNE — geometría de circuitos (uso posterior, no en este CSV)

- **Endpoint:** `https://mapa2.electoral.gov.ar/geoserver/wfs`
- **Capas relevantes identificadas:**
  - `descargas:secciones_electorales` (538 features, nivel departamento)
  - `descargas:circuito_XX` — una capa por distrito, donde `XX` es el
    código numérico de dos dígitos del distrito (ej. `circuito_01` = CABA,
    `circuito_02` = Buenos Aires, `circuito_04` = Córdoba, etc.). Listado
    completo de las 24 capas obtenido vía `GetCapabilities`.
- **Acceso:** requiere el parámetro `authkey` en la URL (la clave que usa el
  visor público de mapas de la CNE; en los comandos de abajo figura como
  `${CNE_AUTHKEY}`). El servidor está
  detrás de un WAF que **rechaza requests sin User-Agent de navegador**
  (`curl` sin `-A "Mozilla/5.0 ..."` devuelve "Request Rejected", no un
  error de GeoServer).
- **Formato recomendado de descarga:** GeoJSON (`outputFormat=application/json`),
  preferido sobre Shapefile o KML por ser nativo de la web y no requerir
  múltiples archivos asociados.
- **Limitación detectada:** el campo `circuito` de esta capa viene **vacío
  (null) en el 100% de los registros** en todos los distritos verificados;
  la capa solo trae geometría + `departamen` + `cabecera` + códigos INDEC.
  Se confirmó igualmente que la geometría SÍ está al nivel de circuito real
  (ej. el departamento Capital de Córdoba tiene 120 polígonos distintos,
  coincidente con su cantidad real de circuitos), pero sin el nombre/número
  oficial poblado. El nombre real se toma del padrón (fuente 1) o de las
  Resoluciones de la CNE (fuente 3).
- **Uso previsto:** cruce geométrico circuito ↔ domicilio del usuario
  (point-in-polygon) para asignar automáticamente a qué circuito pertenece
  cada participante de la plataforma, usando el `gid` de cada feature como
  identificador interno mientras no se complete el cruce con el nombre
  oficial.

### 3. Resoluciones de la Unidad de Geografía Electoral (CNE) — fuente normativa

- **Organismo:** Unidad de Geografía Electoral, dentro de la Cámara
  Nacional Electoral (CNE).
- **Marco normativo:** Acordadas N° 18/2011 y 49/2020 CNE.
- **Publicación:** Boletín Oficial de la República Argentina
  (boletinoficial.gob.ar) y argentina.gob.ar/normativa — una Resolución
  por cada modificación, subdivisión o creación de circuitos en una
  sección electoral puntual.
- **Estructura de cada Resolución:**
  - Anexo I: delimitación cartográfica (mapa) del/los circuito(s)
  - Anexo II: texto descriptivo de la delimitación, calle por calle, con
    el nombre y número oficial del circuito (ej. "Circuito 18A 'San
    José'", "Circuito 19 'Rafael Calzada'")
- **Uso previsto:** fuente de verdad para (a) circuitos creados o
  modificados después de 2017, no reflejados en el padrón de esa fecha, y
  (b) completar el nombre oficial de los 1.003 circuitos que el padrón
  2017 dejó sin nombre (ver sección de limpieza, punto 4), concentrados en
  CABA y Buenos Aires.
- **Limitación:** no existe un dataset único descargable con todas las
  Resoluciones consolidadas; hay que localizar y procesar cada Resolución
  individualmente por sección electoral.

### 4. Resultados provisorios elecciones generales 2023 (DINE) — fuente complementaria

- **Organismo:** Dirección Nacional Electoral (DINE), Ministerio del Interior.
- **Página:** https://www.argentina.gob.ar/dine/resultados-electorales/elecciones-2023
- **Descarga directa:** https://www.argentina.gob.ar/sites/default/files/2023_generales_1.zip
  (28 MB comprimido; ~1 GB descomprimido; fecha del archivo: 16/11/2023)
- **Archivo local:** `data/raw/resultados_generales_2023.zip` (se lee sin descomprimir)
- **Formato:** estándar de preservación de resultados electorales de la DINE,
  una fila por mesa × cargo × agrupación.
- **Columnas utilizadas:** `distrito_id`, `seccion_id`, `seccion_nombre`,
  `circuito_id`, `mesa_id`, `mesa_tipo`, `mesa_electores`.
- **Qué aporta:** electores 2023 por circuito, nombre de sección más completo
  (ej. "Presidente Roque Sáenz Peña") y detección de circuitos nuevos o
  desaparecidos desde 2017.
- **Qué NO aporta:** nombres de circuito. El campo `circuito_nombre` repite el
  código en el 100% de los circuitos.
- **Procesamiento** (`scripts/extraer_circuitos_2023.py` →
  `data/processed/circuitos_2023.csv`):
  - Solo mesas `NATIVOS` (las de `EXTRANJEROS` no votan en elecciones nacionales).
  - En CABA el mismo circuito figura como `00001` y como `1` según la fila;
    se deduplica sobre el código normalizado (sin ceros iniciales, en
    mayúsculas), para no contar dos veces las mesas.
  - Resultado: 5.752 circuitos, 35.410.080 electores (coherente con el padrón
    oficial 2023, ~35,39 millones).

### Otras fuentes evaluadas (24/09/2026)

- **CNE, página de datos del padrón:** solo ofrece el archivo 2017. El padrón
  2025 es solo de consulta individual.
- **DINE, resultados 2025:** la página de resultados llega hasta 2023; no se
  encontró descarga de 2025.
- **Pendiente:** pedido de acceso a la información pública (Ley 27.275) a la
  CNE por la tabla vigente de circuitos con código y nombre.

## Procedimiento de limpieza aplicado

Implementado en `scripts/generar_jerarquia.py`.

1. **Exclusión del distrito 30** ("_Argentinos en el Exterior"): no es
   territorio nacional, no aplica a una jerarquía geográfica de circuitos
   territoriales. Confirmado por consulta directa al dataset.

2. **Corrección de encoding (mixto latin-1 / CP850)**: el padrón mezcla
   nombres correctos con nombres exportados en **CP850** (página de códigos
   DOS de Europa occidental). Ejemplos: "Pi¤eyro" (Piñeyro), "CA¥UELAS"
   (CAÑUELAS), "Santa Mar¡a" (Santa María), "El Jag\x81el" (El Jagüel),
   "1ø DE MAYO" (1° DE MAYO); a la vez, "Córdoba", "PEÑA", "GÜEMES" o
   "N°1" ya vienen bien escritos.

   *Primera versión (errónea, corregida el 24/09/2026):* se aplicó
   `encode('latin-1').decode('cp437')` a todos los textos. Eso arregló los
   casos CP850 pero rompió los que estaban bien: "C≤rdoba" (641 filas,
   toda la provincia), "ICA╤O", "COMUNA N░1", "G▄EMES". Además, CP437 no
   es la página correcta: en el distrito 30 aparecen "EREVµN", "BERLÖN" y
   "CONCEPCIàN", que solo se resuelven con CP850 (Á, Í, Ó).

   *Corrección vigente:* se traducen **carácter por carácter** solo los
   bytes que nunca aparecen legítimamente en nombres en castellano
   (`0x81 0x90 ¡ ¤ ¥ µ ø` → `ü É í ñ Ñ Á °`, según CP850); el resto no se
   toca. El script avisa si queda algún carácter no ASCII fuera del
   conjunto esperado (`áéíóúÁÉÍÓÚñÑüÜ°`). Resultado: 0 caracteres
   residuales.

3. **Colapso mesa → circuito**: se agrupó por
   `distrito, nombre_distrito, secc, seccion, circu, circuito`
   (con `dropna=False`, para no perder silenciosamente circuitos con
   algún campo en null), sumando la columna `electores` para obtener el
   peso poblacional de cada circuito sin necesidad de retener el detalle
   de mesas.

4. **Circuitos sin nombre**: se detectaron **1.003 circuitos** (de 5.760
   totales) cuyo campo `circuito` es nulo en TODAS sus filas de mesa. Se
   verificó que **no hay inconsistencia** (0 circuitos con nombres
   contradictorios entre distintas mesas del mismo circuito) — el dato es
   limpio, solo incompleto. Distribución exclusiva en:
   - Distrito 1 (Capital Federal): 167 circuitos sin nombre
   - Distrito 2 (Buenos Aires): 836 circuitos sin nombre

   Son las dos jurisdicciones con más subdivisiones históricas de
   circuitos (ver ejemplos de Resoluciones de la fuente 3 para Almirante
   Brown y General San Martín, ambas en Buenos Aires), por lo que es
   plausible que el export de 2017 no haya capturado nombres para
   circuitos creados o subdivididos más recientemente en esos dos
   distritos puntuales.

   **Solución aplicada:** se usa `'Circuito ' + circu` (el código
   numérico/alfanumérico del circuito) como nombre provisorio donde falta
   el texto, y se agrega la columna booleana `nombre_verificado` para
   poder filtrar y priorizar estos 1.003 casos en un enriquecimiento
   posterior desde las Resoluciones de la CNE (fuente 3), específicas de
   CABA y Buenos Aires.

## Resultado final

- **Total de circuitos:** 5.760
- **Total de distritos:** 24 (23 provincias + CABA, excluido el exterior)
- **Circuitos con nombre verificado (del padrón):** 4.757
- **Circuitos con nombre provisorio (pendiente de enriquecer):** 1.003

5. **IDs jerárquicos**: clave estable por nodo del árbol, que se usa para
   asociar cada nodo con su conversación de Pol.is.

   | Nivel | Formato | Ejemplo (General Levalle) |
   |---|---|---|
   | Nacional | `AR` | `AR` |
   | Provincial | `AR-` + distrito (2 dígitos) | `AR-04` |
   | Departamental | + `-` + secc (3 dígitos) | `AR-04-017` |
   | Local | + `-` + circu (sin relleno) | `AR-04-017-252` |

   El código de circuito se conserva tal como lo publica la CNE (CABA usa
   `0001`, Córdoba `252` o `10A`, Tierra del Fuego `U1`), sin rellenar con
   ceros, para que sea trazable a la fuente. `circu` se lee como texto
   (`dtype=str`) para no perder ceros iniciales. Se verificó que
   `id_local` es único (el código de circuito no se repite dentro de un
   distrito).

6. **Cruce con 2023**: por `distrito` + código de circuito normalizado.

   | Resultado | Circuitos |
   |---|---|
   | Presentes en 2017 y 2023 | 4.900 |
   | Presentes en 2017, ausentes en 2023 | 134 |
   | Sin cruzar (distritos renumerados) | 726 |
   | Nuevos en 2023 (no están en 2017) | 138 |

   **Distritos renumerados:** Neuquén (15), Santa Fe (21) y Tierra del Fuego
   (24) cambiaron todo el esquema de códigos (ej. Santa Fe pasó de `402`,
   `404A` a `00010`, `00020`; Tierra del Fuego de `U1` a `00101`). Un primer
   cruce ingenuo dio 62 "cambios de sección" que eran coincidencias de código
   entre lugares distintos (Chabás, dpto. Caseros, contra un circuito de La
   Capital). Por eso esos tres distritos no se cruzan: `presente_2023` queda
   vacío y sus 714 circuitos 2023 van a `circuitos_solo_2023.csv` con motivo
   `distrito_renumerado`. Cruzarlos requiere una tabla de equivalencias o
   la geometría.

   Excluidos esos tres, **no hay ningún circuito que haya cambiado de
   sección**. Córdoba cruza completa (634 de 634).

## Salida

- **`data/processed/jerarquia_circuitos.csv`** (5.760 filas, base 2017).
  Columnas: `id_local, id_departamental, id_provincial, distrito,
  nombre_distrito, secc, seccion, circu, circuito, electores,
  nombre_verificado, presente_2023, circu_2023, seccion_2023,
  electores_2023, cambio_seccion_2023`. Las columnas `*_2023` quedan vacías
  cuando no hay cruce.
- **`data/processed/circuitos_2023.csv`**: circuitos 2023 colapsados
  (intermedio).
- **`data/processed/circuitos_solo_2023.csv`** (852 filas): circuitos 2023 sin
  par en 2017, con `motivo` = `nuevo` o `distrito_renumerado`. No tienen
  nombre.
- **Orden de ejecución:** `python3 scripts/extraer_circuitos_2023.py` y
  después `python3 scripts/generar_jerarquia.py`.

## Estructura de carpetas del proyecto

```
democratizar/
├── data/
│   ├── raw/
│   │   ├── Padron_2017.xlsx
│   │   ├── padron_2017.zip
│   │   └── resultados_generales_2023.zip
│   └── processed/
│       ├── circuitos_2023.csv
│       ├── circuitos_solo_2023.csv
│       └── jerarquia_circuitos.csv
├── scripts/
│   ├── extraer_circuitos_2023.py
│   └── generar_jerarquia.py
└── docs/
    └── METODOLOGIA_JERARQUIA_CIRCUITOS.md
```

## Decisiones de diseño (23/09/2026)

- **Dominio:** democratiz.ar, registrado.
- **Asignación del usuario a su circuito:** selección manual con selector
  en cascada (provincia → sección → circuito). No se usa geometría en el
  MVP; el GeoServer queda para una fase posterior.
- **Circuitos sin nombre:** se aceptan con nombre provisorio
  (`Circuito XXXX`); no afectan al piloto.
- **Piloto:** General Levalle, Córdoba.

  | Nivel | ID | Nombre | Electores 2017 |
  |---|---|---|---|
  | Provincial | `AR-04` | Córdoba | — |
  | Departamental | `AR-04-017` | Roque Sáenz Peña | — |
  | Local | `AR-04-017-252` | LEVALLE | 5.116 (2023: 5.236) |

  Pendiente: confirmar que el circuito 252 coincide con el ejido
  municipal de General Levalle (nivel en el que se eligen intendente y
  concejales).

## Limitaciones conocidas

- **Antigüedad del dato de nombres:** el padrón usado es de 2017; circuitos
  creados o subdivididos después de esa fecha no están reflejados y deben
  completarse desde las Resoluciones de la Unidad de Geografía Electoral
  (fuente 3).
- **Significado no uniforme de "sección":** el campo `seccion` no equivale
  a lo mismo en todas las provincias. En CABA equivale a **comuna** (15
  comunas); en Buenos Aires, la cantidad de secciones (135) coincide con
  la cantidad de **partidos** bonaerenses. No debe asumirse equivalencia
  semántica entre provincias sin verificar caso por caso.
- **1.003 circuitos con nombre provisorio:** ver punto 4 de la limpieza.
  No bloquea el uso de los niveles superiores de la jerarquía (nación,
  provincia, sección), que están 100% completos y verificados.
- **Sin geometría en este CSV:** este dataset es tabular (nombres +
  jerarquía + electores), no trae polígonos. Para la geometría, cruzar con
  la fuente 2 (GeoServer WFS) usando el código de circuito como clave de
  unión donde esa capa lo tenga poblado, o por proximidad/nombre en su
  defecto.
- **No incluye datos de padrón por DNI/persona:** la CNE no publica el
  padrón nominal geolocalizado de forma masiva; solo permite consulta
  individual por DNI en electoral.gob.ar / padron.gob.ar. Este proyecto no
  requiere ese nivel de dato — el objetivo es la jerarquía territorial con
  nombres oficiales, no la identificación de electores individuales.

- **Nombres de circuito poco descriptivos:** en Salta (sección Capital)
  varios circuitos tienen como nombre solo "C" en el padrón. Se dejan tal
  cual; no están marcados como no verificados porque el campo no es nulo.

## Comandos de referencia (reproducibilidad)

Descarga del padrón:
```bash
curl -A "Mozilla/5.0" -o padron_2017.zip \
  "https://www.electoral.gob.ar/nuevo/paginas/datos/padron_2017.zip"
unzip padron_2017.zip
```

Ejemplo de consulta al WFS de GeoServer (requiere User-Agent de navegador):
```bash
curl -A "Mozilla/5.0" \
  "https://mapa2.electoral.gov.ar/geoserver/wfs?service=WFS&version=1.0.0&request=GetFeature&authkey=${CNE_AUTHKEY}&typeName=descargas:circuito_04&outputFormat=application%2Fjson"
```

Listado de capas disponibles (GetCapabilities):
```bash
curl -A "Mozilla/5.0" \
  "https://mapa2.electoral.gov.ar/geoserver/wfs?service=WFS&version=1.0.0&request=GetCapabilities&authkey=${CNE_AUTHKEY}"
```

Descarga de resultados 2023 (DINE):
```bash
curl -A "Mozilla/5.0" -o data/raw/resultados_generales_2023.zip \
  "https://www.argentina.gob.ar/sites/default/files/2023_generales_1.zip"
```

Generación de la jerarquía limpia (en este orden):
```bash
python3 scripts/extraer_circuitos_2023.py
python3 scripts/generar_jerarquia.py
```
