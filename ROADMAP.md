# 🗺️ Hoja de Ruta & Evolución: Farmacia Torres

> **Documento de Contexto y Continuidad Técnica**  
> Este archivo detalla el objetivo del proyecto, las decisiones de arquitectura, el estado de avance y los pasos exactos a seguir para que **cualquier modelo de IA o desarrollador** que retome esta sesión pueda continuar sin pérdida de contexto.
>
> 📋 Ver [CHANGELOG.md](./CHANGELOG.md) para el historial detallado de cambios.

---

## 🎯 1. Visión y Objetivo del Proyecto
Automatizar y optimizar el flujo de atención al cliente de farmacias (y comercios de cercanía) mediante:
1. **Atención por WhatsApp:** Respuestas instantáneas sobre stock, presentaciones, precios y si el medicamento requiere receta médica.
2. **Búsqueda por Principio Activo vs. Marca:** Entender tanto marcas comerciales (ej: *Tafirol, Ibupirac*) como drogas genéricas (ej: *Paracetamol, Ibuprofeno*).
3. **Catálogo Web Interactivo Híbrido (Web-to-WhatsApp):** Permitir al cliente armar un carrito desde su celular y enviarlo con un clic formateado directamente al WhatsApp de la farmacia.
4. **Recepción de Recetas Médicas:** Canalizar fotos de órdenes médicas para validación farmacéutica.
5. **Portal B2B de Droguería:** Permitir a otras farmacias de la zona generar pedidos mayoristas de preparados magistrales (oncológicos, cosméticos, analgésicos, quimioterápicos).

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
          │    con botones)     │   │  de Pedidos, Webhooks, B2B) │
          └─────────────┬───────┘   └──────────────┬──────────────┘
                        │                          │
                        └──────────┬───────────────┘
                                   ▼
             ┌───────────────────────────────────────────┐
             │      Base de Datos de Medicamentos        │
             │  • data/medicamentos.json (B2C · 30 prod) │
             │  • data/medicamentos_b2b.json (B2B · 12)  │
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
| **Fase 4** | **Motor de Genéricos & Sugerencia de Ahorro** | ✅ **COMPLETADA** | Filtro genéricos, pares marca vs genérico, sugerencia automática en WhatsApp |
| **Fase 5** | **Entorno Docker (Evolution API v2 + Typebot)** | 🟡 **LISTO PARA LEVANTAR** | `docker-compose.yml`, `.env.example` |
| **Fase 6** | **Rediseño Profesional del Frontend** | ✅ **COMPLETADA** | `static/index.html` reescrito completo, diseño nivel estudio, estética Farmacity |
| **Fase 7** | **Portal B2B Droguería & Laboratorio Magistral** | ✅ **COMPLETADA** | `static/drogueria.html`, `data/medicamentos_b2b.json`, endpoints B2B en `server.py` |
| **Fase 8** | **Auditoría, CHANGELOG & Roadmap** | ✅ **COMPLETADA** | `CHANGELOG.md`, `ROADMAP.md` actualizado, CSV sincronizado, URLs configurables |
| **Fase 9** | **Reconocimiento de Recetas con IA (OCR)** | ⚪ Pendiente | Integrar Gemini Vision API para transcribir fotos de recetas manuscritas |
| **Fase 10** | **Sincronización en Tiempo Real con Google Sheets** | ⚪ Pendiente | Edición dinámica de precios/stock desde Google Drive |
| **Fase 11** | **Handoff a Farmacéutico Humano (Chatwoot)** | ⚪ Pendiente | Derivar chats complejos o de psicotrópicos a farmacéutico |
| **Fase 12** | **Despliegue en Producción** | ⚪ Pendiente | Dominio propio, HTTPS, Docker en VPS, URLs públicas |

---

## ✅ 4. Checklist de Funcionalidades

### Frontend B2C (Público)
- [x] Buscador fuzzy en tiempo real
- [x] Filtros por categoría de síntoma (7 categorías)
- [x] Cards de producto con comparación marca/genérico
- [x] Carrito con cálculo de obra social
- [x] Envío de pedido por WhatsApp (`wa.me`)
- [x] Simulador de bot WhatsApp integrado
- [x] Modal de carga de receta médica
- [x] Diseño profesional (Plus Jakarta Sans, gradientes, trust pillars)
- [x] Enlace al portal B2B desde la barra superior
- [ ] Responsive testing completo en móviles reales
- [ ] Integración con OCR de recetas (Gemini Vision)

### Frontend B2B (Farmacias)
- [x] Catálogo de 12 productos en 4 rubros
- [x] Filtro por rubro (Oncológicos, Cosméticos, Analgésicos, Quimioterápicos)
- [x] Carrito mayorista con cantidades por lote
- [x] Formulario de orden de compra (farmacia, CUIT, director técnico)
- [x] Indicador de cadena de frío
- [x] Ficha técnica de productos
- [x] Envío de orden por WhatsApp
- [ ] Autenticación / registro de farmacias
- [ ] Historial de pedidos por farmacia
- [ ] Tracking de estado de pedidos B2B

