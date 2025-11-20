# Guía de Despliegue en Render - Paso a Paso

Esta guía te llevará paso a paso para desplegar todo el sistema en Render.

## Prerrequisitos

1. ✅ Cuenta en Render (gratis): https://render.com
2. ✅ Repositorio en GitHub con todo el código
3. ✅ ~15 minutos para completar el despliegue

## Paso 1: Verificar Estructura

Asegúrate de que estos archivos existan en la raíz del repositorio:
- ✅ `render.yaml` (configuración de servicios Render)
- ✅ `Procfile` (configuración de la API)
- ✅ `requirements.txt` (dependencias Python)
- ✅ `runtime.txt` (versión de Python)
- ✅ `app/` (código de la aplicación)
- ✅ `config/` (configuración)
- ✅ `scripts/descargar_e_importar.py` (script para Cron Job)
- `app/api.py`
- `app/models/buscador.py`
- `app/services/importador.py`
- `config/settings.py`

## Paso 2: Crear Cuenta y Conectar Repositorio

1. Ve a https://render.com
2. Crea una cuenta (puedes usar GitHub para login rápido)
3. En el Dashboard, haz clic en "New +" → "Blueprint"
4. Conecta tu repositorio de GitHub
5. Selecciona el repositorio que contiene este proyecto

## Paso 3: Configurar Blueprint

Render detectará automáticamente el archivo `render.yaml` y creará los servicios:

1. **Web Service** - `api-productos-sepa`
2. **PostgreSQL Database** - `productos-sepa-db`
3. **Cron Job** - `actualizar-datos-sepa`

### 3.1. Revisar Configuración

Render mostrará una vista previa de los servicios. Verifica que:
- ✅ Web Service apunta a `gunicorn app.api:app`
- ✅ Cron Job apunta a `python scripts/descargar_e_importar.py`
- ✅ Schedule del Cron es `10 13 * * *` (13:10 UTC)

### 3.2. Aplicar Blueprint

Haz clic en "Apply" para crear todos los servicios.

## Paso 4: Configurar Variables de Entorno

### 4.1. Obtener Credenciales de PostgreSQL

1. Ve al servicio `productos-sepa-db` en el Dashboard
2. En la pestaña "Connect", copia:
   - **Internal Database URL** (para el Cron Job)
   - O las credenciales individuales:
     - Host
     - Port
     - Database
     - User
     - Password

### 4.2. Configurar Web Service

1. Ve al servicio `api-productos-sepa`
2. Pestaña "Environment"
3. Agrega/verifica estas variables:

```
DB_HOST=<host-de-postgresql>
DB_PORT=5432
DB_DATABASE=productos_sepa
DB_USER=<usuario-de-postgresql>
DB_PASSWORD=<contraseña-de-postgresql>
API_KEY=<genera-una-clave-segura>
HOST=0.0.0.0
FLASK_DEBUG=False
PORT=10000
```

**Generar API_KEY:**
```bash
# En tu terminal local
openssl rand -hex 32
```

O usa cualquier generador de claves seguras.

### 4.3. Verificar Cron Job

El Cron Job debería tener las variables de DB configuradas automáticamente desde el Blueprint. Verifica en:
1. Servicio `actualizar-datos-sepa`
2. Pestaña "Environment"
3. Deberían estar todas las variables `DB_*` configuradas

## Paso 5: Desplegar Servicios

### 5.1. Desplegar Web Service

1. Ve al servicio `api-productos-sepa`
2. Si no se desplegó automáticamente, haz clic en "Manual Deploy" → "Deploy latest commit"
3. Espera a que termine el build (puede tardar 2-5 minutos)
4. Verifica que el estado sea "Live"

### 5.2. Verificar PostgreSQL

1. Ve al servicio `productos-sepa-db`
2. Verifica que esté "Available"
3. Si está pausado, haz clic en "Resume"

### 5.3. Verificar Cron Job

1. Ve al servicio `actualizar-datos-sepa`
2. Verifica que esté configurado correctamente
3. Puedes hacer una ejecución manual desde "Runs" → "Run now" para probar

## Paso 6: Probar el Sistema

### 6.1. Probar API (Health Check)

```bash
curl https://api-productos-sepa.onrender.com/api/v1/health
```

Debería responder:
```json
{"status":"ok"}
```

### 6.2. Probar Búsqueda (requiere API_KEY)

```bash
curl -H "Authorization: Bearer TU_API_KEY" \
     https://api-productos-sepa.onrender.com/api/v1/producto/7795735000328
```

**Nota:** Si la base de datos está vacía, esto retornará 404. Primero necesitas ejecutar el Cron Job.

### 6.3. Ejecutar Cron Job Manualmente

