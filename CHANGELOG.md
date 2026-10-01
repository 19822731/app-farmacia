# 📋 CHANGELOG — Farmacia Torres

> Registro de todos los cambios realizados en el proyecto.  
> Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).
## [2.4.0] — 2026-10-01 (WhatsApp Real + Deploy Vercel)

### 📱 Botón Inteligente de WhatsApp
- **Detección automática de dispositivo:** En celular, el botón abre directamente la app de WhatsApp real apuntando al número de Farmacia Torres (`543816858001`). En PC, muestra un modal con dos opciones: abrir WhatsApp Web o usar el simulador en pantalla.
- **Links wa.me corregidos:** Todos los enlaces de WhatsApp (header, recetas, pedidos) ahora apuntan al número real `543816858001` en vez de quedar vacíos.
- **Simulador como fallback:** El simulador en pantalla se mantiene para usuarios de PC que no tienen WhatsApp instalado. En deploy remoto (Vercel), si no hay backend disponible, el simulador redirige al WhatsApp real.

### 🚀 Preparación para Deploy en Vercel
- Creado `vercel.json` con rutas para servir los archivos estáticos del frontend.
- Arquitectura híbrida: Frontend en Vercel (catálogo público) + Backend en Mac local (bot WhatsApp + API + panel admin).

---

## [2.3.0] — 2026-10-01 (Chatbot Conversacional & Correlación de Mostrador)

### 🤖 Chatbot Conversacional Gradual (State Machine)
- **Máquina de estados conversacional:** Implementada en `server.py` (`SESIONES_CHAT`) con memoria por usuario.
- **Flujo guiado paso a paso:**
  - Paso 1: Saludo y Menú Principal interactivo (opciones 1 a 5).
  - Paso 2: Búsqueda de medicamento (por nombre, droga o por catálogo de síntomas).
  - Paso 3: Comparador inteligente de Genérico vs Marca Líder con cálculo de ahorro exacto.
  - Paso 4: Selección de modalidad de entrega (Retiro en mostrador o Envío a domicilio).
  - Paso 5: Selección de Obra Social (PAMI 50%, OSDE 40%, Swiss Medical 40%, Particular).
- **Filtro de exclusión (Stopwords):** Eliminados los falsos positivos donde saludos como *"Hola"* arrojaban listas de medicamentos como Alcohol o Salbutamol.
- **Consultas por malestar / síntomas:** Nuevo submenú con 6 categorías que recomienda medicamentos de venta libre.

### 💾 Correlación Transaccional con el Mostrador (/admin)
- **Creación automática de pedidos:** Al concluir la conversación por WhatsApp o simulador, el bot guarda automáticamente el pedido en `data/pedidos.json` con ID `#PED-XXXX`.
- **Panel del operario en tiempo real:** En `http://localhost:8000/admin`, el pedido aparece inmediatamente en la columna de *Pendientes*.
- **Auto-refresco acelerado:** El panel de mostrador ahora consulta cada 5 segundos (antes 10s) tanto para pedidos B2C como B2B.

---

## [2.2.0] — 2026-09-30 (Auditoría y Correcciones)

### 🔧 Corregido
- **CSV desincronizado:** Agregados MED-025 a MED-030 (Vitaminas, Suplementos, Falta de Sueño) a `data/medicamentos.csv`
- **URLs localhost hardcodeadas:** Reemplazadas por constantes configurables (`BASE_URL` / `PUBLIC_URL`) en `server.py`, `whatsapp_bot.js` e `index.html`
- **Panel admin sin B2B:** Agregada pestaña "Droguería B2B" en `admin.html` para ver pedidos mayoristas
- **ROADMAP desactualizado:** Actualizado con fases 6-8 (rediseño, B2B, auditoría) y nueva estructura de archivos

### 📄 Agregado
- `CHANGELOG.md` — Registro de cambios del proyecto
- Endpoint `GET /api/drogueria/pedidos` en `server.py` — Para listar pedidos B2B desde admin

### 🧹 Limpieza
- Eliminado pedido de test B2B-2642 de `data/pedidos_b2b.json`
- Agregadas variables `BASE_URL` y `PUBLIC_URL` a `.env.example`

---

## [2.1.0] — 2026-09-30 (Portal B2B Droguería)

