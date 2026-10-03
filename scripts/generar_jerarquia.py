"""
Genera la jerarquía de circuitos electorales (provincia > sección > circuito)
a partir del padrón 2017 de la CNE, excluyendo voto en el exterior,
corrigiendo el encoding mixto de los nombres y agregando IDs jerárquicos.
Si existe data/processed/circuitos_2023.csv (scripts/extraer_circuitos_2023.py),
agrega electores y nombre de sección 2023 y lista los circuitos solo 2023.
"""
import os
import pandas as pd

RUTA_ENTRADA = "data/raw/Padron_2017.xlsx"
RUTA_2023 = "data/processed/circuitos_2023.csv"
RUTA_SALIDA = "data/processed/jerarquia_circuitos.csv"
RUTA_SOLO_2023 = "data/processed/circuitos_solo_2023.csv"
DISTRITO_EXTERIOR = 30
# Neuquén, Santa Fe y Tierra del Fuego renumeraron todos sus circuitos entre
# 2017 y 2023: un mismo código designa lugares distintos, no se cruzan por código.
DISTRITOS_RENUMERADOS_2023 = {15, 21, 24}

# El padrón mezcla textos correctos (latin-1) con textos exportados en CP850.
# Solo se corrigen los caracteres que nunca aparecen legítimamente en nombres
# en castellano; el resto (á, é, í, ó, Ñ, Ü, °) ya viene bien y no se toca.
MARCADORES_CP850 = '\x81\x90¡¤¥µø'
MAPA_CP850 = str.maketrans({
    c: bytes([ord(c)]).decode('cp850') for c in MARCADORES_CP850
})
CARACTERES_ESPERADOS = set('áéíóúÁÉÍÓÚñÑüÜ°')


def fix_encoding(x):
    if not isinstance(x, str):
        return x
    return x.translate(MAPA_CP850)


def normalizar_circu(s):
    """Código comparable entre fuentes: sin ceros iniciales, en mayúsculas."""
    return s.str.strip().str.lstrip('0').str.upper()


def cruzar_2023(jerarquia):
    c23 = pd.read_csv(RUTA_2023, dtype=str)
    c23['distrito'] = c23['distrito_id'].astype(int)
    c23 = c23.rename(columns={
        'circuito_id': 'circu_2023', 'seccion_nombre': 'seccion_2023',
        'electores': 'electores_2023', 'seccion_id': 'secc_2023',
    })
    c23['motivo'] = 'nuevo'
    c23.loc[c23['distrito'].isin(DISTRITOS_RENUMERADOS_2023), 'motivo'] = 'distrito_renumerado'
    cruzable = c23[c23['motivo'] == 'nuevo']

    jerarquia['circu_norm'] = normalizar_circu(jerarquia['circu'])
    jerarquia = jerarquia.merge(
        cruzable[['distrito', 'circu_norm', 'circu_2023', 'secc_2023', 'seccion_2023', 'electores_2023']],
        on=['distrito', 'circu_norm'], how='left', validate='one_to_one'
    )
    claves_2017 = set(zip(jerarquia['distrito'], jerarquia['circu_norm']))
    sin_par_2017 = pd.Series(
        [k not in claves_2017 for k in zip(c23['distrito'], c23['circu_norm'])],
        index=c23.index
    )
    solo_2023 = c23[(c23['motivo'] == 'distrito_renumerado') | sin_par_2017]

    renumerado = jerarquia['distrito'].isin(DISTRITOS_RENUMERADOS_2023)
    jerarquia['presente_2023'] = jerarquia['circu_2023'].notna().astype('boolean')
    jerarquia.loc[renumerado, 'presente_2023'] = pd.NA
    jerarquia['cambio_seccion_2023'] = (
        jerarquia['presente_2023']
        & (jerarquia['secc'].astype(str) != jerarquia['secc_2023'])
    )
    jerarquia['electores_2023'] = jerarquia['electores_2023'].astype('Int64')

    solo_2023[['distrito', 'secc_2023', 'seccion_2023', 'circu_2023', 'electores_2023', 'motivo']] \
        .sort_values(['distrito', 'secc_2023', 'circu_2023']) \
        .to_csv(RUTA_SOLO_2023, index=False)
    print(f"Cruce 2023: {(jerarquia['presente_2023'] == True).sum()} presentes | "
          f"{(jerarquia['presente_2023'] == False).sum()} ausentes | "
          f"{renumerado.sum()} sin cruzar (distritos renumerados) | "
          f"{(solo_2023['motivo'] == 'nuevo').sum()} nuevos en 2023 | "
          f"{jerarquia['cambio_seccion_2023'].sum()} con cambio de sección")
    return jerarquia


def main():
    df = pd.read_excel(RUTA_ENTRADA, dtype={'circu': str})
    df = df[df['distrito'] != DISTRITO_EXTERIOR]

    for col in ['nombre_distrito', 'seccion', 'circuito']:
        df[col] = df[col].apply(fix_encoding).str.strip()
    df['circu'] = df['circu'].str.strip()

    jerarquia = df.groupby(
        ['distrito', 'nombre_distrito', 'secc', 'seccion', 'circu', 'circuito'],
        dropna=False
    )['electores'].sum().reset_index()

    jerarquia['nombre_verificado'] = jerarquia['circuito'].notna()
    jerarquia['circuito'] = jerarquia['circuito'].fillna(
        'Circuito ' + jerarquia['circu']
    )

    # IDs jerárquicos: el código de circuito se conserva tal cual lo publica
    # la CNE (sin relleno), para que sea trazable a la fuente oficial.
    jerarquia['id_provincial'] = 'AR-' + jerarquia['distrito'].astype(str).str.zfill(2)
    jerarquia['id_departamental'] = (
        jerarquia['id_provincial'] + '-' + jerarquia['secc'].astype(str).str.zfill(3)
    )
    jerarquia['id_local'] = jerarquia['id_departamental'] + '-' + jerarquia['circu']

    assert jerarquia['id_local'].is_unique, "id_local duplicado"

    columnas = ['id_local', 'id_departamental', 'id_provincial',
                'distrito', 'nombre_distrito', 'secc', 'seccion',
                'circu', 'circuito', 'electores', 'nombre_verificado']

    if os.path.exists(RUTA_2023):
        jerarquia = cruzar_2023(jerarquia)
        columnas += ['presente_2023', 'circu_2023', 'seccion_2023',
                     'electores_2023', 'cambio_seccion_2023']
    else:
        print(f"Sin {RUTA_2023}: se omite el cruce con 2023")

    residuales = {
        c for col in ['nombre_distrito', 'seccion', 'circuito']
        for v in jerarquia[col] for c in v
        if ord(c) > 127 and c not in CARACTERES_ESPERADOS
    }
    if residuales:
        print(f"ADVERTENCIA: caracteres no esperados: {sorted(residuales)}")

    jerarquia[columnas].to_csv(RUTA_SALIDA, index=False)
    print(f"Circuitos: {jerarquia.shape[0]} | Distritos: {jerarquia['distrito'].nunique()}")
    print(f"Sin nombre verificado: {(~jerarquia['nombre_verificado']).sum()}")


if __name__ == "__main__":
    main()