1. Ve al servicio `actualizar-datos-sepa`
2. Pestaña "Runs"
3. Haz clic en "Run now"
4. Espera a que termine (puede tardar varios minutos)
5. Revisa los logs para ver el progreso

### 6.4. Verificar Datos Importados

Una vez que el Cron Job termine exitosamente, prueba la búsqueda nuevamente. Debería retornar datos.

## Paso 7: Configurar Actualización Automática

El Cron Job está configurado para ejecutarse automáticamente todos los días a las 10:10 hora Argentina (13:10 UTC).

### Verificar Schedule

1. Ve al servicio `actualizar-datos-sepa`
2. Verifica que el schedule sea: `10 13 * * *`
3. Esto significa: minuto 10, hora 13, todos los días, todos los meses, todos los días de la semana

### Ajustar Horario (si es necesario)

Si necesitas cambiar el horario, edita `render.yaml`:

```yaml
schedule: "10 13 * * *"  # Formato: minuto hora día mes día-semana
```

Ejemplos:
- `"0 10 * * *"` - Todos los días a las 10:00 UTC
- `"30 14 * * *"` - Todos los días a las 14:30 UTC
- `"0 13 * * 1-5"` - Lunes a Viernes a las 13:00 UTC

**Recordatorio:** Argentina está en UTC-3, así que:
- 10:10 Argentina = 13:10 UTC
- 11:10 Argentina = 14:10 UTC

## Monitoreo y Mantenimiento

### Ver Logs

**Web Service:**
- Dashboard → `api-productos-sepa` → "Logs"

**Cron Job:**
- Dashboard → `actualizar-datos-sepa` → "Logs"
- Dashboard → `actualizar-datos-sepa` → "Runs" (historial de ejecuciones)

### Verificar Estado de Servicios

Todos los servicios deberían estar en estado "Live" o "Available". Si alguno está pausado:
- PostgreSQL: Se pausa después de 90 días de inactividad (plan gratuito)
- Web Service: Se "duerme" después de 15 min de inactividad (plan gratuito)

### Actualizar Código

1. Haz commit y push a GitHub
2. Render detectará automáticamente los cambios
3. Reconstruirá y redesplegará los servicios

O manualmente:
- Dashboard → Servicio → "Manual Deploy" → "Deploy latest commit"

## Solución de Problemas Comunes

### Error: "Module not found"
- Verifica que `requirements.txt` tenga todas las dependencias
- Revisa los logs del build para ver qué falta

### Error: "Database connection failed"
- Verifica que PostgreSQL esté activo
- Verifica variables de entorno en ambos servicios
- Asegúrate de que el Cron Job tenga acceso a la DB

### Error: "API returns 404"
- Verifica que el Cron Job se haya ejecutado exitosamente
- Verifica que haya datos en la base de datos
- Revisa logs del Cron Job

### El Cron Job no se ejecuta
- Verifica el schedule en `render.yaml`
- Verifica que el servicio esté activo
- Revisa logs para ver errores

### La API está lenta
- Primera petición después de dormir puede tardar ~30 segundos (plan gratuito)
- Considera usar un plan de pago para mejor rendimiento

## URLs Finales

Una vez desplegado, tendrás:

- **API Base URL**: `https://api-productos-sepa.onrender.com`
- **Health Check**: `https://api-productos-sepa.onrender.com/api/v1/health`
- **Buscar Producto**: `https://api-productos-sepa.onrender.com/api/v1/producto/<codigo_barras>`

## Uso de la API

Para información detallada sobre cómo usar la API, consulta:
- **`USO_API.md`** - Guía completa con ejemplos en múltiples lenguajes
- Incluye ejemplos en: JavaScript, Python, Node.js, React, HTML
- Documentación de todos los endpoints y respuestas

## Costos

**Plan Gratuito:**
- ✅ Web Service: Gratis (se duerme después de 15 min)
- ✅ PostgreSQL: Gratis (se pausa después de 90 días)
- ✅ Cron Job: Gratis

**Limitaciones del Plan Gratuito:**
- ⚠️ Tiempo de "despertar" en primera petición
- ⚠️ PostgreSQL puede pausarse con inactividad
- ⚠️ Recursos limitados

Para producción, considera un plan de pago si necesitas:
- Sin tiempo de despertar
- Base de datos siempre activa
- Mayor rendimiento

## Siguiente Paso

Una vez desplegado, el sistema funcionará automáticamente:
- ✅ Descarga diaria a las 10:10 Argentina
- ✅ Importación automática a PostgreSQL
- ✅ API disponible 24/7 (con limitaciones del plan gratuito)

¡Listo! Tu sistema está desplegado y funcionando. 🎉

