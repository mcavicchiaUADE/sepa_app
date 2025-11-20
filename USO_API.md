# Guía de Uso de la API en Render

Una vez desplegado el sistema en Render, la API estará disponible públicamente.

## URL Base

La URL base de tu API será:
```
https://api-productos-sepa.onrender.com
```

**Nota:** El nombre puede variar según el nombre que le hayas dado al servicio en Render.

## Endpoints Disponibles

### 1. Health Check (Sin autenticación)

Verifica que la API esté funcionando.

**Endpoint:**
```
GET /api/v1/health
```

**Ejemplo:**
```bash
curl https://api-productos-sepa.onrender.com/api/v1/health
```

**Respuesta:**
```json
{
  "status": "ok"
}
```

### 2. Buscar Producto (Requiere autenticación)

Busca un producto por código de barras y retorna información de todos los comercios que lo tienen.

**Endpoint:**
```
GET /api/v1/producto/<codigo_barras>
```

**Headers requeridos:**
```
Authorization: Bearer TU_API_KEY
```

**Ejemplo con curl:**
```bash
curl -H "Authorization: Bearer tu-api-key-aqui" \
     https://api-productos-sepa.onrender.com/api/v1/producto/7795735000328
```

**Ejemplo con JavaScript (fetch):**
```javascript
const codigoBarras = '7795735000328';
const apiKey = 'tu-api-key-aqui';

fetch(`https://api-productos-sepa.onrender.com/api/v1/producto/${codigoBarras}`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${apiKey}`
  }
})
.then(response => response.json())
.then(data => {
  console.log('Producto encontrado:', data);
})
.catch(error => {
  console.error('Error:', error);
});
```

**Ejemplo con Python (requests):**
```python
import requests

codigo_barras = '7795735000328'
api_key = 'tu-api-key-aqui'
url = f'https://api-productos-sepa.onrender.com/api/v1/producto/{codigo_barras}'

headers = {
    'Authorization': f'Bearer {api_key}'
}

response = requests.get(url, headers=headers)
data = response.json()

if response.status_code == 200:
    print('Producto encontrado:', data)
else:
    print('Error:', data)
```

**Ejemplo con Node.js (axios):**
```javascript
const axios = require('axios');

const codigoBarras = '7795735000328';
const apiKey = 'tu-api-key-aqui';

axios.get(`https://api-productos-sepa.onrender.com/api/v1/producto/${codigoBarras}`, {
  headers: {
    'Authorization': `Bearer ${apiKey}`
  }
})
.then(response => {
  console.log('Producto encontrado:', response.data);
})
.catch(error => {
  console.error('Error:', error.response?.data || error.message);
});
```

## Respuestas de la API

### Respuesta Exitosa (200)

```json
{
  "id_producto": "7795735000328",
  "nombre_producto": "bizcocho DON SATUR de grasa PAQ-200-gr",
  "marca_producto": "DON SATUR",
  "comercios": [
    {
      "id_comercio": "9",
      "id_bandera": "1",
      "nombre_comercio": "Vea",
      "precio_producto": "$1200"
    },
    {
      "id_comercio": "12",
      "id_bandera": "1",
      "nombre_comercio": "Coto",
      "precio_producto": "$1250"
    },
    {
      "id_comercio": "10",
      "id_bandera": "1",
      "nombre_comercio": "Carrefour Express",
      "precio_producto": "$1180"
    }
  ]
}
```

### Producto No Encontrado (404)

```json
{
  "error": "Producto no encontrado",
  "id_producto": "7795735000328"
}
```

### Error de Autenticación (401)

```json
{
  "error": "No se proporcionó token de autenticación",
  "mensaje": "Se requiere header Authorization con Bearer token"
}
```

### Token Inválido (403)

```json
{
  "error": "Token inválido",
  "mensaje": "La API key proporcionada no es válida"
}
```

### Error del Servidor (500)

```json
{
  "error": "Error al buscar producto",
  "mensaje": "Descripción del error"
}
```

## Obtener tu API Key

La API Key se configura en las variables de entorno del servicio en Render:

1. Ve al Dashboard de Render
2. Selecciona el servicio `api-productos-sepa`
3. Pestaña "Environment"
4. Busca la variable `API_KEY`
5. Copia el valor (o configúrala si no está)

**Generar una API Key segura:**
```bash
# En tu terminal
openssl rand -hex 32
```

## CORS

La API tiene CORS habilitado para permitir solicitudes desde cualquier origen. Esto significa que puedes hacer peticiones desde:
- Aplicaciones web (JavaScript en el navegador)
- Aplicaciones móviles
- Otros servicios backend
- Cualquier cliente HTTP

## Notas Importantes

### Plan Gratuito de Render

⚠️ **Tiempo de "Despertar":**
- El servicio se "duerme" después de 15 minutos de inactividad
- La primera petición después de dormir puede tardar ~30 segundos
- Las peticiones subsecuentes son normales

**Solución:** Si necesitas evitar el tiempo de despertar, considera:
- Usar un servicio de "ping" periódico para mantener el servicio activo
- Actualizar a un plan de pago

### Rate Limiting

El plan gratuito de Render no tiene rate limiting configurado por defecto. Si necesitas limitar las peticiones, considera:
- Implementar rate limiting en la aplicación
- Usar un servicio externo como Cloudflare
- Actualizar a un plan de pago con rate limiting

### Base de Datos Vacía

Si la base de datos está vacía, todas las búsquedas retornarán 404. Asegúrate de:
1. Ejecutar el Cron Job manualmente al menos una vez
2. Verificar que el proceso de importación se complete exitosamente
3. Revisar los logs del Cron Job para detectar errores

## Ejemplos Completos

### HTML + JavaScript

```html
<!DOCTYPE html>
<html>
<head>
    <title>Buscador de Productos SEPA</title>
