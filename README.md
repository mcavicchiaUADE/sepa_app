# Despliegue en Render - Sistema SEPA

Esta carpeta contiene **TODO** lo necesario para desplegar el sistema completo en Render.

## 📁 Estructura

```
render-deploy/
├── README.md                    # Este archivo
├── DEPLOY.md                    # Guía paso a paso de despliegue
├── USO_API.md                   # Guía completa de uso de la API
├── render.yaml                  # Configuración de servicios Render
├── Procfile                     # Configuración para Render
├── requirements.txt             # Dependencias Python
├── runtime.txt                  # Versión de Python
├── app/                         # Código de la aplicación
│   ├── api.py                   # API REST Flask
│   ├── models/                  # Modelos de datos
│   └── services/                # Servicios (importador)
├── config/                      # Configuración
│   └── settings.py              # Configuración de BD y API
└── scripts/                      # Scripts
    ├── descargar_sepa.py        # Descarga de archivos SEPA
    └── descargar_e_importar.py  # Script combinado para Cron Job (descarga + importa)
```

## 🚀 Inicio Rápido

1. **Sube esta carpeta completa a un repositorio de GitHub**
2. **Conecta el repositorio a Render**
3. **Sigue las instrucciones en `DEPLOY.md`**

## 📋 Componentes del Sistema

### 1. Web Service (API REST)
- **Nombre**: `api-productos-sepa`
- **Función**: Expone la API REST para búsquedas de productos
- **Endpoint**: `https://api-productos-sepa.onrender.com/api/v1/`

### 2. PostgreSQL Database
- **Nombre**: `productos-sepa-db`
- **Función**: Almacena datos de productos y comercios
- **Plan**: Free

### 3. Cron Job (Actualización Diaria)
- **Nombre**: `actualizar-datos-sepa`
- **Función**: Descarga e importa datos SEPA automáticamente
- **Horario**: Todos los días a las 10:10 hora Argentina (13:10 UTC)

## 🔄 Flujo Completo

```
Cron Job (10:10 ARG / 13:10 UTC)
  ↓
1. Descarga archivo SEPA según día de semana
  ↓
2. Procesa ZIP y extrae datos
  ↓
3. Importa a PostgreSQL (comercios + productos)
  ↓
4. Limpia archivos temporales
  ↓
API disponible para búsquedas
```

## 📚 Documentación

- **`DEPLOY.md`** - Guía paso a paso completa de despliegue
- **`INSTRUCCIONES.md`** - Cómo usar esta carpeta y subir a GitHub
- **`USO_API.md`** - Guía completa de uso de la API con ejemplos

## ⚙️ Variables de Entorno Requeridas

### Web Service
- `DB_HOST` - Host de PostgreSQL
- `DB_PORT` - Puerto (5432)
- `DB_DATABASE` - Nombre de base de datos
- `DB_USER` - Usuario de PostgreSQL
- `DB_PASSWORD` - Contraseña de PostgreSQL
- `API_KEY` - Clave secreta para autenticación API

### Cron Job
- Las mismas variables de DB (se configuran automáticamente desde la base de datos)

## ⚠️ Notas Importantes

- **Plan Gratuito de Render:**
  - Web Service se "duerme" después de 15 min de inactividad
  - PostgreSQL se pausa después de 90 días de inactividad
  - Cron Jobs pueden tener pequeñas variaciones en el horario

- **Zona Horaria:**
  - Render usa UTC
  - El Cron está configurado para 13:10 UTC = 10:10 Argentina (GMT-3)

- **Tiempo de Ejecución:**
  - El proceso completo puede tardar varios minutos
  - Render permite hasta 1 hora para Cron Jobs

## 🔗 URLs Finales

Una vez desplegado:
- **API Base**: `https://api-productos-sepa.onrender.com`
- **Health Check**: `https://api-productos-sepa.onrender.com/api/v1/health`
- **Buscar Producto**: `https://api-productos-sepa.onrender.com/api/v1/producto/<codigo_barras>`

## 📖 Siguiente Paso

Lee **`DEPLOY.md`** para comenzar el despliegue paso a paso.
