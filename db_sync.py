#!/usr/bin/env python3
"""
Sincronizador de Base de Datos: SQL Server a MariaDB
Autor: DBCoop
Descripción: Script para sincronizar datos entre SQL Server y MariaDB automáticamente
"""

import os
import sys
import logging
import pandas as pd
import pyodbc
import pymssql
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine
import schedule
import time
import traceback
import re

class DatabaseSyncronizer:
    def __init__(self):
        # Cargar variables de entorno
        load_dotenv('config.env')
        
        # Configurar logging
        self.setup_logging()
        
        # Configuraciones de conexión
        self.sqlserver_config = {
            'host': os.getenv('SQLSERVER_HOST'),
            'port': os.getenv('SQLSERVER_PORT'),
            'database': os.getenv('SQLSERVER_DATABASE'),
            'username': os.getenv('SQLSERVER_USERNAME'),
            'password': os.getenv('SQLSERVER_PASSWORD'),
            'driver': os.getenv('SQLSERVER_DRIVER')
        }
        
        self.mariadb_config = {
            'host': os.getenv('MARIADB_HOST'),
            'port': int(os.getenv('MARIADB_PORT', 3306)),
            'database': os.getenv('MARIADB_DATABASE'),
            'username': os.getenv('MARIADB_USERNAME'),
            'password': os.getenv('MARIADB_PASSWORD')
        }
        
        # Configuraciones de sincronización
        self.tables_to_sync = os.getenv('TABLES_TO_SYNC', '').split(',')
        self.sync_time = os.getenv('SYNC_TIME', '02:00')
        
        self.logger.info("Sincronizador inicializado correctamente")
    
    def setup_logging(self):
        """Configurar el sistema de logging"""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_filename = f"sync_log_{datetime.now().strftime('%Y%m')}.log"
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def test_connections(self):
        """Probar las conexiones a ambas bases de datos"""
        self.logger.info("Probando conexiones a las bases de datos...")
        
        # Probar SQL Server
        try:
            sqlserver_conn = self.connect_sqlserver()
            sqlserver_conn.close()
            self.logger.info("✓ Conexión a SQL Server exitosa")
        except Exception as e:
            self.logger.error(f"✗ Error conectando a SQL Server: {str(e)}")
            return False
        
        # Probar MariaDB
        try:
            mariadb_conn = self.connect_mariadb()
            mariadb_conn.close()
            self.logger.info("✓ Conexión a MariaDB exitosa")
        except Exception as e:
            self.logger.error(f"✗ Error conectando a MariaDB: {str(e)}")
            return False
        
        return True
    
    def connect_sqlserver(self):
        """Conectar a SQL Server"""
        # Intentar diferentes configuraciones de conexión
        connection_configs = [
            # Configuración 1: Microsoft ODBC Driver 17 - Sin cifrado
            f"DRIVER={{{self.sqlserver_config['driver']}}};"
            f"SERVER={self.sqlserver_config['host']},{self.sqlserver_config['port']};"
            f"DATABASE={self.sqlserver_config['database']};"
            f"UID={self.sqlserver_config['username']};"
            f"PWD={self.sqlserver_config['password']};"
            "Encrypt=No;"
            "TrustServerCertificate=Yes;",
            
            # Configuración 2: Microsoft ODBC Driver 17 - Cifrado opcional
            f"DRIVER={{{self.sqlserver_config['driver']}}};"
            f"SERVER={self.sqlserver_config['host']},{self.sqlserver_config['port']};"
            f"DATABASE={self.sqlserver_config['database']};"
            f"UID={self.sqlserver_config['username']};"
            f"PWD={self.sqlserver_config['password']};"
            "Encrypt=Optional;"
            "TrustServerCertificate=Yes;",
            
            # Configuración 3: Microsoft ODBC Driver 17 - Legacy compatible
            f"DRIVER={{{self.sqlserver_config['driver']}}};"
            f"SERVER={self.sqlserver_config['host']};"
            f"DATABASE={self.sqlserver_config['database']};"
            f"UID={self.sqlserver_config['username']};"
            f"PWD={self.sqlserver_config['password']};"
            "Encrypt=No;"
            "TrustServerCertificate=Yes;"
            "Authentication=SqlPassword;",
            
            # Configuración 4: pymssql como alternativa (más compatible)
            "PYMSSQL_NATIVE"
        ]
        
        for i, connection_string in enumerate(connection_configs, 1):
            try:
                self.logger.info(f"Intentando configuración {i} de conexión...")
                
                # Configuración especial para pymssql
                if connection_string == "PYMSSQL_NATIVE":
                    self.logger.info("Usando pymssql...")
                    return pymssql.connect(
                        server=self.sqlserver_config['host'],
                        port=int(self.sqlserver_config['port']),
                        user=self.sqlserver_config['username'],
                        password=self.sqlserver_config['password'],
                        database=self.sqlserver_config['database'],
                        timeout=15
                    )
                else:
                    # Configuraciones ODBC
                    self.logger.debug(f"Cadena de conexión: {connection_string.replace(self.sqlserver_config['password'], '***')}")
                    return pyodbc.connect(connection_string, timeout=15)
                    
            except Exception as e:
                self.logger.warning(f"Configuración {i} falló: {str(e)}")
                if i == len(connection_configs):
                    raise e
                continue
    
    def connect_mariadb(self):
        """Conectar a MariaDB"""
        return mysql.connector.connect(
            host=self.mariadb_config['host'],
            port=self.mariadb_config['port'],
            database=self.mariadb_config['database'],
            user=self.mariadb_config['username'],
            password=self.mariadb_config['password'],
            charset='utf8mb4'
        )
    
    def get_table_structure(self, table_name, connection_type='sqlserver'):
        """Obtener la estructura de una tabla"""
        if connection_type == 'sqlserver':
            conn = self.connect_sqlserver()
            query = f"""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
            """
        else:  # mariadb
            conn = self.connect_mariadb()
            query = f"""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}' AND TABLE_SCHEMA = '{self.mariadb_config['database']}'
            ORDER BY ORDINAL_POSITION
            """
        
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    
    def map_sql_type_to_mysql(self, sql_type, column_length=None):
        """Mapear tipos de SQL Server a MySQL/MariaDB con optimizaciones"""
        sql_type = sql_type.upper()
        
        # Manejar tipos de cadena con longitud
        if 'VARCHAR' in sql_type or 'NVARCHAR' in sql_type:
            if column_length and column_length > 16383:  # Límite para optimizar
                return 'TEXT'
            elif column_length:
                return f'VARCHAR({min(column_length, 16383)})'
            else:
                return 'TEXT'
        
        if 'CHAR' in sql_type and 'VARCHAR' not in sql_type:
            if column_length and column_length > 255:
                return 'TEXT'
            elif column_length:
                return f'CHAR({min(column_length, 255)})'
            else:
                return 'CHAR(255)'
        
        # Mapeo de tipos específicos
        type_mapping = {
            'INT': 'INT',
            'INTEGER': 'INT',
            'BIGINT': 'BIGINT',
            'SMALLINT': 'SMALLINT',
            'TINYINT': 'TINYINT',
            'BIT': 'BOOLEAN',
            'DECIMAL': 'DECIMAL',
            'NUMERIC': 'DECIMAL',
            'FLOAT': 'FLOAT',
            'REAL': 'FLOAT',
            'MONEY': 'DECIMAL(19,4)',
            'SMALLMONEY': 'DECIMAL(10,4)',
            'DATETIME': 'DATETIME',
            'DATETIME2': 'DATETIME',
            'SMALLDATETIME': 'DATETIME',
            'DATE': 'DATE',
            'TIME': 'TIME',
            'TIMESTAMP': 'TIMESTAMP',
            'TEXT': 'LONGTEXT',
            'NTEXT': 'LONGTEXT',
            'IMAGE': 'LONGBLOB',
            'BINARY': 'BLOB',
            'VARBINARY': 'BLOB',
            'UNIQUEIDENTIFIER': 'VARCHAR(36)',
            'XML': 'LONGTEXT'
        }
        
        return type_mapping.get(sql_type, 'TEXT')
    
    def clean_dataframe(self, df):
        """Limpiar DataFrame antes de insertar"""
        # Reemplazar valores NaN/None con None para MySQL
        df = df.where(pd.notnull(df), None)
        
        # Convertir tipos problemáticos
        for col in df.columns:
            if df[col].dtype == 'object':
                # Convertir a string y limpiar
                df[col] = df[col].astype(str)
                df[col] = df[col].replace('nan', None)
                df[col] = df[col].replace('None', None)
                df[col] = df[col].replace('', None)
                
            # Convertir valores booleanos problemáticos
            if df[col].dtype == 'bool' or col.upper() in ['PUBLICA', 'ACTIVO', 'HABILITADO', 'ESTADO', 'FLAG']:
                df[col] = df[col].astype(str)
                df[col] = df[col].replace('True', '1')
                df[col] = df[col].replace('False', '0')
                df[col] = df[col].replace('nan', None)
                df[col] = df[col].replace('None', None)
                
        return df
    
    def clean_column_name(self, column_name):
        """Limpiar nombre de columna para máxima compatibilidad"""
        # Reemplazar espacios con guiones bajos
        clean_name = column_name.replace(' ', '_')
        
        # Reemplazar caracteres especiales con guiones bajos
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', clean_name)
        
        # Eliminar caracteres acentuados
        clean_name = clean_name.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        clean_name = clean_name.replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
        clean_name = clean_name.replace('ñ', 'n').replace('Ñ', 'N')
        
        # Eliminar guiones bajos múltiples
        clean_name = re.sub(r'_+', '_', clean_name)
        
        # Eliminar guiones bajos al inicio y final
        clean_name = clean_name.strip('_')
        
        # Convertir a minúsculas para máxima compatibilidad
        clean_name = clean_name.lower()
        
        self.logger.debug(f"Limpiando nombre de columna: '{column_name}' -> '{clean_name}'")
        
        return clean_name

    def get_optimized_table_structure(self, table_name):
        """Obtener estructura optimizada de tabla desde SQL Server"""
        try:
            conn = self.connect_sqlserver()
            cursor = conn.cursor()
            
            # Obtener estructura completa
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Limpiar nombres de columnas
            cleaned_columns = []
            for col in columns:
                cleaned_col = list(col)  # Convertir a lista para poder modificar
                cleaned_col[0] = self.clean_column_name(col[0])  # Limpiar nombre de columna
                cleaned_columns.append(cleaned_col)
            
            return cleaned_columns
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estructura de tabla '{table_name}': {str(e)}")
            return None
    
    def drop_and_recreate_table(self, table_name):
        """Eliminar y recrear tabla para máxima compatibilidad"""
        try:
            # Eliminar tabla si existe
            mariadb_conn = self.connect_mariadb()
            cursor = mariadb_conn.cursor()
            
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            mariadb_conn.commit()
            self.logger.info(f"Tabla '{table_name}' eliminada (si existía)")
            
            cursor.close()
            mariadb_conn.close()
            
            # Crear tabla nueva
            self.create_table_if_not_exists(table_name)
            
        except Exception as e:
            self.logger.error(f"Error eliminando tabla '{table_name}': {str(e)}")
            raise

    def create_table_if_not_exists(self, table_name):
        """Crear tabla en MariaDB si no existe, con optimizaciones"""
        try:
            # Verificar si la tabla ya existe
            mariadb_conn = self.connect_mariadb()
            cursor = mariadb_conn.cursor()
            
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            if cursor.fetchone():
                cursor.close()
                mariadb_conn.close()
                self.logger.info(f"Tabla '{table_name}' ya existe en MariaDB")
                return
            
            # Obtener estructura optimizada de SQL Server
            sqlserver_conn = self.connect_sqlserver()
            cursor_sql = sqlserver_conn.cursor()
            
            # Obtener estructura completa
            cursor_sql.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
            """)
            
            columns = cursor_sql.fetchall()
            cursor_sql.close()
            sqlserver_conn.close()
            
            if not columns:
                raise Exception(f"No se pudo obtener la estructura de la tabla '{table_name}'")
            
            # Construir definición de columnas
            column_defs = []
            for col in columns:
                col_name = self.clean_column_name(col[0])
                data_type = col[1].upper()
                length = col[2]
                precision = col[3]
                scale = col[4]
                is_nullable = col[5]
                default = col[6]
                
                # Mapear tipos de datos
                if data_type in ['VARCHAR', 'NVARCHAR', 'CHAR', 'NCHAR']:
                    length = min(length or 255, 255)  # Limitar a 255 caracteres
                    col_type = f"VARCHAR({length})"
                elif data_type in ['TEXT', 'NTEXT']:
                    col_type = "TEXT"
                elif data_type == 'DECIMAL':
                    precision = min(precision or 10, 10)  # Limitar precisión
                    scale = min(scale or 2, 2)  # Limitar escala
                    col_type = f"DECIMAL({precision},{scale})"
                elif data_type == 'FLOAT':
                    col_type = "FLOAT"
                elif data_type == 'DATETIME':
                    col_type = "DATETIME"
                elif data_type == 'DATE':
                    col_type = "DATE"
                elif data_type == 'BIT':
                    col_type = "TINYINT(1)"
                elif data_type == 'INT':
                    col_type = "INT"
                elif data_type == 'BIGINT':
                    col_type = "BIGINT"
                else:
                    col_type = "VARCHAR(255)"  # Tipo por defecto
                
                # Construir definición de columna
                col_def = f"`{col_name}` {col_type}"
                if is_nullable == 'NO':
                    col_def += " NOT NULL"
                if default is not None:
                    if default == '':
                        col_def += " DEFAULT ''"
                    elif default.upper() == 'NULL':
                        col_def += " DEFAULT NULL"
                    else:
                        col_def += f" DEFAULT {default}"
                
                column_defs.append(col_def)
            
            # Crear tabla
            create_table_sql = f"CREATE TABLE `{table_name}` (\n  " + ",\n  ".join(column_defs) + "\n)"
            self.logger.debug(f"SQL para crear tabla:\n{create_table_sql}")
            
            cursor.execute(create_table_sql)
            mariadb_conn.commit()
            
            cursor.close()
            mariadb_conn.close()
            
            self.logger.info(f"Tabla '{table_name}' creada/verificada en MariaDB")
            
        except Exception as e:
            self.logger.error(f"Error creando tabla '{table_name}': {str(e)}")
            raise
    
    def validate_table_exists(self, table_name):
        """Validar si la tabla existe en SQL Server"""
        try:
            conn = self.connect_sqlserver()
            cursor = conn.cursor()
            
            # Query para verificar si la tabla existe
            query = "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '%s'" % table_name
            cursor.execute(query)
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return result[0] > 0
            
        except Exception as e:
            self.logger.error(f"Error validando tabla '{table_name}': {str(e)}")
            return False

    def get_table_row_count(self, table_name):
        """Obtener número de registros de una tabla"""
        try:
            conn = self.connect_sqlserver()
            cursor = conn.cursor()
            
            query = f"SELECT COUNT(*) FROM [{table_name}]"
            cursor.execute(query)
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            self.logger.error(f"Error contando registros en '{table_name}': {str(e)}")
            return 0

    def sync_table(self, table_name):
        """Sincronizar una tabla específica con mejoras"""
        try:
            self.logger.info(f"Iniciando sincronización de tabla: {table_name}")
            
            # Validar que la tabla existe
            if not self.validate_table_exists(table_name):
                self.logger.warning(f"⚠️ Tabla '{table_name}' no existe en SQL Server - OMITIDA")
                return
            
            # Verificar si tiene datos
            row_count = self.get_table_row_count(table_name)
            if row_count == 0:
                self.logger.info(f"ℹ️ Tabla '{table_name}' está vacía - OMITIDA")
                return
                
            self.logger.info(f"📊 Tabla '{table_name}' tiene {row_count} registros")
            
            # Mostrar estructura en SQL Server
            sqlserver_conn = self.connect_sqlserver()
            cursor = sqlserver_conn.cursor()
            cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' ORDER BY ORDINAL_POSITION")
            columns = cursor.fetchall()
            self.logger.info(f"Estructura en SQL Server para '{table_name}':")
            for col in columns:
                self.logger.info(f"  - {col[0]} ({col[1]}{', ' + str(col[2]) if col[2] else ''})")
            cursor.close()
            sqlserver_conn.close()
            
            # Eliminar y recrear tabla para máxima compatibilidad
            self.drop_and_recreate_table(table_name)
            
            # Mostrar estructura en MariaDB
            mariadb_conn = self.connect_mariadb()
            cursor = mariadb_conn.cursor()
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()
            self.logger.info(f"Estructura en MariaDB para '{table_name}':")
            for col in columns:
                self.logger.info(f"  - {col[0]} ({col[1]})")
            cursor.close()
            mariadb_conn.close()
            
            # Leer datos de SQL Server
            sqlserver_conn = self.connect_sqlserver()
            
            # Obtener nombres de columnas originales y limpios
            cursor = sqlserver_conn.cursor()
            cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' ORDER BY ORDINAL_POSITION")
            original_columns = [row[0] for row in cursor.fetchall()]
            clean_columns = [self.clean_column_name(col) for col in original_columns]
            cursor.close()
            
            # Construir query SELECT con nombres originales y alias limpios
            select_parts = []
            for orig, clean in zip(original_columns, clean_columns):
                select_parts.append(f'[{orig}] AS [{clean}]')
            columns_str = ', '.join(select_parts)
            query = f"SELECT {columns_str} FROM [{table_name}]"
            
            self.logger.info(f"Query SELECT: {query}")
            
            # Leer datos usando pandas
            df = pd.read_sql(query, sqlserver_conn)
            sqlserver_conn.close()
            
            total_rows = len(df)
            self.logger.info(f"Leyendo {total_rows} registros de SQL Server")
            
            # Verificar que los nombres de columnas en el DataFrame coinciden con los nombres limpios
            df_columns = list(df.columns)
            self.logger.info("Columnas en DataFrame:")
            for col in df_columns:
                self.logger.info(f"  - {col}")
            
            # Verificar que los nombres limpios coinciden con las columnas en MariaDB
            mariadb_conn = self.connect_mariadb()
            cursor = mariadb_conn.cursor()
            cursor.execute(f"DESCRIBE `{table_name}`")
            mariadb_columns = [col[0] for col in cursor.fetchall()]
            cursor.close()
            mariadb_conn.close()
            
            self.logger.info("Columnas en MariaDB:")
            for col in mariadb_columns:
                self.logger.info(f"  - {col}")
            
            # Verificar que todas las columnas limpias existen en MariaDB
            missing_columns = [col for col in clean_columns if col not in mariadb_columns]
            if missing_columns:
                raise Exception(f"Las siguientes columnas no existen en MariaDB: {missing_columns}")
            
            # Verificar que todas las columnas de MariaDB existen en las columnas limpias
            extra_columns = [col for col in mariadb_columns if col not in clean_columns]
            if extra_columns:
                self.logger.warning(f"Las siguientes columnas existen en MariaDB pero no en SQL Server: {extra_columns}")
            
            # Insertar datos en MariaDB
            mariadb_conn = self.connect_mariadb()
            cursor = mariadb_conn.cursor()
            
            # Construir query de inserción con nombres de columnas limpios
            columns_str = ', '.join([f'`{col}`' for col in clean_columns])
            placeholders = ', '.join(['%s'] * len(clean_columns))
            insert_query = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"
            
            self.logger.info(f"Query de inserción: {insert_query}")
            
            # Convertir DataFrame a lista de tuplas, manejando valores especiales
            data = []
            for row in df.values:
                clean_row = []
                for value in row:
                    if pd.isna(value) or value is None or str(value).lower() == 'nan':
                        clean_row.append(None)
                    elif isinstance(value, bool) or str(value).lower() == 'true':
                        clean_row.append(1)
                    elif str(value).lower() == 'false':
                        clean_row.append(0)
                    else:
                        clean_row.append(value)
                data.append(tuple(clean_row))
            
            # Insertar en lotes de 1000
            batch_size = 1000
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                cursor.executemany(insert_query, batch)
                mariadb_conn.commit()
                self.logger.info(f"Insertados {min(i + batch_size, total_rows)}/{total_rows} registros")
            
            cursor.close()
            mariadb_conn.close()
            
            self.logger.info(f"✓ Sincronización de tabla '{table_name}' completada: {total_rows} registros")
            
        except Exception as e:
            self.logger.error(f"✗ Error sincronizando tabla '{table_name}': {str(e)}")
            self.logger.error(f"Traceback:\n{traceback.format_exc()}")
            self.logger.error(f"Fallo en tabla '{table_name}': {str(e)}")
            raise
    
    def sync_all_tables(self):
        """Sincronizar todas las tablas configuradas"""
        start_time = datetime.now()
        self.logger.info("=== INICIANDO SINCRONIZACIÓN COMPLETA ===")
        
        success_count = 0
        error_count = 0
        
        for table_name in self.tables_to_sync:
            table_name = table_name.strip()
            if not table_name:
                continue
                
            try:
                self.sync_table(table_name)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.logger.error(f"Fallo en tabla '{table_name}': {str(e)}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.logger.info("=== SINCRONIZACIÓN COMPLETADA ===")
        self.logger.info(f"Tablas exitosas: {success_count}")
        self.logger.info(f"Tablas con errores: {error_count}")
        self.logger.info(f"Duración total: {duration}")
        
        return error_count == 0
    
    def cleanup_old_logs(self):
        """Limpiar logs antiguos"""
        try:
            retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', 7))
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for filename in os.listdir('.'):
                if filename.startswith('sync_log_') and filename.endswith('.log'):
                    try:
                        # Extraer fecha del nombre del archivo
                        date_str = filename.replace('sync_log_', '').replace('.log', '')
                        file_date = datetime.strptime(date_str, '%Y%m')
                        
                        if file_date < cutoff_date:
                            os.remove(filename)
                            self.logger.info(f"Log antiguo eliminado: {filename}")
                    except:
                        continue  # Ignorar archivos con formato incorrecto
                        
        except Exception as e:
            self.logger.warning(f"Error limpiando logs antiguos: {str(e)}")
    
    def run_scheduled_sync(self):
        """Ejecutar sincronización programada"""
        self.logger.info("Ejecutando sincronización programada...")
        
        # Probar conexiones antes de sincronizar
        if not self.test_connections():
            self.logger.error("Error en las conexiones. Sincronización cancelada.")
            return
        
        # Ejecutar sincronización
        success = self.sync_all_tables()
        
        # Limpiar logs antiguos
        self.cleanup_old_logs()
        
        if success:
            self.logger.info("🎉 Sincronización programada completada exitosamente")
        else:
            self.logger.error("⚠️ Sincronización completada con errores")
    
    def start_scheduler(self):
        """Iniciar el programador de tareas"""
        self.logger.info(f"Programando sincronización diaria a las {self.sync_time}")
        
        # Programar tarea diaria
        schedule.every().day.at(self.sync_time).do(self.run_scheduled_sync)
        
        self.logger.info("Programador iniciado. Presiona Ctrl+C para detener.")
        self.logger.info(f"Próxima ejecución: {schedule.next_run()}")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
        except KeyboardInterrupt:
            self.logger.info("Programador detenido por el usuario")

def main():
    """Función principal"""
    syncronizer = DatabaseSyncronizer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            # Probar conexiones
            if syncronizer.test_connections():
                print("✓ Todas las conexiones están funcionando correctamente")
                sys.exit(0)
            else:
                print("✗ Error en las conexiones")
                sys.exit(1)
                
        elif command == 'sync':
            # Ejecutar sincronización manual
            success = syncronizer.sync_all_tables()
            sys.exit(0 if success else 1)
            
        elif command == 'schedule':
            # Iniciar programador
            syncronizer.start_scheduler()
            
        else:
            print("Comandos disponibles:")
            print("  test     - Probar conexiones")
            print("  sync     - Ejecutar sincronización manual")
            print("  schedule - Iniciar programador automático")
            sys.exit(1)
    else:
        # Por defecto, mostrar ayuda
        print("Sincronizador de Base de Datos: SQL Server -> MariaDB")
        print("\nUso: python db_sync.py [comando]")
        print("\nComandos disponibles:")
        print("  test     - Probar conexiones a ambas bases de datos")
        print("  sync     - Ejecutar sincronización manual inmediata")
        print("  schedule - Iniciar el programador automático")
        print("\nEjemplos:")
        print("  python db_sync.py test")
        print("  python db_sync.py sync")
        print("  python db_sync.py schedule")

if __name__ == "__main__":
    main() 