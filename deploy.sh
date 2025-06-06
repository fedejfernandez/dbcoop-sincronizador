#!/bin/bash

# ===============================================
# Script de Despliegue - DBCoop Sincronizador
# ===============================================

set -e  # Salir en caso de error

echo "🚀 === Despliegue de DBCoop Sincronizador ==="
echo ""

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar si es root
if [[ $EUID -eq 0 ]]; then
   error "Este script no debe ejecutarse como root"
   exit 1
fi

# 1. Verificar requisitos del sistema
info "Verificando requisitos del sistema..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    warning "Docker no está instalado. Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    success "Docker instalado correctamente"
    warning "Reinicia la sesión para usar Docker sin sudo"
else
    success "Docker ya está instalado"
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    warning "Docker Compose no está instalado. Instalando..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    success "Docker Compose instalado correctamente"
else
    success "Docker Compose ya está instalado"
fi

# 2. Configuración del proyecto
info "Configurando proyecto..."

# Verificar si existe config.env
if [ ! -f "config.env" ]; then
    warning "Archivo config.env no encontrado. Creando desde template..."
    if [ -f "config.env.example" ]; then
        cp config.env.example config.env
        warning "¡IMPORTANTE! Edita config.env con tus credenciales reales antes de continuar"
        echo ""
        echo "Ejecuta: nano config.env"
        echo ""
        read -p "Presiona Enter después de configurar config.env..."
    else
        error "No se encontró config.env.example"
        exit 1
    fi
else
    success "Archivo config.env encontrado"
fi

# 3. Crear directorios necesarios
info "Creando directorios..."
mkdir -p logs backups
success "Directorios creados"

# 4. Construir imagen Docker
info "Construyendo imagen Docker..."
if ./build-docker.sh build; then
    success "Imagen Docker construida exitosamente"
else
    error "Error construyendo imagen Docker"
    exit 1
fi

# 5. Probar conexiones
info "Probando conexiones a las bases de datos..."
if ./build-docker.sh test; then
    success "Conexiones probadas exitosamente"
else
    warning "Error en las conexiones. Verifica config.env"
    echo ""
    echo "Para revisar configuración:"
    echo "  nano config.env"
    echo ""
    echo "Para probar conexiones:"
    echo "  ./build-docker.sh test"
    exit 1
fi

# 6. Configurar servicio systemd (opcional)
read -p "¿Deseas configurar el servicio como systemd? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Configurando servicio systemd..."
    
    sudo tee /etc/systemd/system/dbcoop-sync.service > /dev/null << EOF
[Unit]
Description=DBCoop Database Synchronizer
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/build-docker.sh sync
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Crear timer para ejecución automática
    sudo tee /etc/systemd/system/dbcoop-sync.timer > /dev/null << EOF
[Unit]
Description=DBCoop Sync Timer
Requires=dbcoop-sync.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable dbcoop-sync.timer
    sudo systemctl start dbcoop-sync.timer
    
    success "Servicio systemd configurado"
    info "Para ver estado: sudo systemctl status dbcoop-sync.timer"
fi

# 7. Configuración de firewall (opcional)
read -p "¿Deseas configurar reglas de firewall básicas? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Configurando firewall..."
    
    # Permitir SSH
    sudo ufw allow ssh
    
    # Permitir conexiones Docker (si es necesario)
    sudo ufw allow from 172.0.0.0/8
    
    success "Firewall configurado"
fi

# 8. Crear script de backup
info "Creando script de backup..."
cat > backup.sh << 'EOF'
#!/bin/bash
# Script de Backup Automático

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

mkdir -p $BACKUP_DIR

echo "🔄 Creando backup de la base de datos..."

# Backup de MariaDB
docker exec cooperativa-rrhh-mariadb-1 mysqldump -u intradb -pIntradb1256 --single-transaction --routines --triggers procoop > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✅ Backup creado: $BACKUP_FILE"
    
    # Comprimir backup
    gzip $BACKUP_FILE
    echo "✅ Backup comprimido: $BACKUP_FILE.gz"
    
    # Limpiar backups antiguos (más de 7 días)
    find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
    echo "🧹 Backups antiguos limpiados"
else
    echo "❌ Error creando backup"
    exit 1
fi
EOF

chmod +x backup.sh
success "Script de backup creado (./backup.sh)"

# 9. Información final
echo ""
success "¡Despliegue completado exitosamente!"
echo ""
echo "📋 Comandos útiles:"
echo "  ./build-docker.sh test     - Probar conexiones"
echo "  ./build-docker.sh sync     - Sincronización manual"
echo "  ./build-docker.sh start    - Iniciar servicio automático"
echo "  ./build-docker.sh logs     - Ver logs"
echo "  ./build-docker.sh status   - Ver estado"
echo "  ./backup.sh                - Crear backup manual"
echo ""
echo "📊 Monitoreo:"
echo "  docker-compose logs -f     - Logs en tiempo real"
echo "  docker ps                  - Estado de contenedores"
echo ""
echo "⚙️  Configuración:"
echo "  nano config.env            - Editar configuración"
echo "  ./build-docker.sh rebuild  - Reconstruir después de cambios"
echo ""

if command -v systemctl &> /dev/null && [ -f /etc/systemd/system/dbcoop-sync.timer ]; then
    echo "🕐 Servicio systemd:"
    echo "  sudo systemctl status dbcoop-sync.timer  - Ver estado del timer"
    echo "  sudo systemctl stop dbcoop-sync.timer    - Detener programación"
    echo "  sudo journalctl -u dbcoop-sync.service   - Ver logs del servicio"
    echo ""
fi

warning "¡Recuerda configurar las credenciales correctas en config.env!"
info "Para una primera sincronización, ejecuta: ./build-docker.sh sync" 