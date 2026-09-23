# 🗺️ Hoja de Ruta & Evolución: Bot de WhatsApp y Catálogo para Farmacias

> **Documento de Contexto y Continuidad Técnica**  
> Este archivo detalla el objetivo del proyecto, las decisiones de arquitectura, el estado de avance y los pasos exactos a seguir para que **cualquier modelo de IA o desarrollador** que retome esta sesión pueda continuar sin pérdida de contexto.

---

## 🎯 1. Visión y Objetivo del Proyecto
Automatizar y optimizar el flujo de atención al cliente de farmacias (y comercios de cercanía) mediante:
1. **Atención por WhatsApp:** Respuestas instantáneas sobre stock, presentaciones, precios y si el medicamento requiere receta médica.
2. **Búsqueda por Principio Activo vs. Marca:** Entender tanto marcas comerciales (ej: *Tafirol, Ibupirac*) como drogas genéricas (ej: *Paracetamol, Ibuprofeno*).
3. **Catálogo Web Interactivo Híbrido (Web-to-WhatsApp):** Permitir al cliente armar un carrito desde su celular y enviarlo con un clic formateado directamente al WhatsApp de la farmacia.
4. **Recepción de Recetas Médicas:** Canalizar fotos de órdenes médicas para validación farmacéutica.

---

## 🏗️ 2. Arquitectura del Sistema

```
                    ┌─────────────────────────┐
                    │   Cliente en WhatsApp   │
                    └───────────┬─────────────┘
                                │ (Mensajes / Fotos de recetas)
                                ▼
         ┌───────────────────────────────────────────────┐
         │     Evolution API v2 (Gateway WhatsApp)       │
         │   (Emula sesión WhatsApp Web con código QR)   │
         └──────────────┬─────────────────┬──────────────┘
                        │                 │
                        ▼                 ▼
          ┌─────────────────────┐   ┌─────────────────────────────┐
          │   Typebot Builder   │   │  Backend Python / FastAPI   │
          │ (Flujos interactivos│   │ (Búsqueda Fuzzy, Generador  │
          │    con botones)     │   │  de Pedidos, Webhooks)      │
          └─────────────┬───────┘   └──────────────┬──────────────┘
                        │                          │
                        └──────────┬───────────────┘
                                   ▼
             ┌───────────────────────────────────────────┐
             │      Base de Datos de Medicamentos        │
             │  • data/medicamentos.json (PoC Local)     │
             │  • data/medicamentos.csv (Google Sheets)  │
             │  • PostgreSQL (Producción en Docker)      │
             └───────────────────────────────────────────┘
```

---

## 📊 3. Estado de Avance y Evolución

| Fase | Descripción | Estado | Componentes / Archivos |
| :--- | :--- | :--- | :--- |
| **Fase 1** | **PoC Local & Dataset de Farmacia** | ✅ **COMPLETADA** | `data/medicamentos.json`, `data/medicamentos.csv`, `server.py`, `static/index.html` |
| **Fase 2** | **Conector de WhatsApp Real (Código QR sin Docker)** | ✅ **COMPLETADA** | `whatsapp_bot.js`, `CONECTAR_WHATSAPP_REAL.command`, `@whiskeysockets/baileys` |
| **Fase 3** | **Panel de Mostrador & Obras Sociales (/admin)** | ✅ **COMPLETADA** | `static/admin.html`, `data/pedidos.json`, cálculo de copago OSDE/PAMI/Swiss |
| **Fase 4** | **Motor de Genéricos & Sugerencia de Ahorro** | ✅ **COMPLETADA** | Filtro genéricos, pares de marca vs genérico, sugerencia automática de ahorro en WhatsApp |
| **Fase 5** | **Entorno Docker (Evolution API v2 + Typebot)** | 🟡 **LISTO PARA LEVANTAR** | `docker-compose.yml`, `.env.example` |
| **Fase 6** | **Reconocimiento de Recetas con IA (OCR)** | ⚪ Pendiente | Integrar Gemini Vision API para transcribir fotos de recetas manuscritas |
| **Fase 7** | **Sincronización en Tiempo Real con Google Sheets** | ⚪ Pendiente | Edición dinámica de precios/stock desde Google Drive |
| **Fase 8** | **Handoff a Farmacéutico Humano (Chatwoot)** | ⚪ Pendiente | Derivar chats complejos o de psicotrópicos a farmacéutico |

