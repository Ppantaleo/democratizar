# Infraestructura (CloudFormation)

`base.yaml` crea la infraestructura del piloto en us-east-1.

| Recurso | Configuración | USD/mes aprox. |
|---|---|---|
| EC2 Ubuntu 24.04 | t3a.medium, créditos `standard`, 30 GB gp3 cifrado, IMDSv2 | ~30 |
| IP elástica | IPv4 fija para Cloudflare | ~3,6 |
| RDS PostgreSQL 17 | db.t4g.micro, una zona, 20 GB gp3 cifrado, privada, 7 días de backup | ~14 |
| Secrets Manager | contraseña de la RDS | ~0,4 |
| S3 | privado, cifrado; `dumps/` expira a los 90 días | < 1 |
| VPC | subred pública (EC2), dos privadas (RDS), endpoint S3; **sin NAT** | 0 |

Acceso al servidor solo por SSM: no hay SSH ni par de claves. Puertos
abiertos: 80 y 443. La RDS acepta conexiones solo desde la EC2.

DynamoDB no se crea acá: Delphi crea sus propias tablas. El rol de la
instancia tiene permiso sobre las tablas de la cuenta en la región.

## Desplegar

Requiere un perfil de AWS CLI de la cuenta donde se despliega (en este
ejemplo, `democratizar`):

```bash
aws configure --profile democratizar
aws sts get-caller-identity --profile democratizar
```

Validar y desplegar:

```bash
aws cloudformation validate-template \
  --template-body file://infra/base.yaml \
  --profile democratizar --region us-east-1

aws cloudformation deploy \
  --template-file infra/base.yaml \
  --stack-name democratizar-base \
  --capabilities CAPABILITY_IAM \
  --tags Proyecto=democratizar \
  --profile democratizar --region us-east-1
```

La etiqueta `Proyecto=democratizar` se propaga a todos los recursos. La RDS
tarda unos 10 minutos.

Ver las salidas (IP, endpoint de la base, comando de SSM):

```bash
aws cloudformation describe-stacks --stack-name democratizar-base \
  --query 'Stacks[0].Outputs' --output table \
  --profile democratizar --region us-east-1
```

## Borrar

```bash
aws cloudformation delete-stack --stack-name democratizar-base \
  --profile democratizar --region us-east-1
```

- La RDS deja un snapshot final (se cobra el almacenamiento hasta que se
  borre a mano).
- El bucket S3 se conserva (`DeletionPolicy: Retain`).

## Pendientes

- Restringir los puertos 80/443 a los rangos de IP de Cloudflare.
- Acotar el permiso de DynamoDB al prefijo de tablas de Delphi.
- Presupuesto filtrado por `Proyecto=democratizar` (activar la etiqueta en
  Facturación → Etiquetas de asignación de costos).
