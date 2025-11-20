#!/usr/bin/env python
"""
Script para descargar el archivo ZIP del SEPA según el día de la semana.

Este script detecta el día actual (en hora Argentina GMT-3) y descarga
el archivo correspondiente desde el portal de datos de producción.
El archivo se guarda como 'sepa_data.zip' en la carpeta 'data/' o en la raíz.
"""
import sys
import os
import requests
from datetime import datetime
import pytz

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# URLs de descarga según el día de la semana
URLS_SEPA = {
    0: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/f8e75128-515a-436e-bf8d-5c63a62f2005/download/sepa_domingo.zip',  # Domingo
    1: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/9dc06241-cc83-44f4-8e25-c9b1636b8bc8/download/sepa_martes.zip',  # Lunes
    2: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/9dc06241-cc83-44f4-8e25-c9b1636b8bc8/download/sepa_martes.zip',  # Martes
    3: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/1e92cd42-4f94-4071-a165-62c4cb2ce23c/download/sepa_miercoles.zip',  # Miércoles
    4: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/d076720f-a7f0-4af8-b1d6-1b99d5a90c14/download/sepa_jueves.zip',  # Jueves
    5: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/91bc072a-4726-44a1-85ec-4a8467aad27e/download/sepa_viernes.zip',  # Viernes
    6: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/b3c3da5d-213d-41e7-8d74-f23fda0a3c30/download/sepa_sabado.zip',  # Sábado
}

NOMBRES_DIAS = {
    0: 'Domingo',
    1: 'Lunes',
    2: 'Martes',
    3: 'Miércoles',
    4: 'Jueves',
    5: 'Viernes',
    6: 'Sábado'
}


def obtener_dia_argentina():
    """
    Obtiene el día de la semana actual en hora Argentina (GMT-3).

    Returns:
        int: Día de la semana (0=Domingo, 1=Lunes, ..., 6=Sábado)
    """
    tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
    fecha_argentina = datetime.now(tz_argentina)
    return fecha_argentina.weekday()


def obtener_ruta_destino():
    """
    Determina la ruta donde guardar el archivo descargado.

    Prioriza la carpeta 'data/' si existe, sino usa la raíz del proyecto.

    Returns:
        str: Ruta completa donde guardar el archivo.
    """
    proyecto_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    carpeta_data = os.path.join(proyecto_root, 'data')
    
    if os.path.exists(carpeta_data):
        return os.path.join(carpeta_data, 'sepa_data.zip')
    else:
        return os.path.join(proyecto_root, 'sepa_data.zip')


def eliminar_archivo_viejo(ruta_archivo):
    """
    Elimina el archivo anterior si existe.

    Args:
        ruta_archivo (str): Ruta del archivo a eliminar.
    """
    if os.path.exists(ruta_archivo):
        try:
            os.remove(ruta_archivo)
            print(f"[INFO] Archivo anterior eliminado: {ruta_archivo}")
        except Exception as e:
            print(f"[ERROR] No se pudo eliminar el archivo anterior: {e}")


def descargar_archivo_sepa():
    """
    Descarga el archivo ZIP del SEPA según el día de la semana actual.

    El archivo se guarda como 'sepa_data.zip' en la carpeta 'data/' o en la raíz.
    Antes de descargar, elimina el archivo anterior si existe.

    Returns:
        bool: True si la descarga fue exitosa, False en caso contrario.
    """
    dia_semana = obtener_dia_argentina()
    nombre_dia = NOMBRES_DIAS[dia_semana]
    url = URLS_SEPA.get(dia_semana)
    
    if not url:
        print(f"[ERROR] No hay URL configurada para el día {nombre_dia}")
        return False
    
    ruta_destino = obtener_ruta_destino()
    
    print(f"[INFO] Día de la semana: {nombre_dia}")
    print(f"[INFO] URL de descarga: {url}")
    print(f"[INFO] Destino: {ruta_destino}")
    
    # Eliminar archivo anterior
    eliminar_archivo_viejo(ruta_destino)
    
    try:
        print(f"[INFO] Iniciando descarga...")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Obtener tamaño del archivo si está disponible
        tamaño_total = int(response.headers.get('content-length', 0))
        tamaño_mb = tamaño_total / (1024 * 1024) if tamaño_total > 0 else 0
        
        print(f"[INFO] Tamaño del archivo: {tamaño_mb:.2f} MB")
        
        # Descargar archivo en chunks
        descargado = 0
        chunk_size = 8192
        
        with open(ruta_destino, 'wb') as archivo:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    archivo.write(chunk)
                    descargado += len(chunk)
                    
                    # Mostrar progreso cada 10MB
                    if tamaño_total > 0 and descargado % (10 * 1024 * 1024) < chunk_size:
                        progreso = (descargado / tamaño_total) * 100
                        print(f"[INFO] Progreso: {progreso:.1f}% ({descargado / (1024 * 1024):.2f} MB)")
        
        tamaño_final = os.path.getsize(ruta_destino) / (1024 * 1024)
        print(f"[INFO] Descarga completada exitosamente: {tamaño_final:.2f} MB")
        print(f"[INFO] Archivo guardado en: {ruta_destino}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error al descargar el archivo: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        return False


def main():
    """
    Función principal del script de descarga.
    """
    print("=" * 70)
    print("Descargador de archivos SEPA")
    print("=" * 70)
    
    exito = descargar_archivo_sepa()
    
    if exito:
        print("\n[SUCCESS] Descarga completada exitosamente")
        sys.exit(0)
    else:
        print("\n[ERROR] La descarga falló")
        sys.exit(1)


if __name__ == '__main__':
    main()