### Panel Admin (Mostrador)
- [x] Lista de pedidos B2C con estados
- [x] Cambio de estado de pedidos
- [x] Vista de inventario
- [x] Pestaña de pedidos B2B (droguería)
- [ ] Dashboard con métricas de ventas
- [ ] Alertas de stock bajo
- [ ] Exportación de reportes

### Backend API
- [x] `GET /api/medicamentos` — Catálogo B2C (30 productos)
- [x] `GET /api/medicamentos/buscar?q=` — Búsqueda fuzzy
- [x] `POST /api/pedidos/crear` — Crear pedido B2C
- [x] `GET /api/pedidos` — Listar pedidos B2C
- [x] `GET /api/drogueria/productos` — Catálogo B2B (12 productos)
- [x] `POST /api/drogueria/pedidos` — Crear pedido B2B
- [x] `GET /api/drogueria/pedidos` — Listar pedidos B2B
- [x] `POST /api/webhook/whatsapp` — Webhook para Evolution API
- [x] URLs configurables via `BASE_URL` (env var)
- [ ] Autenticación JWT para admin y B2B
- [ ] Rate limiting en API pública
- [ ] Validación CUIT

### WhatsApp Bot
- [x] Menú de bienvenida
- [x] Búsqueda de medicamentos
- [x] Sugerencia de genéricos
- [x] Derivación a farmacéutico
- [x] Soporte auto-mensajes (`append` events)
- [x] URLs configurables via `PUBLIC_URL` (env var)
- [ ] Procesamiento de fotos de recetas
- [ ] Confirmación de pedidos por bot
- [ ] Notificación de cambio de estado

---

## 📁 5. Estructura de Archivos del Proyecto

```
farmacia-whatsapp-bot/
├── ROADMAP.md                     # Este documento (Evolución y Guía)
├── CHANGELOG.md                   # Registro de cambios por versión
├── README.md                      # Documentación de inicio rápido
├── CONECTAR_WHATSAPP_REAL.command # Lanzador con QR y autoarranque
├── INICIAR_DEMO_FARMACIA.command  # Lanzador rápido del servidor
├── docker-compose.yml             # Stack: Evolution API, Typebot, PostgreSQL, Redis
├── .env.example                   # Variables de entorno (BASE_URL, PUBLIC_URL, etc.)
├── .gitignore                     # Protege auth_session, node_modules, .env
├── server.py                      # Backend FastAPI (B2C + B2B + Webhooks)
├── whatsapp_bot.js                # Conector WhatsApp con Baileys
├── package.json                   # Dependencias Node.js
├── data/
│   ├── medicamentos.json          # Base de datos B2C (30 productos)
│   ├── medicamentos_b2b.json      # Base de datos B2B (12 productos, 4 rubros)
│   ├── medicamentos.csv           # CSV sincronizado para Google Sheets/Excel
│   ├── pedidos.json               # Pedidos de mostrador (B2C)
│   └── pedidos_b2b.json           # Pedidos mayoristas (B2B)
└── static/
    ├── index.html                 # Catálogo web público (diseño profesional)
    ├── admin.html                 # Panel de mostrador (B2C + B2B tabs)
    └── drogueria.html             # Portal B2B para farmacias
```

---

## 🚀 6. Cómo probar el sistema

1. **Ejecutar el servidor local:**
   ```bash
   cd /Users/arquimedescarrizo/Desktop/farmacia-whatsapp-bot
   python3 server.py
   ```
2. **Abrir en el navegador:**
   - Catálogo público: `http://localhost:8000`
   - Panel admin: `http://localhost:8000/admin`
   - Portal B2B: `http://localhost:8000/drogueria`
   - API Swagger: `http://localhost:8000/docs`

3. **Conectar WhatsApp (opcional):**
   ```bash
   node whatsapp_bot.js
   ```
   Escanear el código QR que aparece en terminal.

---

## 🤖 7. Instrucciones para el Próximo Modelo de IA / Próxima Sesión

Si la sesión se cierra y otro modelo de IA retoma este repositorio:
1. **Idioma:** Comunicarse siempre en **español** con el usuario.
2. **Contexto:** El usuario desarrolla una solución para automatizar la atención en farmacias mediante WhatsApp y catálogo web, con un portal B2B para droguería.
3. **Decisión tecnológica:** Stack Open Source: Evolution API + Typebot + Backend Python/FastAPI + Catálogo Web.
4. **Leer primero:** `CHANGELOG.md` para entender el historial, y este `ROADMAP.md` para el estado actual.
5. **Variables de entorno:** `BASE_URL` (Python) y `PUBLIC_URL` (Node.js) para URLs públicas.
6. **Siguientes tareas recomendadas:**
   - Integrar OCR de recetas con Gemini Vision API
   - Agregar autenticación para panel admin y portal B2B
   - Desplegar en producción con dominio propio
   - Sincronizar con Google Sheets para edición de precios