---

## 📁 4. Estructura de Archivos del Proyecto

```
farmacia-whatsapp-bot/
├── ROADMAP.md                  # Este documento (Evolución y Guía para IA)
├── README.md                   # Documentación de inicio rápido
├── CONECTAR_WHATSAPP_REAL.command # Lanzador con QR y autoarranque
├── INICIAR_DEMO_FARMACIA.command  # Lanzador rápido del servidor y navegador
├── docker-compose.yml          # Stack de Evolution API v2, Typebot, Postgres y Redis
├── .env.example                # Variables de entorno modelo
├── server.py                   # Backend FastAPI (Búsqueda fuzzy, Pedidos, /admin, Webhooks)
├── whatsapp_bot.js             # Conector nativo de WhatsApp con Baileys y Modo Seguro
├── data/
│   ├── medicamentos.json       # Base de datos de prueba con campos farmacéuticos
│   ├── medicamentos.csv        # Versión CSV para importar a Google Sheets/Excel
│   └── pedidos.json            # Base de datos persistente de pedidos de mostrador
└── static/
    ├── index.html              # Catálogo web para clientes + Carrito + Calculadora Obra Social
    └── admin.html              # Panel de control de mostrador, gestión de pedidos e inventario
```

---

## 🚀 5. Cómo probar lo que está construido actualmente (Fase 1)

Dado que en el entorno local no se cuenta con Docker instalado por defecto, se creó un **servidor independiente en Python** con FastAPI y RapidFuzz que permite probar toda la experiencia sin dependencias externas:

1. **Ejecutar el servidor local:**
   ```bash
   cd /Users/arquimedescarrizo/Desktop/farmacia-whatsapp-bot
   python3 server.py
   ```
2. **Abrir en el navegador:**
   - Catálogo web y Simulador de Bot: `http://localhost:8000`
   - Documentación Swagger de la API: `http://localhost:8000/docs`
3. **Funcionalidades activas para probar:**
   - **Buscador en tiempo real:** Escribir marcas comerciales (*"Tafirol"*, *"Actron"*) o drogas genéricas (*"Ibuprofeno"*, *"Amoxicilina"*, *"Paracetamol"*). El algoritmo utiliza **Fuzzy Search**, por lo que tolera errores tipográficos.
   - **Carrito y Pedido por WhatsApp:** Agregar medicamentos al carrito. Detecta si algún medicamento requiere receta y agrega automáticamente la advertencia legal. Al presionar *"Enviar Pedido por WhatsApp"*, genera el mensaje formateado listo para enviar por `wa.me`.
   - **Simulador de Bot de WhatsApp:** Botón en la esquina superior derecha que abre un chat donde simula cómo responderá el bot a las consultas de los clientes.

---

## 🤖 6. Instrucciones para el Próximo Modelo de IA / Próxima Sesión

Si la sesión se cierra y otro modelo de IA retoma este repositorio:
1. **Idioma:** Comunicarse siempre en **español** con el usuario.
2. **Contexto:** El usuario está desarrollando una solución para automatizar la atención en farmacias mediante WhatsApp y un catálogo web conectado.
3. **Decisión tecnológica:** Se eligió la **Opción 2** (Stack Open Source: Evolution API + Typebot + Backend Python/FastAPI + Catálogo Web).
4. **Siguientes tareas inmediatas recomendadas a consultar con el usuario:**
   - Si el usuario desea instalar Docker en su Mac para levantar `docker-compose.yml` (Evolution API y Typebot) o si prefiere seguir refinando la lógica del backend y el catálogo en Python.
   - Conectar un modelo de visión (como Gemini 1.5/2.0 Flash) para analizar fotos de recetas médicas.
   - Sincronizar la base de datos con una hoja real de Google Sheets para que los empleados de la farmacia puedan modificar precios desde el celular.
