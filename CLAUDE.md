# democratiz.ar

Plataforma de agenda ciudadana sobre Pol.is, organizada en los niveles
territoriales en los que se eligen representantes (nacional, provincial,
departamental, local). Arquitectura y decisiones en `docs/ARQUITECTURA.md`;
datos territoriales en `docs/METODOLOGIA_JERARQUIA_CIRCUITOS.md`.

## Convenciones

- Responder y documentar en español; mayúsculas según la RAE (solo primera
  palabra y nombres propios, también en títulos).
- Las decisiones registradas en `docs/ARQUITECTURA.md` están cerradas: no
  volver a discutirlas salvo pedido explícito.
- Comandos en el servidor: uno por vez, por SSM; marcar con [MODIFICA] los
  que cambian el sistema y esperar el resultado antes de seguir.
- Backup de la base antes de cualquier cambio de esquema o datos.
- Sin secretos en el repositorio (es público): usar variables de entorno.
- Commits sin atribución a Claude.

## Datos

- `data/raw/` no se versiona; se descarga con los comandos de la metodología.
- Regenerar los datos procesados:
  `python3 scripts/extraer_circuitos_2023.py && python3 scripts/generar_jerarquia.py`
- El CSV principal es `data/processed/jerarquia_circuitos.csv`; la clave es
  `id_local` (`AR-<distrito>-<secc>-<circu>`).

## Estado

Ver la sección "Pendientes" de `docs/ARQUITECTURA.md`. Infraestructura base
en `infra/base.yaml` (instrucciones en `infra/README.md`). Próximo paso:
desplegar el stack `democratizar-base` e instalar Pol.is en la EC2.
