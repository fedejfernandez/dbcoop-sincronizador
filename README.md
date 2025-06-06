# Sincronizador de Base de Datos SQL Server a MariaDB

**Autor:** fedejfernadez

Este proyecto implementa un sincronizador automático de bases de datos que transfiere datos desde SQL Server a MariaDB. Está diseñado para ejecutarse como un servicio programado dentro de un contenedor Docker.

## 🚀 Características

- ✅ Sincronización automática SQL Server → MariaDB
- ✅ Soporte para múltiples tablas configurables
- ✅ Mapeo automático de tipos de datos
- ✅ Conexión resiliente con múltiples fallbacks
- ✅ Ejecución programada (cron-like)
- ✅ Logs detallados y monitoreo
- ✅ Contenedor Docker completo
- ✅ Respaldos automáticos

## 📋 Requisitos

### Para Ejecución con Docker (Recomendado)
- Docker y Docker Compose
- Acceso de red a SQL Server origen
- Acceso a MariaDB destino

### Para Ejecución Nativa
- Ubuntu 20.04+ (recomendado para drivers)
- Python 3.8+
- Drivers ODBC para SQL Server
- Acceso a bases de datos

## 🔧 Instalación Rápida

### 1. Clonar Repositorio
```bash
git clone <url-del-repositorio>
cd dbcoop
```

### 2. Configurar Variables de Entorno
```bash
cp config.env.example config.env
nano config.env  # Editar con tus credenciales
```

### 3. Ejecutar con Docker
```bash
# Construir imagen
./build-docker.sh build

# Probar conexiones
./build-docker.sh test

# Sincronización manual
./build-docker.sh sync

# Iniciar servicio automático
./build-docker.sh start
```

## ⚙️ Configuración

### Variables de Entorno (`config.env`)

```bash
# SQL Server (Origen)
SQLSERVER_HOST=192.168.0.231
SQLSERVER_PORT=1433
SQLSERVER_DATABASE=PR_FLOR
SQLSERVER_USERNAME=tu_usuario
SQLSERVER_PASSWORD=tu_password

# MariaDB (Destino)
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_DATABASE=procoop
MARIADB_USERNAME=root
MARIADB_PASSWORD=tu_password

# Sincronización
SYNC_TIME=00:00                    # Hora de ejecución automática
TABLES_TO_SYNC=SOCIOS,PERSONAS     # Tablas a sincronizar
LOG_LEVEL=INFO                     # Nivel de logs
BACKUP_RETENTION_DAYS=7            # Días de retención de backups
```

### Tablas Disponibles
- `SOCIOS` - Información de socios
- `PERSONAS` - Datos personales
- `SERSOC` - Servicios de socios
- `CUENTAS` - Información de cuentas
- `PAG_SOC` - Pagos de socios
- `SUMSOC_HST` - Historial de suministros
- `USUARIOS_GIS` - Usuarios del sistema GIS
- `USERS` - Usuarios del sistema
- `MODULOS` - Módulos del sistema
- `PERFILES` - Perfiles de usuario

## 🐳 Comandos Docker

### Gestión de Contenedores
```bash
./build-docker.sh build     # Construir imagen
./build-docker.sh rebuild   # Reconstruir desde cero
./build-docker.sh test      # Probar conexiones
./build-docker.sh sync      # Sincronización manual
./build-docker.sh start     # Iniciar servicio automático
./build-docker.sh stop      # Detener servicios
./build-docker.sh logs      # Ver logs
./build-docker.sh shell     # Shell interactiva
./build-docker.sh status    # Ver estado
./build-docker.sh clean     # Limpiar recursos
```

### Docker Compose Manual
```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f

# Detener servicios
docker-compose down
```

## 💻 Ejecución Nativa (Alternativa)

### 1. Instalación de Dependencias
```bash
# Instalar sistema
sudo ./install.sh

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar Cron (Opcional)
```bash
# Instalar tarea programada
./setup_cron.sh
```

### 3. Ejecutar
```bash
# Probar conexiones
python3 db_sync.py test

