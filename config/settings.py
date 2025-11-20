"""
Configuración centralizada del proyecto.

Este módulo carga y expone todas las variables de configuración necesarias
para la aplicación, incluyendo conexión a base de datos, comercios permitidos
y autenticación API.
"""
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 5433)),
    'database': os.environ.get('DB_DATABASE', 'productos_sepa'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'postgres')
}

COMERCIOS_PERMITIDOS = [9, 12, 15, 10]

api_key_raw = os.environ.get('API_KEY')
API_KEY = api_key_raw.strip("'\"") if api_key_raw else None
