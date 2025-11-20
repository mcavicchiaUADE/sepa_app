"""
Servicio de importación de datos desde archivos ZIP del SEPA.

Este módulo proporciona funciones para procesar archivos ZIP del Sistema de
Precios de Argentina (SEPA), extraer información de comercios y productos,
y cargarla eficientemente en una base de datos PostgreSQL usando operaciones
de carga masiva (COPY).
"""
import psycopg2
from psycopg2 import sql
import csv
import os
import zipfile
import tempfile
import re
import shutil
from config import DB_CONFIG, COMERCIOS_PERMITIDOS


def conectar_postgresql():
    """Establece conexión con la base de datos PostgreSQL.

    Returns:
        psycopg2.connection: Conexión activa a PostgreSQL.

    Raises:
        psycopg2.Error: Si no se puede establecer la conexión.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"[DEBUG] Conexion a PostgreSQL establecida: {DB_CONFIG['database']}")
        return conn
    except psycopg2.Error as e:
        print(f"[ERROR] No se pudo conectar a PostgreSQL: {e}")
        raise


def crear_tablas(conn):
    """Crea las tablas necesarias en PostgreSQL si no existen.

    Crea tres tablas:
    - comercios: Información de comercios con clave primaria compuesta.
    - productos: Productos con foreign key a comercios.
    - productos_staging: Tabla temporal para carga masiva sin restricciones.

    Args:
        conn (psycopg2.connection): Conexión a PostgreSQL.

    Returns:
        psycopg2.connection: La misma conexión recibida.
    """
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comercios (
            id_comercio INTEGER,
            id_bandera INTEGER,
            comercio_razon_social TEXT,
            comercio_bandera_nombre TEXT,
            comercio_bandera_url TEXT,
            PRIMARY KEY (id_comercio, id_bandera)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            id_comercio INTEGER,
            id_bandera INTEGER,
            id_producto TEXT,
            productos_precio_lista NUMERIC(10,2),
            productos_descripcion TEXT,
            productos_marca TEXT,
            FOREIGN KEY (id_comercio, id_bandera) REFERENCES comercios(id_comercio, id_bandera)
        )
    ''')
    
    cursor.execute('''
        DROP TABLE IF EXISTS productos_staging CASCADE;
        CREATE TABLE productos_staging (
            id_comercio INTEGER,
            id_bandera INTEGER,
            id_producto TEXT,
            productos_precio_lista NUMERIC(10,2),
            productos_descripcion TEXT,
            productos_marca TEXT
        )
    ''')
    
    conn.commit()
    print("[DEBUG] Tablas creadas correctamente")
    return conn


def mover_datos_staging_a_final(conn):
    """Transfiere datos de la tabla staging a la tabla final eliminando duplicados.

    Utiliza DISTINCT ON para eliminar duplicados por (id_comercio, id_bandera, id_producto),
    manteniendo el registro con el precio más bajo cuando hay múltiples precios.

    Args:
        conn (psycopg2.connection): Conexión a PostgreSQL.

    Returns:
        int: Cantidad de filas insertadas en la tabla final.
    """
    print("[DEBUG] Moviendo datos de staging a tabla final...")
    cursor = conn.cursor()
    
    cursor.execute('SET session_replication_role = replica')
    
    cursor.execute('''
        INSERT INTO productos (id_comercio, id_bandera, id_producto, productos_precio_lista,
                              productos_descripcion, productos_marca)
        SELECT DISTINCT ON (id_comercio, id_bandera, id_producto)
            id_comercio, id_bandera, id_producto, productos_precio_lista,
            productos_descripcion, productos_marca
        FROM productos_staging
        ORDER BY id_comercio, id_bandera, id_producto, productos_precio_lista
    ''')
    
    filas_insertadas = cursor.rowcount
    
    cursor.execute('SET session_replication_role = DEFAULT')
    cursor.execute('TRUNCATE TABLE productos_staging')
    
    conn.commit()
    print(f"[DEBUG] {filas_insertadas} filas movidas de staging a tabla final")
    return filas_insertadas


def crear_indices_productos(conn):
    """Crea índices en la tabla productos para optimizar búsquedas.

    Crea dos índices:
    - idx_codigo_barras: En id_producto para búsquedas por código de barras.
    - idx_comercio_bandera: En (id_comercio, id_bandera) para optimizar JOINs.

    Args:
        conn (psycopg2.connection): Conexión a PostgreSQL.
    """
    print("[DEBUG] Creando indices en tabla productos...")
    cursor = conn.cursor()
    
    print("[DEBUG] Creando indice idx_codigo_barras...")
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_codigo_barras ON productos(id_producto)
    ''')
    
    print("[DEBUG] Creando indice idx_comercio_bandera...")
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_comercio_bandera ON productos(id_comercio, id_bandera)
    ''')
    
    conn.commit()
    print("[DEBUG] Indices creados correctamente")


def importar_comercios_desde_csv(conn, ruta_csv):
    """Importa datos de comercios desde un archivo CSV.

    Filtra automáticamente solo los comercios permitidos según COMERCIOS_PERMITIDOS.
    Utiliza INSERT ... ON CONFLICT para actualizar registros existentes.

    Args:
        conn (psycopg2.connection): Conexión a PostgreSQL.
        ruta_csv (str): Ruta al archivo CSV de comercios.

    Returns:
        int: Cantidad de comercios importados.
    """
    print(f"  [DEBUG] Iniciando importacion de comercios desde: {os.path.basename(ruta_csv)}")
    cursor = conn.cursor()
    contador = 0
    
    try:
        with open(ruta_csv, 'r', encoding='utf-8-sig') as archivo:
            lector = csv.DictReader(archivo, delimiter='|')
            print(f"  [DEBUG] Archivo CSV abierto, leyendo filas...")
            
            for fila in lector:
                if not fila.get('id_comercio') or fila.get('id_comercio').strip() == '':
                    continue
                
                try:
                    id_comercio = int(fila['id_comercio'])
                    
                    if id_comercio not in COMERCIOS_PERMITIDOS:
                        continue
                    
                    id_bandera = int(fila['id_bandera']) if fila.get('id_bandera') and fila.get('id_bandera').strip() else None
                    
                    if id_bandera is None:
                        continue
                    
                    cursor.execute('''
                        INSERT INTO comercios 
                        (id_comercio, id_bandera, comercio_razon_social, comercio_bandera_nombre, comercio_bandera_url)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id_comercio, id_bandera) 
                        DO UPDATE SET
                            comercio_razon_social = EXCLUDED.comercio_razon_social,
                            comercio_bandera_nombre = EXCLUDED.comercio_bandera_nombre,
                            comercio_bandera_url = EXCLUDED.comercio_bandera_url
                    ''', (
                        id_comercio,
                        id_bandera,
                        fila.get('comercio_razon_social', ''),
                        fila.get('comercio_bandera_nombre', ''),
                        fila.get('comercio_bandera_url', '')
                    ))
                    contador += 1
                except (ValueError, KeyError):
                    continue
        
        conn.commit()
        print(f"  [DEBUG] Comercios importados: {contador}")
        return contador
    except Exception as e:
        print(f"Error leyendo {ruta_csv}: {e}")
        return 0


def preparar_csv_para_copy(ruta_csv_original, ruta_csv_limpio):
    """Prepara un CSV limpio y validado para carga masiva con COPY.

    Valida y filtra los datos del CSV original, manteniendo solo filas válidas
    de comercios permitidos. Genera estadísticas de errores por tipo.

    Args:
        ruta_csv_original (str): Ruta al CSV original con todos los productos.
        ruta_csv_limpio (str): Ruta donde se guardará el CSV limpio.

    Returns:
        tuple: (filas_validas, errores) donde:
            - filas_validas (int): Cantidad de filas válidas procesadas.
            - errores (dict): Diccionario con contadores de errores por tipo.
    """
    print(f"  [DEBUG] Preparando CSV limpio para COPY...")
    
    total_filas = 0
    filas_validas = 0
    errores = {
        'sin_id_producto': 0,
        'id_comercio_no_permitido': 0,
        'sin_id_bandera': 0,
        'sin_precio': 0,
        'sin_descripcion': 0,
        'otros': 0
    }
    
    with open(ruta_csv_original, 'r', encoding='utf-8-sig') as archivo_entrada:
        lector = csv.DictReader(archivo_entrada, delimiter='|')
        
        columnas = lector.fieldnames
        if not columnas:
            print(f"  [ERROR] No se pudieron leer las columnas del CSV!")
            return 0, errores
        
        id_comercio_key = None
        for col in columnas:
            if 'id_comercio' in col.lower().replace(' ', '').replace('\ufeff', ''):
                id_comercio_key = col
                break
        
        if not id_comercio_key:
            print(f"  [ERROR] Columna 'id_comercio' no encontrada!")
            return 0, errores
        
        with open(ruta_csv_limpio, 'w', encoding='utf-8', newline='') as archivo_salida:
            escritor = csv.writer(archivo_salida, delimiter='|')
            
            escritor.writerow(['id_comercio', 'id_bandera', 'id_producto', 
                             'productos_precio_lista', 'productos_descripcion', 'productos_marca'])
            
            for fila in lector:
                total_filas += 1
                
                id_producto = fila.get('id_producto', '').strip() if fila.get('id_producto') else ''
                if not id_producto:
                    errores['sin_id_producto'] += 1
                    continue
                
                id_comercio_valor = fila.get(id_comercio_key, '').strip() if fila.get(id_comercio_key) else ''
                if not id_comercio_valor:
                    errores['otros'] += 1
                    continue
                
                try:
                    id_comercio = int(id_comercio_valor)
                except ValueError:
                    errores['otros'] += 1
                    continue
                
                if id_comercio not in COMERCIOS_PERMITIDOS:
                    errores['id_comercio_no_permitido'] += 1
                    continue
                
                id_bandera_str = fila.get('id_bandera', '').strip() if fila.get('id_bandera') else ''
                if not id_bandera_str:
                    errores['sin_id_bandera'] += 1
                    continue
                
                try:
                    id_bandera = int(id_bandera_str)
                except ValueError:
                    errores['sin_id_bandera'] += 1
                    continue
                
                precio_str = fila.get('productos_precio_lista', '').strip() if fila.get('productos_precio_lista') else ''
                if not precio_str:
                    errores['sin_precio'] += 1
                    continue
                
                try:
                    precio_lista = float(precio_str)
                except ValueError:
                    errores['sin_precio'] += 1
                    continue
                
                descripcion = fila.get('productos_descripcion', '').strip() if fila.get('productos_descripcion') else ''
                if not descripcion:
                    errores['sin_descripcion'] += 1
                    continue
                
                marca = fila.get('productos_marca', '').strip() if fila.get('productos_marca') else ''
                
                escritor.writerow([id_comercio, id_bandera, id_producto, precio_lista, descripcion, marca])
                filas_validas += 1
                
                if filas_validas % 100000 == 0:
                    print(f"  [DEBUG] Procesadas {filas_validas} filas válidas...")
    
    print(f"  [DEBUG] CSV preparado: {filas_validas} filas válidas de {total_filas} totales")
    return filas_validas, errores


def importar_productos_desde_csv(conn, ruta_csv):
    """Importa productos desde CSV usando COPY de PostgreSQL para carga masiva.

    Utiliza COPY para cargar datos directamente en la tabla staging, lo cual
    es significativamente más rápido que INSERT individuales.

    Args:
        conn (psycopg2.connection): Conexión a PostgreSQL.
        ruta_csv (str): Ruta al archivo CSV de productos.

    Returns:
        tuple: (filas_importadas, total_errores) donde:
            - filas_importadas (int): Cantidad de filas cargadas exitosamente.
            - total_errores (int): Total de filas rechazadas por validación.
    """
    print(f"  [DEBUG] Iniciando importacion de productos desde: {os.path.basename(ruta_csv)}")
    cursor = conn.cursor()
    
    temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
    temp_csv.close()
    
    try:
        filas_validas, errores = preparar_csv_para_copy(ruta_csv, temp_csv.name)
        
        if filas_validas == 0:
            print(f"  [DEBUG] No hay filas válidas para importar")
            os.unlink(temp_csv.name)
            total_errores = sum(errores.values())
            return 0, total_errores
        
        print(f"  [DEBUG] Cargando {filas_validas} filas a staging usando COPY...")
        with open(temp_csv.name, 'r', encoding='utf-8') as f:
            cursor.copy_expert(
                sql.SQL("COPY productos_staging (id_comercio, id_bandera, id_producto, productos_precio_lista, productos_descripcion, productos_marca) FROM STDIN WITH (FORMAT csv, DELIMITER '|', HEADER true, ENCODING 'utf8')"),
                f
            )
        
        conn.commit()
        print(f"  [DEBUG] {filas_validas} filas cargadas a staging")
        
        total_errores = sum(errores.values())
        return filas_validas, total_errores
        
    except Exception as e:
        print(f"  [ERROR] Error en importación: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return 0, 0
    finally:
        if os.path.exists(temp_csv.name):
            os.unlink(temp_csv.name)


def descomprimir_zip_principal(ruta_zip):
    """Descomprime el ZIP principal del SEPA y localiza la carpeta con fecha.

    El ZIP principal contiene una carpeta con formato YYYY-MM-DD que a su vez
    contiene múltiples ZIPs de comercios individuales.

    Args:
        ruta_zip (str): Ruta al archivo ZIP principal del SEPA.

    Returns:
        str: Ruta a la carpeta con formato fecha (YYYY-MM-DD) o None si hay error.
    """
    print(f"[DEBUG] Descomprimiendo {ruta_zip}...")
    
    temp_dir = tempfile.mkdtemp(prefix='sepa_import_')
    print(f"[DEBUG] Directorio temporal creado: {temp_dir}")
    
    try:
        tamaño_zip = os.path.getsize(ruta_zip)
        print(f"[DEBUG] Tamaño del ZIP principal: {tamaño_zip / (1024*1024):.2f} MB")
        
        with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
            total_archivos = len(zip_ref.namelist())
            print(f"[DEBUG] Total de archivos en ZIP: {total_archivos}")
            print(f"[DEBUG] Extrayendo archivos...")
            zip_ref.extractall(temp_dir)
            print(f"[DEBUG] Extraccion completada")
        
        print(f"[DEBUG] Buscando carpeta con formato fecha...")
        fecha_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path) and fecha_pattern.match(item):
                print(f"[DEBUG] Carpeta encontrada: {item}")
                return item_path
        
        print(f"[DEBUG] No se encontro carpeta con formato fecha, usando directorio temporal")
        return temp_dir
    except Exception as e:
        print(f"Error descomprimiendo ZIP principal: {e}")
        import traceback
        traceback.print_exc()
        return None


def procesar_zip_sepa(ruta_zip_principal='data/sepa_jueves.zip'):
    """Procesa el ZIP principal del SEPA e importa todos los datos.

    Ejecuta el proceso completo de importación en 5 fases:
    1. Creación/verificación de tablas y limpieza de datos existentes.
    2. Importación de comercios desde todos los ZIPs.
    3. Importación de productos a tabla staging usando COPY.
    4. Transferencia de datos de staging a tabla final eliminando duplicados.
    5. Creación de índices para optimizar búsquedas.

    Args:
        ruta_zip_principal (str, optional): Ruta al archivo ZIP principal.
            Defaults to 'data/sepa_jueves.zip'.
    """
    print("Iniciando importación de datos desde ZIP del SEPA...")
    print("="*70)
    
    if not os.path.exists(ruta_zip_principal):
        ruta_alternativa = os.path.basename(ruta_zip_principal)
        if os.path.exists(ruta_alternativa):
            ruta_zip_principal = ruta_alternativa
        else:
            print(f"Error: No se encontró el archivo {ruta_zip_principal}")
            return
    
    conn = conectar_postgresql()
    
    print("[FASE 1] Creando/Verificando tablas...")
    crear_tablas(conn)
    
    cursor = conn.cursor()
    print("[FASE 1] Limpiando tablas existentes...")
    cursor.execute('TRUNCATE TABLE productos CASCADE')
    cursor.execute('TRUNCATE TABLE comercios CASCADE')
    cursor.execute('TRUNCATE TABLE productos_staging')
    conn.commit()
    print("[FASE 1] Tablas limpiadas\n")
    
    carpeta_fecha = descomprimir_zip_principal(ruta_zip_principal)
    if not carpeta_fecha:
        print("Error: No se pudo descomprimir el ZIP principal")
        conn.close()
        return
    
    zips_comercios = []
    zips_omitidos = 0
    
    patron_comercio = re.compile(r'comercio-sepa-(\d+)')
    
    for item in os.listdir(carpeta_fecha):
        if item.endswith('.zip'):
            match = patron_comercio.search(item)
            if match:
                id_comercio_archivo = int(match.group(1))
                if id_comercio_archivo in COMERCIOS_PERMITIDOS:
                    zips_comercios.append(os.path.join(carpeta_fecha, item))
                else:
                    zips_omitidos += 1
            else:
                zips_omitidos += 1
    
    print(f"\nComercios permitidos: {COMERCIOS_PERMITIDOS}")
    print(f"Encontrados {len(zips_comercios)} archivos ZIP de comercios permitidos")
    if zips_omitidos > 0:
        print(f"Omitidos {zips_omitidos} ZIPs de otros comercios")
    print("Procesando ZIPs...\n")
    
    total_productos = 0
    total_errores = 0
    total_comercios = 0
    
    temp_extract_dir = tempfile.mkdtemp(prefix='sepa_extract_')
    
    print("[FASE 2] Importando comercios...")
    print("="*70)
    
    for i, zip_comercio in enumerate(zips_comercios, 1):
        print(f"\n[{i}/{len(zips_comercios)}] Procesando comercio: {os.path.basename(zip_comercio)}...")
        
        for item in os.listdir(temp_extract_dir):
            item_path = os.path.join(temp_extract_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        
        try:
            nombre_zip = os.path.basename(zip_comercio)
            with zipfile.ZipFile(zip_comercio, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            ruta_comercio_csv = None
            for root, dirs, files in os.walk(temp_extract_dir):
                for file in files:
                    if file == 'comercio.csv':
                        ruta_comercio_csv = os.path.join(root, file)
                        break
                if ruta_comercio_csv:
                    break
            
            if ruta_comercio_csv and os.path.exists(ruta_comercio_csv):
                importar_comercios_desde_csv(conn, ruta_comercio_csv)
                print(f"  OK - Comercio importado")
            else:
                print(f"  ADVERTENCIA - No se encontro comercio.csv")
        except Exception as e:
            print(f"  ERROR - {e}")
    
    conn.commit()
    print(f"\n[FASE 2] Comercios importados correctamente\n")
    
    print("[FASE 3] Importando productos (esta fase puede tardar varios minutos)...")
    print("="*70)
    
    for i, zip_comercio in enumerate(zips_comercios, 1):
        print(f"\n[{i}/{len(zips_comercios)}] Procesando productos: {os.path.basename(zip_comercio)}...")
        
        for item in os.listdir(temp_extract_dir):
            item_path = os.path.join(temp_extract_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        
        try:
            nombre_zip = os.path.basename(zip_comercio)
            with zipfile.ZipFile(zip_comercio, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            ruta_productos_csv = None
            for root, dirs, files in os.walk(temp_extract_dir):
                for file in files:
                    if file == 'productos.csv':
                        ruta_productos_csv = os.path.join(root, file)
                        break
                if ruta_productos_csv:
                    break
            
            if ruta_productos_csv and os.path.exists(ruta_productos_csv):
                productos, errores = importar_productos_desde_csv(conn, ruta_productos_csv)
                total_productos += productos
                total_errores += errores
                total_comercios += 1
                
                if productos > 0:
                    print(f"  OK - {productos} productos importados")
                else:
                    print(f"  ADVERTENCIA - Sin productos")
            else:
                print(f"  ADVERTENCIA - No se encontro productos.csv")
        except Exception as e:
            print(f"  ERROR - {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n[FASE 3] Productos cargados a staging\n")
    
    print("[FASE 4] Moviendo datos de staging a tabla final...")
    print("="*70)
    total_productos_final = mover_datos_staging_a_final(conn)
    print(f"[FASE 4] {total_productos_final} productos movidos a tabla final\n")
    
    print("[FASE 5] Creando indices en tabla productos...")
    print("="*70)
    crear_indices_productos(conn)
    print("[FASE 5] Indices creados\n")
    
    shutil.rmtree(temp_extract_dir)
    shutil.rmtree(os.path.dirname(carpeta_fecha))
    
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM productos')
    total_productos_db = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM comercios')
    total_comercios_db = cursor.fetchone()[0]
    
    print(f"\n{'='*60}")
    print(f"Importación completada:")
    print(f"  - ZIPs procesados: {total_comercios}")
    print(f"  - Comercios únicos (id_comercio, id_bandera): {total_comercios_db}")
    print(f"  - Productos totales: {total_productos_db}")
    if total_errores > 0:
        print(f"  - Errores: {total_errores}")
    print(f"{'='*60}")
    
    conn.close()
