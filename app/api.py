"""
API REST para búsqueda de productos SEPA.

Este módulo expone endpoints HTTP para consultar información de productos
del Sistema de Precios de Argentina (SEPA) mediante código de barras.
"""
import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, Blueprint, jsonify, request
from flask_cors import CORS
from functools import wraps
from app.models import BuscadorProductos
from config import API_KEY

app = Flask(__name__)
CORS(app)

# Crear Blueprint con prefijo /api/v1
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

buscador = BuscadorProductos()


def requiere_api_key(f):
    """Decorador para proteger endpoints con autenticación por API Key.

    Valida que las solicitudes incluyan un token Bearer válido en el header
    Authorization. Si el token no es válido o no se proporciona, retorna
    un error HTTP apropiado.

    Args:
        f: Función del endpoint a proteger.

    Returns:
        function: Decorador que valida la API key antes de ejecutar el endpoint.

    Raises:
        HTTP 401: Si no se proporciona token o el formato es inválido.
        HTTP 403: Si el token proporcionado no coincide con la API key configurada.
    """
    @wraps(f)
    def decorador(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': 'No se proporcionó token de autenticación',
                'mensaje': 'Se requiere header Authorization con Bearer token'
            }), 401
        
        try:
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        except IndexError:
            return jsonify({
                'error': 'Formato de token inválido',
                'mensaje': 'Formato esperado: Bearer <token>'
            }), 401
        
        if token != API_KEY:
            return jsonify({
                'error': 'Token inválido',
                'mensaje': 'La API key proporcionada no es válida'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorador


@api_v1.route('/producto/<codigo_barras>', methods=['GET'])
@requiere_api_key
def buscar_producto(codigo_barras):
    """Busca un producto por código de barras y retorna información de comercios.

    Args:
        codigo_barras (str): Código de barras del producto a buscar.

    Returns:
        tuple: Tupla con (JSON response, status_code).
            - 200: Producto encontrado exitosamente.
            - 404: Producto no encontrado en la base de datos.
            - 500: Error interno del servidor.

    Example:
        Respuesta exitosa (200):
        {
            "id_producto": "7795735000328",
            "nombre_producto": "Producto ejemplo",
            "marca_producto": "Marca ejemplo",
            "comercios": [
                {
                    "id_comercio": "9",
                    "id_bandera": "1",
                    "nombre_comercio": "Vea",
                    "precio_producto": "$1200"
                }
            ]
        }
    """
    try:
        resultados = buscador.buscar_por_codigo_barras(codigo_barras)
        
        if not resultados:
            return jsonify({
                'error': 'Producto no encontrado',
                'id_producto': codigo_barras
            }), 404
        
        primer_resultado = resultados[0]
        comercios = []
        
        for resultado in resultados:
            nombre_comercio = resultado['comercio_nombre']
            
            if resultado['id_comercio'] == 10:
                if nombre_comercio in ("Express", "Market"):
                    nombre_comercio = f"Carrefour {nombre_comercio}"
            
            comercios.append({
                'id_comercio': str(resultado['id_comercio']),
                'id_bandera': str(resultado['id_bandera']),
                'nombre_comercio': nombre_comercio,
                'precio_producto': f"${resultado['precio_lista']:.0f}"
            })
        
        respuesta = {
            'id_producto': primer_resultado['codigo_barras'],
            'nombre_producto': primer_resultado['descripcion'],
            'marca_producto': primer_resultado['marca'] or '',
            'comercios': comercios
        }
        
        return jsonify(respuesta), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Error al buscar producto',
            'mensaje': str(e)
        }), 500


@api_v1.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificación de salud del servicio.

    Returns:
        tuple: Tupla con (JSON response, status_code 200).
            {"status": "ok"}
    """
    return jsonify({'status': 'ok'}), 200


# Registrar el Blueprint en la aplicación
app.register_blueprint(api_v1)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Iniciando servidor API en http://{host}:{port}")
    print(f"Endpoint: GET http://{host}:{port}/api/v1/producto/<codigo_barras>")
    print(f"Health check: GET http://{host}:{port}/api/v1/health")
    
    app.run(host=host, port=port, debug=debug)
