# Instrucciones para Desplegar en Render

## 📦 ¿Qué es esta carpeta?

Esta carpeta (`render-deploy/`) contiene **TODO** lo necesario para desplegar el sistema completo en Render. Es una versión limpia y lista para producción.

## 🚀 Pasos para Desplegar

### Opción 1: Subir a GitHub y conectar a Render (Recomendado)

1. **Crea un nuevo repositorio en GitHub**
   ```bash
   # En GitHub, crea un nuevo repositorio llamado "sepa-api-render"
   ```

2. **Inicializa git en esta carpeta**
   ```bash
   cd render-deploy
   git init
   git add .
   git commit -m "Initial commit - Sistema SEPA para Render"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/sepa-api-render.git
   git push -u origin main
   ```

3. **Conecta a Render**
   - Ve a https://render.com
   - Dashboard → "New +" → "Blueprint"
   - Conecta tu repositorio de GitHub
   - Selecciona el repositorio `sepa-api-render`
   - Render detectará automáticamente el `render.yaml`

4. **Sigue las instrucciones en `DEPLOY.md`**

### Opción 2: Subir directamente a Render

1. **Comprime esta carpeta**
   ```bash
   # En Windows
   Compress-Archive -Path render-deploy -DestinationPath render-deploy.zip
   
   # En Linux/Mac
   zip -r render-deploy.zip render-deploy/
   ```

2. **Sube a Render**
   - Ve a https://render.com
   - Dashboard → "New +" → "Blueprint"
   - Sube el archivo ZIP
   - Render extraerá y detectará el `render.yaml`

## ✅ Verificación Pre-Despliegue

Antes de desplegar, verifica que tengas:

- ✅ `render.yaml` - Configuración de servicios
- ✅ `Procfile` - Configuración de la API
- ✅ `requirements.txt` - Dependencias
- ✅ `runtime.txt` - Versión de Python
- ✅ `app/` - Código de la aplicación
- ✅ `config/` - Configuración
- ✅ `scripts/` - Scripts necesarios

## 📋 Checklist de Despliegue

- [ ] Carpeta subida a GitHub o lista para subir
- [ ] Repositorio conectado a Render
- [ ] Variables de entorno configuradas (ver `DEPLOY.md`)
- [ ] API_KEY generada y configurada
- [ ] Base de datos PostgreSQL creada
- [ ] Cron Job configurado correctamente
- [ ] Primera ejecución del Cron Job completada
- [ ] API probada y funcionando

## 🔍 Estructura de Archivos

```
render-deploy/
├── README.md                    # Descripción general
├── INSTRUCCIONES.md            # Este archivo
├── DEPLOY.md                    # Guía paso a paso
├── USO_API.md                   # Guía de uso de la API
├── render.yaml                  # ⭐ Configuración principal de Render
├── Procfile                     # Configuración de la API
├── requirements.txt             # Dependencias Python
├── runtime.txt                  # Versión de Python
├── .gitignore                   # Archivos a ignorar en git
├── app/                         # Código de la aplicación
├── config/                      # Configuración
└── scripts/                     # Scripts
```

## ⚠️ Importante

- **NO modifiques** los paths en los scripts, están configurados para funcionar en Render
- **NO agregues** archivos `.env` a git (están en `.gitignore`)
- **SÍ configura** las variables de entorno en el dashboard de Render
- **SÍ prueba** el sistema después del despliegue

## 📚 Documentación

- **`DEPLOY.md`** - Guía completa paso a paso
- **`USO_API.md`** - Cómo usar la API una vez desplegada
- **`README.md`** - Descripción general del sistema

## 🆘 Problemas Comunes

### El despliegue falla
- Verifica que todas las dependencias estén en `requirements.txt`
- Revisa los logs de build en Render
- Asegúrate de que Python 3.11 esté disponible

### La API no responde
- Verifica que el Web Service esté "Live"
- Revisa las variables de entorno
- Verifica los logs del servicio

### El Cron Job no se ejecuta
- Verifica el schedule en `render.yaml`
- Revisa los logs del Cron Job
- Asegúrate de que las variables de DB estén configuradas

## ✅ Listo para Desplegar

Si tienes todo listo, sigue las instrucciones en **`DEPLOY.md`** para comenzar el despliegue.

¡Buena suerte! 🚀

