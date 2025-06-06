#!/bin/bash

echo "=== Instalador de Sincronizador de Base de Datos ==="
echo "SQL Server -> MariaDB"
echo ""

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado. Por favor, instala Python3 primero."
    exit 1
fi

echo "✓ Python3 encontrado: $(python3 --version)"

# Verificar si pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 no está instalado. Instalando pip..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

echo "✓ pip3 encontrado: $(pip3 --version)"

# Instalar dependencias del sistema para pyodbc
echo "📦 Instalando dependencias del sistema..."
sudo apt-get update
sudo apt-get install -y curl apt-transport-https

# Añadir repositorio de Microsoft para ODBC Driver
if [ ! -f /etc/apt/sources.list.d/mssql-release.list ]; then
    echo "📥 Añadiendo repositorio de Microsoft..."
    curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
    curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
    sudo apt-get update
fi

# Instalar ODBC Driver para SQL Server
echo "🔧 Instalando ODBC Driver para SQL Server..."
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Instalar dependencias adicionales
echo "📦 Instalando dependencias adicionales..."
sudo apt-get install -y unixodbc-dev g++ python3-dev

# Crear entorno virtual
echo "🐍 Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

# Actualizar pip
echo "⬆️ Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias de Python
echo "📦 Instalando dependencias de Python..."
pip install -r requirements.txt

echo ""
echo "✅ Instalación completada exitosamente!"
echo ""
echo "Para usar el sincronizador:"
echo "1. Edita el archivo 'config.env' con tus credenciales de base de datos"
echo "2. Activa el entorno virtual: source venv/bin/activate"
echo "3. Ejecuta: python db_sync.py test (para probar conexiones)"
echo "4. Ejecuta: python db_sync.py sync (para sincronización manual)"
echo "5. Ejecuta: python db_sync.py schedule (para programación automática)"
echo ""
echo "📝 Recuerda configurar las variables en config.env antes de usar!" 