</head>
<body>
    <h1>Buscador de Productos</h1>
    <input type="text" id="codigoBarras" placeholder="Código de barras">
    <button onclick="buscarProducto()">Buscar</button>
    <div id="resultado"></div>

    <script>
        const API_URL = 'https://api-productos-sepa.onrender.com/api/v1';
        const API_KEY = 'tu-api-key-aqui'; // ⚠️ En producción, usa variables de entorno

        async function buscarProducto() {
            const codigoBarras = document.getElementById('codigoBarras').value;
            const resultadoDiv = document.getElementById('resultado');

            if (!codigoBarras) {
                resultadoDiv.innerHTML = '<p>Por favor ingresa un código de barras</p>';
                return;
            }

            try {
                const response = await fetch(`${API_URL}/producto/${codigoBarras}`, {
                    headers: {
                        'Authorization': `Bearer ${API_KEY}`
                    }
                });

                const data = await response.json();

                if (response.ok) {
                    resultadoDiv.innerHTML = `
                        <h2>${data.nombre_producto}</h2>
                        <p><strong>Marca:</strong> ${data.marca_producto}</p>
                        <h3>Comercios:</h3>
                        <ul>
                            ${data.comercios.map(c => `
                                <li>${c.nombre_comercio}: ${c.precio_producto}</li>
                            `).join('')}
                        </ul>
                    `;
                } else {
                    resultadoDiv.innerHTML = `<p>Error: ${data.error}</p>`;
                }
            } catch (error) {
                resultadoDiv.innerHTML = `<p>Error de conexión: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
```

### React

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'https://api-productos-sepa.onrender.com/api/v1';
const API_KEY = 'tu-api-key-aqui'; // ⚠️ Usar variable de entorno

function BuscadorProductos() {
  const [codigoBarras, setCodigoBarras] = useState('');
  const [producto, setProducto] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const buscar = async () => {
    if (!codigoBarras) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `${API_URL}/producto/${codigoBarras}`,
        {
          headers: {
            'Authorization': `Bearer ${API_KEY}`
          }
        }
      );

      setProducto(response.data);
    } catch (err) {
      setError(err.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        type="text"
        value={codigoBarras}
        onChange={(e) => setCodigoBarras(e.target.value)}
        placeholder="Código de barras"
      />
      <button onClick={buscar} disabled={loading}>
        {loading ? 'Buscando...' : 'Buscar'}
      </button>

      {error && <p>Error: {error.error || error}</p>}

      {producto && (
        <div>
          <h2>{producto.nombre_producto}</h2>
          <p>Marca: {producto.marca_producto}</p>
          <h3>Comercios:</h3>
          <ul>
            {producto.comercios.map((comercio, index) => (
              <li key={index}>
                {comercio.nombre_comercio}: {comercio.precio_producto}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default BuscadorProductos;
```

## Testing

### Probar con Postman

1. Crear nueva petición GET
2. URL: `https://api-productos-sepa.onrender.com/api/v1/producto/7795735000328`
3. Headers:
   - Key: `Authorization`
   - Value: `Bearer tu-api-key-aqui`
4. Enviar petición

### Probar con cURL

```bash
# Health check
curl https://api-productos-sepa.onrender.com/api/v1/health

# Buscar producto
curl -H "Authorization: Bearer tu-api-key-aqui" \
     https://api-productos-sepa.onrender.com/api/v1/producto/7795735000328
```

## Monitoreo

### Ver Logs de la API

1. Dashboard de Render → `api-productos-sepa`
2. Pestaña "Logs"
3. Ver logs en tiempo real o históricos

### Verificar Estado del Servicio

- Estado "Live": Servicio funcionando
- Estado "Sleeping": Servicio dormido (primera petición será lenta)
- Estado "Deploying": Servicio desplegándose

## Seguridad

⚠️ **Importante:**
- Nunca expongas tu API_KEY en código frontend público
- Usa variables de entorno en aplicaciones cliente
- Considera implementar rate limiting para producción
- Monitorea los logs para detectar uso anómalo

