"""
Colapsa los resultados provisorios de las elecciones generales 2023 (DINE)
a nivel circuito: sección con nombre, código de circuito y electores.
Lee el CSV directamente desde el zip, sin descomprimirlo (~1 GB).
"""
import zipfile
import pandas as pd

RUTA_ENTRADA = "data/raw/resultados_generales_2023.zip"
ARCHIVO_EN_ZIP = "2023_Generales/ResultadoElectorales_2023_Generales.csv"
RUTA_SALIDA = "data/processed/circuitos_2023.csv"
COLUMNAS = ['distrito_id', 'seccion_id', 'seccion_nombre',
            'circuito_id', 'mesa_id', 'mesa_tipo', 'mesa_electores']


def normalizar_circu(s):
    """Código comparable entre fuentes: sin ceros iniciales, en mayúsculas."""
    return s.str.strip().str.lstrip('0').str.upper()


def main():
    partes = []
    with zipfile.ZipFile(RUTA_ENTRADA) as z, z.open(ARCHIVO_EN_ZIP) as f:
        for bloque in pd.read_csv(f, usecols=COLUMNAS, dtype=str, chunksize=2_000_000):
            # Las mesas de extranjeros no votan en elecciones nacionales
            bloque = bloque[bloque['mesa_tipo'] == 'NATIVOS'].copy()
            # En CABA el mismo circuito aparece como "00001" y como "1"
            # según la fila; se deduplica sobre el código normalizado.
            bloque['circu_norm'] = normalizar_circu(bloque['circuito_id'])
            partes.append(bloque.drop_duplicates(['distrito_id', 'circu_norm', 'mesa_id']))

    mesas = pd.concat(partes).drop_duplicates(['distrito_id', 'circu_norm', 'mesa_id'])
    mesas['mesa_electores'] = mesas['mesa_electores'].astype(int)
    # Se conserva el código en su forma larga (5 caracteres) cuando existe
    mesas['largo'] = mesas['circuito_id'].str.len()
    mesas = mesas.sort_values('largo', ascending=False)

    circuitos = mesas.groupby(['distrito_id', 'circu_norm']).agg(
        seccion_id=('seccion_id', 'first'),
        seccion_nombre=('seccion_nombre', 'first'),
        circuito_id=('circuito_id', 'first'),
        electores=('mesa_electores', 'sum'),
        secciones_distintas=('seccion_id', 'nunique'),
    ).reset_index()

    assert (circuitos['secciones_distintas'] == 1).all(), "circuito en más de una sección"
    circuitos.drop(columns='secciones_distintas').to_csv(RUTA_SALIDA, index=False)
    print(f"Circuitos 2023: {len(circuitos)} | Electores: {circuitos['electores'].sum()}")


if __name__ == "__main__":
    main()
