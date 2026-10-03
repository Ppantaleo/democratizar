# Arquitectura de democratiz.ar

## Qué es

Plataforma para relevar y priorizar agenda ciudadana en los mismos niveles
territoriales en los que se eligen representantes. Usa
[Pol.is](https://github.com/compdemocracy/polis) como motor de votación y
agrupamiento de opiniones, con una capa propia que organiza las
conversaciones en jerarquía.

## Niveles y conversaciones

Una sola instalación de Pol.is; una conversación por nodo del árbol.

| Nivel | ID | Quién participa | Arranque |
|---|---|---|---|
| Nacional | `AR` | Todos los usuarios | Statements iniciales editoriales |
| Provincial | `AR-04` | Usuarios de la provincia | Statements iniciales editoriales |
| Departamental | `AR-04-017` | Usuarios de la sección | Pregunta disparadora |
| Local | `AR-04-017-252` | Usuarios del circuito | Pregunta disparadora |

Los IDs salen de `data/processed/jerarquia_circuitos.csv` (ver
[METODOLOGIA_JERARQUIA_CIRCUITOS.md](METODOLOGIA_JERARQUIA_CIRCUITOS.md)).

- **Asignación del usuario:** selección manual en cascada
  (provincia → sección → circuito). Sin geolocalización en el MVP.
- **Statements:** cualquier participante habilitado puede proponer; la
  moderación es humana.
- **Promoción entre niveles:** curada. Un statement con consenso o disenso
  marcado en varios nodos hijos puede sembrarse en el nivel superior,
  registrando su origen.

## Piloto

General Levalle, Córdoba: `AR-04-017-252` (circuito 252 "LEVALLE", sección
17 Presidente Roque Sáenz Peña; 5.236 electores en 2023).

## Infraestructura (AWS, us-east-1)

```
           Cloudflare (DNS, TLS, WAF)
                     │
   ┌──────── EC2 t3a.medium (SSM) ──────┐
   │ nginx                              │
   │  ├─ democratiz.ar       → app      │
   │  └─ polis.democratiz.ar → Pol.is   │
   │ Docker: Pol.is (server, math,      │
   │         Delphi, clientes)          │
   └────┬──────────────┬──────────┬─────┘
        │ red privada  │          │ rol de instancia
   RDS PostgreSQL    S3       DynamoDB
   (polis +       (reportes,  (resultados
    democratizar)  dumps)      de Delphi)
```

| Componente | Decisión | Motivo |
|---|---|---|
| Cómputo | EC2 t3a.medium (4 GB), modo de créditos `standard` | Piloto chico; se amplía cambiando el tipo |
| Base de datos | RDS PostgreSQL db.t4g.micro, fuera de la EC2 | Pol.is exige PostgreSQL; backups gestionados |
| Archivos | S3 | Reportes de Delphi y dumps |
| Resultados de Delphi | DynamoDB on-demand | Lo exige Delphi en producción |
| Etiquetado de temas | API de Anthropic | Sin Ollama: no entra en 4 GB |
| Acceso al servidor | SSM, sin SSH | Sin puertos de administración abiertos |
| Infraestructura | CloudFormation | Reproducible y borrable |
| Aplicación propia | Node (a confirmar: Astro o Next.js) | Mismo lenguaje que Pol.is |

### Ajustes necesarios para 4 GB

- Ollama desactivado.
- Tope de memoria de Delphi (`DELPHI_CONTAINER_MEMORY`) en 1,5–2 GB
  (por defecto 16 GB).
- Imágenes construidas fuera de la instancia o descargadas.
- 4 GB de swap.

### Control de costos

- AWS Budgets con alertas al 50 %, 80 % y 100 %.
- Sin NAT Gateway (EC2 en subred pública, RDS en subred privada).
- Etiqueta `Proyecto=democratizar` en todos los recursos.
- Snapshot de RDS al borrar el stack.
- Costo estimado del piloto: ~50 USD/mes.

### Escalado

La base, los archivos y los resultados ya están fuera de la EC2. Para
escalar se pasa a la arquitectura de producción de Pol.is: servidores web
detrás de un balanceador, cálculo separado y trabajadores de Delphi. La
aplicación propia no debe guardar estado en la instancia.

Límite conocido: el cálculo de una conversación no se distribuye y su
memoria crece con participantes × statements. El nivel nacional a escala
de millones requiere un diseño propio (muestreo, rondas o conversaciones
temáticas).

## Pendientes

- Verificar si el circuito 252 coincide con el ejido municipal de
  General Levalle.
- Confirmar si Delphi reemplaza por completo a math (Clojure) para correr
  uno solo.
- Verificación de identidad y control de bots antes de escalar.
- Revisión legal: las opiniones políticas son datos sensibles
  (Ley 25.326).
- Pedido de acceso a la información pública a la CNE por la tabla vigente
  de circuitos.