### 🆕 Agregado
- **Portal B2B completo** para farmacias (`/drogueria` y `/b2b`)
- Nuevo archivo `static/drogueria.html` — Interfaz dark-theme profesional para pedidos mayoristas
- Nuevo archivo `data/medicamentos_b2b.json` — 12 productos en 4 rubros:
  - 🧬 Oncológicos (3): Ondansetrón, Metoclopramida, Dexametasona
  - 💄 Cosméticos (3): Ácido Hialurónico, Vitamina C Serum, Niacinamida
  - 💊 Analgésicos (3): Tramadol, Ketorolac, Diclofenac Sódico
  - 🧪 Quimioterápicos (3): Ciclofosfamida, Metotrexato, Capecitabina
- Nuevo archivo `data/pedidos_b2b.json` — Almacén de pedidos mayoristas
- Endpoint `POST /api/drogueria/pedidos` — Crear órdenes de compra B2B
- Endpoint `GET /api/drogueria/productos` — Consultar catálogo mayorista
- Modelos Pydantic: `ItemPedidoB2B`, `PedidoB2BRequest`
- Enlace "🏢 Acceso Farmacias & Droguería B2B" en la barra superior de `index.html`
- Botón "Droguería B2B" en header de `index.html`

### 🔄 Modificado
- `server.py`: Versión 2.1.0, nuevas rutas B2B, helpers de carga/guardado B2B
- Título y descripción de la app actualizados

---

## [2.0.0] — 2026-09-30 (Rediseño Profesional)

### 🎨 Rediseño Completo del Frontend
- **Reescritura total de `static/index.html`** (~1240 líneas) con diseño nivel estudio
- Tipografía: **Plus Jakarta Sans** (Google Fonts)
- Barra superior oscura con indicadores de confianza (turno, envíos, matrícula)
- Header omnichannel con buscador centrado y atajo `⌘K`
- Banner hero con gradiente y propuesta de valor (60% ahorro, 70% OS)
- Sección "¿Qué necesitas tratar?" estilo Farmacity con 7 cards:
  - 🤒 Gripe y Resfrío, 🤕 Dolor de Cabeza, 🤢 Dolor de Panza
  - 🤧 Alergias, 😴 Falta de Sueño, 💊 Vitaminas, 🏋️ Suplementos
- Pilares de confianza: ANMAT, Farmacéutico, Precios Claros, Obras Sociales
- Cards de productos profesionales con comparación genérica inteligente
- Modal de carga de recetas médicas
- Carrito rediseñado con cálculo de descuento por obra social
- Botón flotante de simulador WhatsApp
- Footer institucional completo

### 🆕 Productos Nuevos
- MED-025: Redoxon Vitamina C 1g (Marca)
- MED-026: Vitamina C 1g Efervescente Genérica
- MED-027: Total Magnesiano Vitalizante (Marca)
- MED-028: Magnesio Quelato 500mg Genérico
- MED-029: Melatol Plus Melatonina 3mg (Marca)
- MED-030: Melatonina 3mg Pura Genérica

---

## [1.1.0] — 2026-09-30 (Renombramiento)

### 🔄 Renombramiento: "Farmacia San Martín" → "Farmacia Torres"
- Archivos modificados: `server.py`, `whatsapp_bot.js`, `static/index.html`, `static/admin.html`, `CONECTAR_WHATSAPP_REAL.command`, `README.md`
- Todas las menciones del nombre de la farmacia actualizadas
- Direcciones físicas (Av. San Martín) conservadas como datos de ubicación

### 🔧 Mejoras en WhatsApp Bot
- Soporte para eventos `append` (auto-mensajes) además de `notify`
- Variable `quoteOpt` para evitar citar mensajes propios
- Logging mejorado: `📩 [WhatsApp ${m.type}]` en consola

---

## [1.0.0] — 2026-09-30 (Versión Inicial)

### 🆕 Sistema Completo de Farmacia
- **Backend FastAPI** (`server.py`): Búsqueda fuzzy con RapidFuzz, gestión de pedidos, webhooks
- **Catálogo Web** (`static/index.html`): Buscador, carrito, calculadora de obra social, simulador WhatsApp
- **Panel Admin** (`static/admin.html`): Gestión de pedidos, estados, inventario
- **Bot WhatsApp** (`whatsapp_bot.js`): Conector Baileys, respuestas automáticas, derivación humana
- **Base de datos**: 24 medicamentos con marca/genérico, precios, stock, receta
- **Docker Stack** (`docker-compose.yml`): Evolution API, Typebot, PostgreSQL, Redis
- Repositorio inicializado en GitHub: `19822731/app-farmacia`
