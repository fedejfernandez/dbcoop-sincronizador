#!/bin/bash

echo "=== Configurador de Cron para Sincronización Automática ==="
echo ""

# Obtener directorio actual
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"
SCRIPT_PATH="$SCRIPT_DIR/db_sync.py"

# Verificar que los archivos existen
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ No se encontró el entorno virtual. Ejecuta install.sh primero."
    exit 1
fi

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ No se encontró db_sync.py"
    exit 1
fi

# Leer hora de sincronización del archivo de configuración
SYNC_TIME="02:00"
if [ -f "$SCRIPT_DIR/config.env" ]; then
    SYNC_TIME=$(grep "SYNC_TIME=" "$SCRIPT_DIR/config.env" | cut -d'=' -f2)
fi

# Convertir hora a formato cron (HH:MM -> MM HH)
HOUR=$(echo $SYNC_TIME | cut -d':' -f1)
MINUTE=$(echo $SYNC_TIME | cut -d':' -f2)

# Crear comando cron
CRON_COMMAND="$MINUTE $HOUR * * * cd $SCRIPT_DIR && $PYTHON_PATH $SCRIPT_PATH sync >> $SCRIPT_DIR/cron.log 2>&1"

echo "Configurando cron para ejecutar todos los días a las $SYNC_TIME"
echo "Comando: $CRON_COMMAND"
echo ""

# Hacer backup del crontab actual
echo "📋 Haciendo backup del crontab actual..."
crontab -l > "$SCRIPT_DIR/crontab_backup.txt" 2>/dev/null || echo "No hay crontab previo"

# Añadir nueva entrada
echo "➕ Añadiendo entrada al crontab..."
(crontab -l 2>/dev/null | grep -v "db_sync.py"; echo "$CRON_COMMAND") | crontab -

# Verificar que se añadió correctamente
echo "✅ Entrada añadida al crontab:"
crontab -l | grep "db_sync.py"

echo ""
echo "🎉 Configuración de cron completada!"
echo ""
echo "La sincronización se ejecutará automáticamente todos los días a las $SYNC_TIME"
echo "Los logs se guardarán en: $SCRIPT_DIR/cron.log"
echo ""
echo "Para verificar el estado del cron:"
echo "  crontab -l"
echo ""
echo "Para ver los logs:"
echo "  tail -f $SCRIPT_DIR/cron.log"
echo ""
echo "Para eliminar la tarea programada:"
echo "  crontab -e (y eliminar la línea manualmente)" 