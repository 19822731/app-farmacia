# 📋 CHANGELOG — Farmacia Torres

> Registro de todos los cambios realizados en el proyecto.  
> Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## [2.7.0] — 2026-10-02 (Normalizador Inteligente de Celulares Argentinos y Verificación en Vivo de Cuentas WhatsApp)

### 🧠 Función Inteligente de Normalización Telefónica (Argentina)
- **Adaptabilidad Total de Formatos:** Normaliza automáticamente cualquier entrada de teléfono móvil de Argentina (`381...`, `0381 15...`, `+54 9 ...`, `54...`, con o sin guiones y espacios) a la estructura internacional que exige WhatsApp: **`549 + código de área + número`** (`549381XXXXXXX`).
- **Inyección del prefijo móvil obligatorio `9`:** Resuelve la causa por la cual WhatsApp rechazaba números argentinos tratándolos como líneas fijas cuando faltaba el `9`.
- **Previsualización en tiempo real en Droguería B2B:** Al ingresar el WhatsApp en el formulario mayorista, se despliega una vista previa formateada y validada en vivo (`📱 WhatsApp: +54 9 381 685-8020`).

### 📡 Verificación en Tiempo Real de Existencia en WhatsApp
- **Microservicio Baileys Integrado (`:8001`):** Implementado servicio HTTP interno que consulta con los servidores de WhatsApp (`sock.onWhatsApp`) si el número efectivamente tiene cuenta registrada y activa.
- **Endpoint API:** `GET /api/whatsapp/verificar-numero?telefono=...` en `server.py` que combina normalización sintáctica y consulta en tiempo real al bot.
- **Botón "Verificar WA" en Panel de Mostrador:** Presente en cada tarjeta de pedido (B2B y B2C) para que el operador verifique con un solo clic si el cliente o farmacia receptora tiene WhatsApp activo (`🟢 WA Activo`, `🔴 Sin cuenta WA` o `⚠️ Formato inválido`).

---

## [2.6.0] — 2026-10-02 (Gestión Integral de Pedidos B2B Droguería & Flujo Completo B2C)

### 🏢 Flujo Operativo y Comercial Completo B2B (Farmacia a Farmacia)
- **Nuevo Endpoint API:** Implementado `PATCH /api/drogueria/pedidos/{pedido_id}/estado` en `server.py` para transicionar los pedidos mayoristas inter-farmacias.
- **Ciclo de vida B2B interactivo:**
  - `Pendiente Aprobación`: Botón **"Aprobar & Armar Lotes"** (pasa a preparación con aviso automático por WhatsApp al Director Técnico) y botón **"Rechazar"** (marca cancelado).
  - `En Armado de Lotes`: Botón **"Marcar Despachado & Avisar WA"** (incluye control de cadena de frío 2°C - 8°C y monto a abonar).
  - `Despachado / Listo`: Botón **"Confirmar Cobrado & Entregado"** (pasa a completado y genera confirmación final).
  - `Entregado & Cobrado`: Badge de operación completada y botón para abrir el **Remito Comercial Digital**.
- **Remito Comercial Oficial Imprimible:** Nuevo modal en el panel de mostrador con membrete oficial de Droguería Farmacia Torres, datos fiscales de la farmacia solicitante (CUIT, DT, Teléfono), detalle de lotes, condición comercial y sectores para firma y sello de recepción, con función directa de impresión / PDF (`window.print()`).
- **Badge de Alertas B2B en Tiempo Real:** En la pestaña "Pedidos Droguería (B2B)" se agregó un contador dinámico ámbar que alerta de pedidos mayoristas entrantes pendientes de aprobación.

### 🛒 Flujo Completo B2C Mostrador (Consumidor Final)
- **Ciclo de vida integral reforzado:** Opciones de cancelación y reactivación para pedidos en mostrador, soporte para delivery y retiro, notificación directa por WhatsApp al tener el pedido listo, y registro del cobro y entrega final.

---

## [2.5.2] — 2026-10-02 (Búsqueda por Enter, Botón Buscar y Scroll Automático a Resultados)

