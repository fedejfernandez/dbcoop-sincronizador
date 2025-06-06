# 🚀 Guía de Despliegue - DBCoop Sincronizador

## 📦 Preparación Completada

✅ **Repositorio Git configurado**  
✅ **Archivos de configuración listos**  
✅ **Scripts de despliegue incluidos**  
✅ **Documentación completa**  
✅ **Sistema probado y funcionando**

---

## 🌐 Subir a Repositorio Remoto

### 1. Crear Repositorio en GitHub/GitLab

Crea un nuevo repositorio en tu plataforma preferida:
- **GitHub**: https://github.com/new
- **GitLab**: https://gitlab.com/projects/new
- **Bitbucket**: https://bitbucket.org/repo/create

**Nombre sugerido**: `dbcoop-sincronizador`

### 2. Conectar Repositorio Local

```bash
# Agregar origen remoto (reemplaza con tu URL)
git remote add origin https://github.com/tu_usuario/dbcoop-sincronizador.git

# Verificar configuración
git remote -v

# Cambiar a rama main (opcional)
git branch -M main

# Subir código
git push -u origin main
```

---

## 🖥️ Despliegue en Servidor Nuevo

### Opción A: Despliegue Automatizado
```bash
# En el servidor de destino
git clone https://github.com/tu_usuario/dbcoop-sincronizador.git
cd dbcoop-sincronizador

# Ejecutar script de despliegue
chmod +x deploy.sh
./deploy.sh
```

### Opción B: Despliegue Manual
```bash
# 1. Clonar repositorio
git clone https://github.com/tu_usuario/dbcoop-sincronizador.git
cd dbcoop-sincronizador

# 2. Configurar variables
cp config.env.example config.env
nano config.env  # Editar credenciales

# 3. Dar permisos
chmod +x *.sh

# 4. Construir y probar
./build-docker.sh build
./build-docker.sh test

# 5. Ejecutar primera sincronización
./build-docker.sh sync

# 6. Iniciar servicio automático
./build-docker.sh start
```

---

## ⚙️ Configuración en Servidor de Destino

### 1. Variables de Entorno Críticas
```bash
# En config.env - ACTUALIZAR CON VALORES REALES:

# SQL Server (Origen)
SQLSERVER_HOST=192.168.0.231          # IP del servidor SQL Server
SQLSERVER_DATABASE=PR_FLOR            # Nombre de la base
SQLSERVER_USERNAME=tu_usuario          # Usuario SQL Server
SQLSERVER_PASSWORD=tu_password         # Password SQL Server

# MariaDB (Destino)
MARIADB_HOST=localhost                 # IP del MariaDB
MARIADB_USERNAME=tu_usuario_mariadb    # Usuario MariaDB
MARIADB_PASSWORD=tu_password_mariadb   # Password MariaDB

# Tablas a sincronizar
TABLES_TO_SYNC=SOCIOS,PERSONAS,SERSOC,CUENTAS,PAG_SOC,SUMSOC_HST
```

### 2. Verificación de Red
```bash
# Probar conectividad SQL Server
ping 192.168.0.231
telnet 192.168.0.231 1433

# Probar conectividad MariaDB local
docker ps | grep mariadb
./build-docker.sh test
```

---

## 🔧 Comandos Post-Despliegue

### Gestión del Servicio
```bash
# Ver estado
./build-docker.sh status

# Sincronización manual
./build-docker.sh sync

# Ver logs en tiempo real
./build-docker.sh logs

# Reiniciar servicio
./build-docker.sh stop
./build-docker.sh start
```

### Monitoreo
```bash
# Verificar datos sincronizados
docker exec -it cooperativa-rrhh-mariadb-1 mariadb -u intradb -pIntradb1256 procoop -e "SELECT table_name, table_rows FROM information_schema.tables WHERE table_schema = 'procoop' ORDER BY table_rows DESC;"

# Crear backup manual
./backup.sh

# Ver logs del sistema
sudo journalctl -u dbcoop-sync.service -f
```

---

## 📋 Checklist de Despliegue

### Pre-Despliegue
- [ ] Servidor con Docker instalado
- [ ] Acceso de red a SQL Server origen
- [ ] MariaDB configurado y accesible
- [ ] Credenciales de ambas bases de datos
- [ ] Puertos necesarios abiertos (1433, 3306)

### Durante Despliegue
- [ ] Repositorio clonado correctamente
- [ ] `config.env` configurado con credenciales reales
- [ ] Imagen Docker construida sin errores
- [ ] Prueba de conexiones exitosa
- [ ] Primera sincronización completada

### Post-Despliegue
- [ ] Servicio automático funcionando
- [ ] Logs generándose correctamente
- [ ] Backup configurado (opcional)
- [ ] Monitoreo configurado
- [ ] Documentación entregada al equipo

---

## 🚨 Resolución de Problemas Comunes

### Error: "No se puede conectar a SQL Server"
```bash
# Verificar conectividad
ping 192.168.0.231
telnet 192.168.0.231 1433

# Revisar logs
./build-docker.sh logs

# Probar diferentes configuraciones
./build-docker.sh test
```

### Error: "Access denied MariaDB"
```bash
# Verificar contenedor MariaDB
docker ps | grep mariadb

# Verificar credenciales en config.env
cat config.env | grep MARIADB

# Conectar manualmente para probar
docker exec -it cooperativa-rrhh-mariadb-1 mariadb -u intradb -p
```

### Error: "Docker build failed"
```bash
# Limpiar Docker
./build-docker.sh clean

# Reconstruir desde cero
./build-docker.sh rebuild

# Verificar espacio en disco
df -h
```

---

## 📞 Información de Contacto

**Desarrollador**: Federico J. Fernández  
**Email**: federicojfernandez@gmail.com  
**Repositorio**: [Agregar URL después de crear]

---

## 📈 Métricas de Rendimiento Esperadas

- **SUMSOC_HST**: ~24K registros en 30 segundos
- **USUARIOS_GIS**: ~20K registros en 25 segundos
- **Throughput promedio**: 800-1000 registros/segundo
- **Uso de memoria**: <512MB durante sincronización
- **Tiempo total sincronización completa**: 5-10 minutos (depende de tablas configuradas)

¡Despliegue listo para producción! 🎉 