#!/bin/bash

echo "🐳 === Administrador de Docker para DBCoop Sincronizador ==="
echo ""

# Crear directorios necesarios
mkdir -p logs backups

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  build    - Construir la imagen Docker"
    echo "  test     - Probar conexiones a las bases de datos"
    echo "  sync     - Ejecutar sincronización manual"
    echo "  start    - Iniciar sincronizador automático (programado)"
    echo "  stop     - Detener todos los contenedores"
    echo "  logs     - Ver logs del contenedor"
    echo "  shell    - Abrir shell interactiva en el contenedor"
    echo "  rebuild  - Reconstruir imagen desde cero"
    echo "  status   - Ver estado de contenedores"
    echo "  clean    - Limpiar contenedores e imágenes no usadas"
    echo ""
    echo "Ejemplos:"
    echo "  $0 build      # Construir imagen"
    echo "  $0 test       # Probar conexiones"
    echo "  $0 sync       # Sincronización manual"
    echo "  $0 start      # Iniciar programador automático"
}

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor, instala Docker primero."
    echo "   Instrucciones: https://docs.docker.com/engine/install/"
    exit 1
fi

# Verificar que docker-compose esté disponible
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose no está disponible."
    echo "   Instala docker-compose o usa Docker con plugin compose"
    exit 1
fi

# Determinar comando de compose
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Procesar comando
case "$1" in
    "build")
        echo "🔨 Construyendo imagen Docker..."
        $COMPOSE_CMD build
        echo "✅ Imagen construida exitosamente!"
        ;;
        
    "test")
        echo "🧪 Probando conexiones a las bases de datos..."
        $COMPOSE_CMD run --rm dbcoop-test
        ;;
        
    "sync")
        echo "🔄 Ejecutando sincronización manual..."
        $COMPOSE_CMD run --rm dbcoop-manual
        ;;
        
    "start")
        echo "🚀 Iniciando sincronizador automático..."
        $COMPOSE_CMD up -d dbcoop-sync
        echo "✅ Sincronizador iniciado!"
        echo "📝 Ver logs: $0 logs"
        echo "🛑 Detener: $0 stop"
        ;;
        
    "stop")
        echo "🛑 Deteniendo todos los contenedores..."
        $COMPOSE_CMD down
        echo "✅ Contenedores detenidos!"
        ;;
        
    "logs")
        echo "📋 Mostrando logs del sincronizador..."
        $COMPOSE_CMD logs -f dbcoop-sync
        ;;
        
    "shell")
        echo "🐚 Abriendo shell en el contenedor..."
        $COMPOSE_CMD run --rm dbcoop-sync bash
        ;;
        
    "rebuild")
        echo "🔄 Reconstruyendo imagen desde cero..."
        $COMPOSE_CMD down
        $COMPOSE_CMD build --no-cache
        echo "✅ Imagen reconstruida!"
        ;;
        
    "status")
        echo "📊 Estado de contenedores:"
        $COMPOSE_CMD ps
        echo ""
        echo "🐳 Imágenes Docker:"
        docker images | grep dbcoop
        ;;
        
    "clean")
        echo "🧹 Limpiando contenedores e imágenes no usadas..."
        $COMPOSE_CMD down
        docker system prune -f
        echo "✅ Limpieza completada!"
        ;;
        
    *)
        show_help
        exit 1
        ;;
esac 