"""
Modelo de búsqueda de productos en la base de datos.

Este módulo proporciona la clase BuscadorProductos para realizar consultas
optimizadas sobre la base de datos PostgreSQL que contiene información de
productos y comercios del SEPA.
"""
import psycopg2
from typing import List, Dict
from config import DB_CONFIG


class BuscadorProductos:
    """Clase para realizar búsquedas de productos en la base de datos PostgreSQL.
    
    Proporciona métodos optimizados para buscar productos por código de barras
    o por descripción, retornando información completa incluyendo precios
    en diferentes comercios.
    """
    
    def __init__(self):
        """Inicializa el buscador con conexión a PostgreSQL.
        
        La conexión se establece de forma lazy (al primer uso) para optimizar
        recursos y permitir reutilización de conexiones.
        """
        self.conn = None
    
    def _get_connection(self):
        """Obtiene o crea una conexión a PostgreSQL.
        
        Returns:
            psycopg2.connection: Conexión activa a la base de datos.
            
        Raises:
            psycopg2.Error: Si no se puede establecer la conexión.
        """
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(**DB_CONFIG)
        return self.conn
    
    def buscar_por_codigo_barras(self, codigo_barras: str) -> List[Dict]:
        """Busca un producto por código de barras en todos los comercios disponibles.

        Realiza una búsqueda optimizada usando JOIN y DISTINCT ON para eliminar
        duplicados por comercio/bandera, retornando el precio más bajo cuando
        hay múltiples precios para el mismo producto en el mismo comercio.

        Args:
            codigo_barras (str): Código de barras del producto (id_producto).

        Returns:
            List[Dict]: Lista de diccionarios con información del producto en cada comercio.
                Cada diccionario contiene:
                - codigo_barras (str): Código de barras del producto.
                - descripcion (str): Descripción del producto.
                - marca (str): Marca del producto (puede ser None).
                - precio_lista (float): Precio del producto en el comercio.
                - id_comercio (int): ID del comercio.
                - id_bandera (int): ID de la bandera del comercio.
                - comercio_nombre (str): Nombre del comercio.
                - comercio_url (str): URL del comercio (puede ser None).
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT ON (p.id_comercio, p.id_bandera)
                p.id_producto,
                p.productos_descripcion,
                p.productos_marca,
                p.productos_precio_lista,
                p.id_comercio,
                p.id_bandera,
                c.comercio_bandera_nombre,
                c.comercio_razon_social,
                c.comercio_bandera_url
            FROM productos p
            INNER JOIN comercios c ON p.id_comercio = c.id_comercio 
                                   AND p.id_bandera = c.id_bandera
            WHERE p.id_producto = %s
            ORDER BY p.id_comercio, p.id_bandera, p.productos_precio_lista ASC
        ''', (codigo_barras,))
        
        resultados = []
        for fila in cursor.fetchall():
            resultados.append({
                'codigo_barras': fila[0],
                'descripcion': fila[1],
                'marca': fila[2],
                'precio_lista': float(fila[3]),
                'id_comercio': fila[4],
                'id_bandera': fila[5],
                'comercio_nombre': fila[6] or fila[7],
                'comercio_url': fila[8]
            })
        
        return resultados
    
    def buscar_por_descripcion(self, termino: str, limite: int = 20) -> List[Dict]:
        """Busca productos por descripción usando búsqueda parcial (LIKE).

        Realiza una búsqueda por coincidencia parcial en la descripción del producto,
        agrupando resultados por producto y retornando estadísticas de precios
        (mínimo, máximo) y cantidad de comercios donde está disponible.

        Args:
            termino (str): Término de búsqueda para buscar en la descripción.
            limite (int, optional): Cantidad máxima de resultados a retornar.
                Defaults to 20.

        Returns:
            List[Dict]: Lista de productos encontrados con resumen de precios.
                Cada diccionario contiene:
                - codigo_barras (str): Código de barras del producto.
                - descripcion (str): Descripción del producto.
                - marca (str): Marca del producto (puede ser None).
                - precio_minimo (float): Precio más bajo encontrado.
                - precio_maximo (float): Precio más alto encontrado.
                - cantidad_comercios (int): Cantidad de comercios donde está disponible.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT
                id_producto,
                productos_descripcion,
                productos_marca,
                MIN(productos_precio_lista) as precio_minimo,
                MAX(productos_precio_lista) as precio_maximo,
                COUNT(*) as cantidad_comercios
            FROM productos
            WHERE productos_descripcion LIKE %s
            GROUP BY id_producto, productos_descripcion, productos_marca
            ORDER BY cantidad_comercios DESC
            LIMIT %s
        ''', (f'%{termino}%', limite))
        
        resultados = []
        for fila in cursor.fetchall():
            resultados.append({
                'codigo_barras': fila[0],
                'descripcion': fila[1],
                'marca': fila[2],
                'precio_minimo': float(fila[3]) if fila[3] else None,
                'precio_maximo': float(fila[4]) if fila[4] else None,
                'cantidad_comercios': fila[5]
            })
        
        return resultados
