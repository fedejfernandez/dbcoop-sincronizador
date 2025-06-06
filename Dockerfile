# Usar Ubuntu 20.04 que tiene mejor compatibilidad con drivers SQL Server
FROM ubuntu:20.04

# Evitar prompts interactivos durante la instalación
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Mexico_City

# Instalar dependencias básicas
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg2 \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    unixodbc-dev \
    unixodbc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Configurar timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Configurar OpenSSL para permitir algoritmos legacy (necesario para SQL Server antiguo)
RUN echo "[provider_sect]" >> /etc/ssl/openssl.cnf \
    && echo "default = default_sect" >> /etc/ssl/openssl.cnf \
    && echo "legacy = legacy_sect" >> /etc/ssl/openssl.cnf \
    && echo "" >> /etc/ssl/openssl.cnf \
    && echo "[default_sect]" >> /etc/ssl/openssl.cnf \
    && echo "activate = 1" >> /etc/ssl/openssl.cnf \
    && echo "" >> /etc/ssl/openssl.cnf \
    && echo "[legacy_sect]" >> /etc/ssl/openssl.cnf \
    && echo "activate = 1" >> /etc/ssl/openssl.cnf \
    && sed -i '/^\[openssl_init\]/a providers = provider_sect' /etc/ssl/openssl.cnf

# Añadir repositorio de Microsoft para SQL Server ODBC Driver
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl -fsSL https://packages.microsoft.com/config/ubuntu/20.04/prod.list | tee /etc/apt/sources.list.d/mssql-release.list

# Actualizar e instalar ODBC Driver para SQL Server
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 msodbcsql18 \
    && ACCEPT_EULA=Y apt-get install -y mssql-tools \
    && apt-get install -y freetds-dev freetds-bin tdsodbc \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero para aprovechar cache de Docker
COPY requirements.txt .

# Crear entorno virtual e instalar dependencias Python
RUN python3 -m venv /app/venv \
    && /app/venv/bin/pip install --upgrade pip \
    && /app/venv/bin/pip install -r requirements.txt

# Copiar el resto de archivos de la aplicación
COPY . .

# Dar permisos de ejecución a scripts
RUN chmod +x *.sh *.py 2>/dev/null || true

# Configurar variables de entorno para el entorno virtual
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Crear directorio para logs
RUN mkdir -p /app/logs

# Exponer puerto para futuras funcionalidades web (opcional)
EXPOSE 8080

# Comando por defecto
CMD ["python", "db_sync.py"] 