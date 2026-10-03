# democratiz.ar

Plataforma para relevar y priorizar agenda ciudadana en los mismos niveles
territoriales en los que se eligen representantes en Argentina: nacional,
provincial, departamental y local. Usa [Pol.is](https://github.com/compdemocracy/polis)
como motor de votación y agrupamiento de opiniones.

Proyecto en desarrollo; piloto en General Levalle, Córdoba.

## Contenido

- `docs/ARQUITECTURA.md`: diseño de niveles, infraestructura y decisiones.
- `docs/METODOLOGIA_JERARQUIA_CIRCUITOS.md`: fuentes y limpieza de la
  jerarquía de circuitos electorales (CNE 2017 y DINE 2023).
- `scripts/`: generación de la jerarquía de circuitos.
- `data/processed/`: jerarquía resultante (5.760 circuitos).

## Fuentes de datos

- Padrón electoral 2017, Cámara Nacional Electoral.
- Resultados provisorios elecciones generales 2023, Dirección Nacional
  Electoral.

## Licencia

- **Código** (`scripts/` y el código de la aplicación): [GNU AGPL-3.0](LICENSE).
- **Documentación y datos** (`docs/`, `data/processed/`):
  [CC BY 4.0](LICENSE-DOCS). Los datos derivan de fuentes públicas de la
  CNE y la DINE; citar este repositorio y las fuentes originales.