### ⌨️ Soporte Completo para Tecla Enter y Botón "Buscar"
- **Acción Enter en Desktop y Móvil:** Al presionar la tecla Enter (`onkeydown` y `onsubmit`), la búsqueda se ejecuta de inmediato y la página realiza un **scroll suave directo hacia los resultados del catálogo**, evitando que el usuario sienta que no ocurrió nada.
- **Botón visual "Buscar":** Incorporado dentro de la barra de búsqueda tanto en versión de escritorio como en smartphones para usuarios que prefieren hacer clic o tocar con el dedo.
- **Cierre del teclado en móviles (`this.blur()`):** Al presionar Enter o Buscar en smartphones, el teclado virtual se oculta automáticamente para que la pantalla quede despejada mostrando los medicamentos encontrados.
- **Títulos dinámicos de sección:** Al buscar, el título del catálogo cambia en tiempo real a `Resultados para "[nombre]"` con el conteo exacto de medicamentos encontrados.

---

## [2.5.1] — 2026-10-02 (Buscador Multi-Criterio, Filtros Cross-Browser y Botón WhatsApp Ultra-Visible)

### 🔍 Buscador Inteligente Local (0ms de latencia, 100% Vercel)
- **Normalización de acentos y tildes:** Búsquedas insensibles a mayúsculas, minúsculas y tildes (`analgésico` = `analgesico`, `sueño` = `sueno`).
- **Búsqueda multi-palabra y multi-campo:** Busca simultáneamente por nombre comercial, principio activo, categoría, indicación médica, laboratorio y concentración.
- **Sinónimos y malestares clínicos integrados:** Búsquedas como `"gripe"`, `"dolor de cabeza"`, `"panza"`, `"acidez"`, `"dormir"` mapean con precisión a medicamentos relevantes.
- **Filtros rápidos directos:** `"generico"`, `"receta"`, `"venta libre"`.
- **Chips sugeridos interactivos:** Los botones de sugerencia (`💊 Paracetamol`, `💉 Ibuprofeno`, `🧬 Amoxicilina`, `🟢 Genéricos Ahorro`) ahora son botones interactivos que lanzan la búsqueda instantáneamente con scroll automático.

### 🛡️ Compatibilidad Total Cross-Browser (Safari, iOS, Firefox, Chrome)
- **Eliminado ReferenceError de `window.event`:** Las funciones de filtrado ahora reciben `this` directamente (`filtrarCategoria(cat, this)`), eliminando el fallo en Safari/iOS y Firefox que congelaba los botones al hacer clic.
- **Scroll suave automático:** Al seleccionar cualquier categoría o síntoma, la página realiza un scroll suave hacia el catálogo, asegurando que en pantallas móviles el usuario vea los medicamentos de inmediato.
- **Botón "Ocultar listado":** Permite al usuario colapsar el catálogo en cualquier momento con un solo toque.

### 📱 Responsividad y Botón Flotante de WhatsApp
- **Botón WhatsApp Ultra-Visible:** Estilizado con verde oficial `#25D366`, pulso animado de disponibilidad 24hs, contraste elevado, etiqueta legible en móviles y escritorio, y capa superior `z-50` para evitar solapamientos con barras de navegación móviles.

---

## [2.5.0] — 2026-10-02 (Catálogo Bajo Demanda + Correcciones Críticas)

### 🎯 Catálogo Bajo Demanda (UX Limpia)
- **Catálogo oculto por defecto:** La grilla de medicamentos ya NO se muestra al cargar la página, dejando la pantalla limpia y profesional.
- **Placeholder informativo:** En lugar del listado, se muestra un mensaje invitando al usuario a buscar o seleccionar una categoría, con ejemplos de búsquedas populares.
- **Se muestra al interactuar:** El catálogo aparece automáticamente cuando:
  - El usuario escribe ≥2 caracteres en el buscador (desktop o móvil)
  - El usuario hace clic en una categoría (Todos, Genéricos, Vitaminas, etc.)
  - El usuario hace clic en una tarjeta de síntoma (Gripe, Dolor de cabeza, etc.)
- **Se oculta al limpiar:** Al borrar la búsqueda o hacer clic en "Ver todos los productos", vuelve al estado limpio con el placeholder.

### 🔧 Correcciones Críticas
- **Fix tag `<script>` faltante:** Se restauró el tag `<script>` de apertura que fue eliminado accidentalmente durante la inserción del código de turnos/seguridad. Esto causaba que TODA la funcionalidad JavaScript fuera interpretada como texto.
- **Buscador con fallback local:** Cuando la API de búsqueda no está disponible (Vercel), filtra localmente por nombre comercial, principio activo e indicación.
- **Cierre `</section>` restaurado:** Se reparó el cierre de sección HTML del catálogo que se perdió durante la reestructuración.

---

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
