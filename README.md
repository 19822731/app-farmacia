# 🏥 Farmacia Torres - WhatsApp Bot & Catálogo Web

Solución integral de código abierto para automatizar la atención al cliente, consultas de precios/stock y pedidos en farmacias mediante **WhatsApp** y un **Catálogo Web Híbrido**.

---

## ⚡ Inicio Rápido (Prueba Local Inmediata)

No requiere Docker para comenzar a probar. El proyecto cuenta con un servidor en Python con FastAPI y un catálogo web listo para usar:

```bash
# 1. Ingresar a la carpeta del proyecto
cd farmacia-whatsapp-bot

# 2. Iniciar el servidor
python3 server.py
```

Luego abre tu navegador en:
* **Catálogo Web para Clientes:** [http://localhost:8000](http://localhost:8000)
* **Panel de Mostrador & Farmacéutico:** [http://localhost:8000/admin](http://localhost:8000/admin)
* **Documentación interactiva de la API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📱 Conectar un WhatsApp Real con Código QR (Sin Docker)

Puedes conectar tu propio número de WhatsApp inmediatamente para que el bot responda mensajes en vivo:

```bash
cd farmacia-whatsapp-bot
node whatsapp_bot.js
```
*(O simplemente hacer doble clic en el archivo ejecutable `CONECTAR_WHATSAPP_REAL.command`)*.

1. Aparecerá un **código QR en la terminal**.
2. Abre WhatsApp en tu celular > **Ajustes / Dispositivos vinculados** > **Vincular un dispositivo**.
3. Escanea el código QR y verás el mensaje: `¡WHATSAPP CONECTADO EXITOSAMENTE A LA FARMACIA!`.
4. Envía un mensaje desde otro teléfono (o pide a alguien que te escriba) palabras como *"Hola"*, *"Tafirol"*, *"Ibuprofeno"*, o mándale una foto de una receta médica para ver las respuestas automáticas.

---

Para conectar un número real de WhatsApp mediante código QR y flujos visuales interactivos:

```bash
# 1. Copiar archivo de entorno
cp .env.example .env

# 2. Levantar los contenedores
docker compose up -d
```

### Servicios Disponibles con Docker:
* **Evolution API v2:** `http://localhost:8080` (Conector oficial de WhatsApp con código QR).
* **Typebot Builder:** `http://localhost:3000` (Diseñador visual de árboles de decisión y flujos).
* **Typebot Viewer:** `http://localhost:3001` (Motor conversacional).
* **PostgreSQL:** Puerto 5432.
* **Redis:** Puerto 6379.

---

## 📋 Estructura del Proyecto

* **[ROADMAP.md](ROADMAP.md):** Hoja de ruta completa, arquitectura detallada y guía de continuidad para modelos de IA.
* **`server.py`:** Backend con motor de búsqueda difusa (*Fuzzy Search* con RapidFuzz), generador de pedidos y webhook de WhatsApp.
* **`data/medicamentos.json`:** Base de datos de ejemplo con marcas, principios activos, precios y alertas de receta médica.
* **`data/medicamentos.csv`:** Archivo compatible con Google Sheets o Excel.
* **`static/index.html`:** Catálogo web moderno, buscador en tiempo real, carrito de compras y botón *"Pedir por WhatsApp"*.
* **`docker-compose.yml`:** Orquestación de contenedores para producción.