# Sincronización manual
python3 db_sync.py sync

# Servicio automático
python3 db_sync.py schedule
```

## 📊 Monitoreo y Logs

### Ubicación de Logs
- **Docker**: `docker-compose logs -f`
- **Nativo**: `./logs/sync_YYYYMM.log`

### Comandos de Monitoreo
```bash
# Ver logs en tiempo real
./build-docker.sh logs

# Ver estado de contenedores
./build-docker.sh status

# Verificar última sincronización
docker exec -it cooperativa-rrhh-mariadb-1 mariadb -u root -p -e "SELECT table_name, table_rows FROM information_schema.tables WHERE table_schema = 'procoop' ORDER BY table_rows DESC;"
```

## 🔧 Resolución de Problemas

### Problemas de Conexión SQL Server
1. **Error SSL Legacy**: El sistema usa pymssql como fallback automático
2. **Driver ODBC no encontrado**: Use Docker (recomendado)
3. **Timeout de conexión**: Verifique firewall y red

### Problemas de MariaDB
1. **Acceso denegado**: Verifique credenciales en `config.env`
2. **Base no existe**: Crear base `procoop` manualmente
3. **Permisos**: Usuario debe tener permisos CREATE, INSERT, UPDATE, DELETE

### Problemas de Docker
```bash
# Limpiar todo y reconstruir
./build-docker.sh clean
./build-docker.sh rebuild

# Ver logs detallados
docker-compose logs --details
```

## 📁 Estructura del Proyecto

```
dbcoop/
├── db_sync.py              # Script principal de sincronización
├── config.env.example      # Plantilla de configuración
├── requirements.txt        # Dependencias Python
├── Dockerfile              # Imagen Docker
├── docker-compose.yml      # Orquestación de servicios
├── build-docker.sh         # Script de gestión Docker
├── install.sh              # Instalador para Ubuntu
├── setup_cron.sh          # Configurador de cron
├── .gitignore             # Archivos ignorados por Git
├── .dockerignore          # Archivos ignorados por Docker
└── README.md              # Esta documentación
```

## 🔄 Flujo de Sincronización

1. **Conexión**: Múltiples métodos de conexión a SQL Server
2. **Validación**: Verificación de tablas y estructura
3. **Mapeo**: Conversión automática de tipos de datos
4. **Transferencia**: Copia completa con chunks de 1000 registros
5. **Verificación**: Confirmación de integridad de datos
6. **Logs**: Registro detallado de todo el proceso

## 🚀 Despliegue en Producción

### Servidor Nuevo
1. Instalar Docker y Docker Compose
2. Clonar repositorio
3. Configurar `config.env`
4. Ejecutar `./build-docker.sh build`
5. Iniciar con `./build-docker.sh start`

### Servidor Existente
1. Verificar compatibilidad de puertos (3306 MariaDB)
2. Ajustar configuración de red en `docker-compose.yml`
3. Configurar backup automático
4. Monitorear logs regularmente

## 📈 Rendimiento

- **SUMSOC_HST**: ~24K registros en ~30 segundos
- **USUARIOS_GIS**: ~20K registros en ~25 segundos
- **Throughput**: ~800-1000 registros/segundo
- **Memoria**: <512MB durante ejecución

## 🔐 Seguridad

- ✅ Credenciales en variables de entorno
- ✅ No exponer puertos innecesarios
- ✅ Conexiones SSL cuando es posible
- ✅ Logs sin credenciales expuestas
- ✅ `.gitignore` configurado correctamente

## 🆘 Soporte

Para problemas o mejoras:
1. Revisar logs detallados
2. Verificar conectividad de red
3. Consultar sección de resolución de problemas
4. Crear issue en el repositorio

---

**Desarrollado por fedejfernadez**  
**Licencia**: MIT  
**Versión**: 1.0.0 