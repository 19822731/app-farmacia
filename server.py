import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from rapidfuzz import fuzz, process

# Rutas base
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "medicamentos.json"
DATA_B2B_FILE = BASE_DIR / "data" / "medicamentos_b2b.json"
PEDIDOS_FILE = BASE_DIR / "data" / "pedidos.json"
PEDIDOS_B2B_FILE = BASE_DIR / "data" / "pedidos_b2b.json"
STATIC_DIR = BASE_DIR / "static"
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8000')

app = FastAPI(
    title="Farmacia & Droguería Torres API",
    description="Backend integral: Catálogo público, portal droguería B2B (Oncológicos, Cosméticos, Analgésicos, Quimioterápicos) y WhatsApp Bot",
    version="2.1.0"
)

# Servir archivos estáticos
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- MANEJO DE DATOS ---

def load_medicamentos() -> List[dict]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_medicamentos(meds: List[dict]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(meds, f, indent=2, ensure_ascii=False)

def load_pedidos() -> List[dict]:
    if not PEDIDOS_FILE.exists():
        return []
    with open(PEDIDOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_pedidos(pedidos: List[dict]):
    with open(PEDIDOS_FILE, "w", encoding="utf-8") as f:
        json.dump(pedidos, f, indent=2, ensure_ascii=False)

def load_medicamentos_b2b() -> List[dict]:
    if not DATA_B2B_FILE.exists():
        return []
    with open(DATA_B2B_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_pedidos_b2b() -> List[dict]:
    if not PEDIDOS_B2B_FILE.exists():
        return []
    with open(PEDIDOS_B2B_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_pedidos_b2b(pedidos: List[dict]):
    with open(PEDIDOS_B2B_FILE, "w", encoding="utf-8") as f:
        json.dump(pedidos, f, indent=2, ensure_ascii=False)

# --- MODELOS PYDANTIC ---

class ItemPedido(BaseModel):
    id: str
    cantidad: int

class ItemPedidoB2B(BaseModel):
    id: str
    cantidad: int

class PedidoB2BRequest(BaseModel):
    farmacia_nombre: str
    cuit: str
    director_tecnico: str
    telefono: str
    direccion: Optional[str] = ""
    items: List[ItemPedidoB2B]
    observaciones: Optional[str] = ""

class PedidoRequest(BaseModel):
    cliente_nombre: Optional[str] = "Cliente"
    cliente_telefono: Optional[str] = ""
    obra_social: Optional[str] = "Particular (Sin cobertura)"
    descuento_pct: Optional[int] = 0
    items: List[ItemPedido]
    observaciones: Optional[str] = ""

class ActualizarEstadoRequest(BaseModel):
    estado: str  # 'pendiente', 'preparando', 'listo', 'entregado', 'cancelado'

class MedicamentoInput(BaseModel):
    nombre_comercial: str
    principio_activo: str
    concentracion: Optional[str] = ""
    presentacion: str
    laboratorio: str
    precio: float
    stock: int
    requiere_receta: bool
    es_generico: Optional[bool] = False
    categoria: str
    indicacion: Optional[str] = ""

class ActualizarStockPrecio(BaseModel):
    precio: Optional[float] = None
    stock: Optional[int] = None

# --- VISTAS HTML ---

@app.get("/", response_class=HTMLResponse)
async def serve_catalog():
    """Sirve la página web del catálogo para clientes."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Catálogo de Farmacia - En construcción</h1>")

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    """Sirve el panel de administración / mostrador para el farmacéutico."""
    admin_file = STATIC_DIR / "admin.html"
    if admin_file.exists():
        return HTMLResponse(content=admin_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Panel Administrador - En construcción</h1>")

@app.get("/drogueria", response_class=HTMLResponse)
@app.get("/b2b", response_class=HTMLResponse)
async def serve_drogueria():
    """Sirve el portal B2B de droguería y laboratorio para farmacias asociadas."""
    drogueria_file = STATIC_DIR / "drogueria.html"
    if drogueria_file.exists():
        return HTMLResponse(content=drogueria_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Portal Droguería & Farmacias - En construcción</h1>")

# --- ENDPOINTS B2B (DROGUERÍA / FARMACIAS) ---

@app.get("/api/drogueria/productos")
async def listar_productos_b2b(rubro: Optional[str] = None):
    """Lista los productos mayoristas elaborados por la droguería de Farmacia Torres."""
    prods = load_medicamentos_b2b()
    if rubro and rubro.lower() != "todos":
        prods = [p for p in prods if p.get("rubro", "").lower() == rubro.lower()]
    return prods

@app.get("/api/drogueria/pedidos")
async def listar_pedidos_b2b():
    """Lista las órdenes de compra B2B de farmacias."""
    return load_pedidos_b2b()

@app.post("/api/drogueria/pedidos")
async def crear_pedido_b2b(pedido: PedidoB2BRequest):
    """Registra una orden de compra B2B entre farmacias y genera el remito comercial."""
    prods = {p["id"]: p for p in load_medicamentos_b2b()}
    pedido_id = f"B2B-{random.randint(1000, 9999)}"
    
    lineas_msg = []
    total_bruto = 0.0
    items_detalle = []
    requiere_frio_global = False
    
    for it in pedido.items:
        prod = prods.get(it.id)
        if not prod:
            continue
        subtotal = prod["precio_mayorista"] * it.cantidad
        total_bruto += subtotal
        if prod.get("requiere_frio"):
            requiere_frio_global = True
            
        lineas_msg.append(
            f"• *{prod['nombre']}* ({prod['rubro']})\n"
            f"  Cant: {it.cantidad} lotes | Lote: {prod.get('lote','S/D')} | Subtotal: ${subtotal:,.0f}"
        )
        items_detalle.append({
            "id": prod["id"],
            "nombre": prod["nombre"],
            "rubro": prod["rubro"],
            "lote": prod.get("lote"),
            "cantidad": it.cantidad,
            "precio_unitario": prod["precio_mayorista"],
            "subtotal": subtotal,
            "requiere_frio": prod.get("requiere_frio", False)
        })
        
    nuevo_pedido = {
        "id": pedido_id,
        "farmacia_nombre": pedido.farmacia_nombre,
        "cuit": pedido.cuit,
        "director_tecnico": pedido.director_tecnico,
        "telefono": pedido.telefono,
        "direccion": pedido.direccion,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "estado": "pendiente_aprobacion",
        "requiere_frio": requiere_frio_global,
        "items": items_detalle,
        "total_mayorista": total_bruto,
        "observaciones": pedido.observaciones
    }
    
    pedidos = load_pedidos_b2b()
    pedidos.append(nuevo_pedido)
    save_pedidos_b2b(pedidos)
    
    # Formatear remito/mensaje WhatsApp inter-farmacias
    msg_wa = (
        f"🏢 *ORDEN DE COMPRA B2B - DROGUERÍA FARMACIA TORRES* (#{pedido_id})\n\n"
        f"🏥 *Farmacia Solicitante:* {pedido.farmacia_nombre}\n"
        f"📄 *CUIT:* {pedido.cuit}\n"
        f"👨‍⚕️ *Director Técnico:* {pedido.director_tecnico}\n"
        f"📱 *Tel:* {pedido.telefono}\n"
    )
    if pedido.direccion:
        msg_wa += f"📍 *Entrega:* {pedido.direccion}\n"
        
    msg_wa += "\n📦 *Detalle de Lotes Solicitados:*\n" + "\n".join(lineas_msg)
    msg_wa += f"\n\n💰 *Total Mayorista Estimado:* *${total_bruto:,.0f}*"
    
    if requiere_frio_global:
        msg_wa += "\n\n❄️ *Aviso Logístico:* Incluye preparados con *CADENA DE FRÍO (2°C - 8°C)*. Se despachará con conservadora y control de temperatura."
        
    if pedido.observaciones:
        msg_wa += f"\n\n📝 *Observaciones:* {pedido.observaciones}"
        
    return {
        "pedido_id": pedido_id,
        "total_mayorista": total_bruto,
        "requiere_frio": requiere_frio_global,
        "mensaje_whatsapp": msg_wa
    }

# --- ENDPOINTS MEDICAMENTOS ---

@app.get("/api/medicamentos")
async def listar_medicamentos(categoria: Optional[str] = None, solo_genericos: bool = False):
    meds = load_medicamentos()
    if solo_genericos:
        meds = [m for m in meds if m.get("es_generico") is True]
    if categoria and categoria.lower() != "todas":
        meds = [m for m in meds if m.get("categoria", "").lower() == categoria.lower()]
    return meds

STOPWORDS_MEDICAMENTOS = {
    "hola", "buenas", "buen dia", "buenas tardes", "buenas noches",
    "menu", "menú", "inicio", "ayuda", "si", "sí", "no", "ok", "gracias",
    "muchas gracias", "chau", "adios", "adiós", "hasta luego",
    "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "cancelar", "farmacia", "pedido", "orden"
}

@app.get("/api/medicamentos/buscar")
async def buscar_medicamentos(q: str = Query(..., min_length=2), solo_genericos: bool = False):
    meds = load_medicamentos()
    q_clean = q.lower().strip()
    
    # Si la consulta es una palabra conversacional común, no buscar como medicamento
    if q_clean in STOPWORDS_MEDICAMENTOS:
        return []

    # Si la consulta explícita es 'generico' o 'genericos'
    busca_genericos_explicito = "generico" in q_clean or "genericos" in q_clean
    if busca_genericos_explicito:
        solo_genericos = True
        q_clean = q_clean.replace("generico", "").replace("genericos", "").strip()

    resultados = []

    for med in meds:
        if solo_genericos and not med.get("es_generico"):
            continue

        texto_busqueda = f"{med['nombre_comercial']} {med['principio_activo']} {med.get('concentracion', '')} {med['categoria']} {med.get('indicacion', '')}".lower()
        
        if not q_clean:  # Si solo buscaba "genericos"
            score = 100
        elif q_clean in texto_busqueda:
            score = 100
        else:
            # Para términos muy cortos (<=4 letras), evitar partial_ratio para no coincidir falsamente con subcadenas
            if len(q_clean) <= 4:
                score_nombre = fuzz.ratio(q_clean, med['nombre_comercial'].lower())
                score_droga = fuzz.ratio(q_clean, med['principio_activo'].lower())
                score = max(score_nombre, score_droga)
                if score < 70:
                    score = 0
            else:
                score_nombre = fuzz.partial_ratio(q_clean, med['nombre_comercial'].lower())
                score_droga = fuzz.partial_ratio(q_clean, med['principio_activo'].lower())
                score = max(score_nombre, score_droga)

        if score >= 55:
            item = med.copy()
            item["score_relevancia"] = score
            resultados.append(item)

    resultados.sort(key=lambda x: x["score_relevancia"], reverse=True)
    return resultados

@app.post("/api/medicamentos")
async def crear_medicamento(data: MedicamentoInput):
    meds = load_medicamentos()
    nuevo_id = f"MED-{len(meds) + 1:03d}"
    nuevo_med = {
        "id": nuevo_id,
        "nombre_comercial": data.nombre_comercial,
        "principio_activo": data.principio_activo,
        "presentacion": data.presentacion,
        "laboratorio": data.laboratorio,
        "precio": data.precio,
        "stock": data.stock,
        "requiere_receta": data.requiere_receta,
        "categoria": data.categoria,
        "indicacion": data.indicacion or ""
    }
    meds.append(nuevo_med)
    save_medicamentos(meds)
    return nuevo_med

@app.patch("/api/medicamentos/{med_id}")
async def actualizar_medicamento(med_id: str, data: ActualizarStockPrecio):
    meds = load_medicamentos()
    encontrado = False
    for m in meds:
        if m["id"] == med_id:
            if data.precio is not None:
                m["precio"] = data.precio
            if data.stock is not None:
                m["stock"] = data.stock
            encontrado = True
            break
    if not encontrado:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")
    save_medicamentos(meds)
    return {"status": "updated", "id": med_id}

@app.delete("/api/medicamentos/{med_id}")
async def eliminar_medicamento(med_id: str):
    meds = load_medicamentos()
    nuevos_meds = [m for m in meds if m["id"] != med_id]
    if len(nuevos_meds) == len(meds):
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")
    save_medicamentos(nuevos_meds)
    return {"status": "deleted", "id": med_id}

# --- ENDPOINTS PEDIDOS ---

@app.get("/api/pedidos")
async def listar_pedidos():
    """Devuelve todos los pedidos ordenados del más reciente al más antiguo."""
    pedidos = load_pedidos()
    return list(reversed(pedidos))

@app.post("/api/pedidos/crear")
async def crear_pedido(pedido: PedidoRequest):
    """
    Registra el pedido, aplica cobertura de Obra Social si corresponde
    y genera el mensaje oficial formateado para WhatsApp.
    """
    meds = {m["id"]: m for m in load_medicamentos()}
    total_bruto = 0.0
    descuento_obra_social = 0.0
    items_procesados = []
    lineas_msg = []
    requiere_receta_global = False

    pct_desc = max(0, min(100, pedido.descuento_pct or 0))

    for item in pedido.items:
        med = meds.get(item.id)
        if not med:
            continue
        subtotal = med["precio"] * item.cantidad
        total_bruto += subtotal
        
        # Descuento de obra social aplica principalmente a medicamentos bajo receta o cobertura general
        subtotal_desc = 0.0
        if med.get("requiere_receta") and pct_desc > 0:
            subtotal_desc = subtotal * (pct_desc / 100.0)
            descuento_obra_social += subtotal_desc

        if med.get("requiere_receta"):
            requiere_receta_global = True

        aviso_receta = " ⚠️ *(Bajo receta)*" if med.get("requiere_receta") else ""
        lineas_msg.append(f"• {item.cantidad}x {med['nombre_comercial']} (${med['precio']:,.0f}) = *${subtotal:,.0f}*{aviso_receta}")
        
        items_procesados.append({
            "id": med["id"],
            "nombre": med["nombre_comercial"],
            "cantidad": item.cantidad,
            "precio_unitario": med["precio"],
            "subtotal": subtotal,
            "requiere_receta": med.get("requiere_receta", False)
        })

    if not items_procesados:
        raise HTTPException(status_code=400, detail="No se seleccionaron medicamentos válidos.")

    total_final = max(0.0, total_bruto - descuento_obra_social)
    pedido_id = f"PED-{random.randint(1000, 9999)}"
    ahora_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    nuevo_pedido = {
        "id": pedido_id,
        "cliente_nombre": pedido.cliente_nombre or "Cliente",
        "cliente_telefono": pedido.cliente_telefono or "",
        "fecha": ahora_str,
        "estado": "pendiente",
        "obra_social": pedido.obra_social or "Particular",
        "requiere_receta": requiere_receta_global,
        "items": items_procesados,
        "total_bruto": total_bruto,
        "descuento_obra_social": descuento_obra_social,
        "total_final": total_final,
        "observaciones": pedido.observaciones or ""
    }

    # Guardar en archivo persistente
    pedidos = load_pedidos()
    pedidos.append(nuevo_pedido)
    save_pedidos(pedidos)

    # Formatear mensaje para WhatsApp
    msg_wa = (
        f"👋 *Nuevo Pedido en Farmacia Torres* (#{pedido_id})\n\n"
        f"👤 *Cliente:* {pedido.cliente_nombre}\n"
    )
    if pedido.cliente_telefono:
        msg_wa += f"📱 *Teléfono:* {pedido.cliente_telefono}\n"
    
    if pedido.obra_social and "Particular" not in pedido.obra_social:
        msg_wa += f"🏥 *Obra Social:* {pedido.obra_social}\n"

    msg_wa += "\n📦 *Medicamentos solicitados:*\n" + "\n".join(lineas_msg)
    
    if descuento_obra_social > 0:
        msg_wa += f"\n\nSubtotal: ${total_bruto:,.0f}"
        msg_wa += f"\nDescuento Obra Social ({pct_desc}%): -${descuento_obra_social:,.0f}"
    
    msg_wa += f"\n\n💰 *Total a abonar:* *${total_final:,.0f}*"

    if requiere_receta_global:
        msg_wa += "\n\n⚠️ *Aviso Importante:* Este pedido contiene medicamentos *bajo receta*. Por favor, envía la foto de la receta médica a este mismo chat para prepararlo."

    if pedido.observaciones:
        msg_wa += f"\n\n📝 *Nota:* {pedido.observaciones}"

    return {
        "pedido_id": pedido_id,
        "total_bruto": total_bruto,
        "descuento_obra_social": descuento_obra_social,
        "total_final": total_final,
        "requiere_receta": requiere_receta_global,
        "mensaje_whatsapp": msg_wa
    }

@app.patch("/api/pedidos/{pedido_id}/estado")
async def actualizar_estado_pedido(pedido_id: str, data: ActualizarEstadoRequest):
    pedidos = load_pedidos()
    encontrado = None
    for p in pedidos:
        if p["id"] == pedido_id:
            p["estado"] = data.estado
            encontrado = p
            break
    if not encontrado:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    save_pedidos(pedidos)

    # Mensaje sugerido para avisar al cliente por WhatsApp
    mensaje_notificacion = ""
    if data.estado == "listo":
        mensaje_notificacion = (
            f"👋 ¡Hola {encontrado['cliente_nombre']}! Te avisamos desde *Farmacia Torres* "
            f"que tu pedido *#{pedido_id}* ya está listo para retirar en mostrador. "
            f"Total a abonar: *${encontrado['total_final']:,.0f}*. ¡Te esperamos en Farmacia Torres!"
        )
    elif data.estado == "en_camino":
        mensaje_notificacion = (
            f"🛵 ¡Hola {encontrado['cliente_nombre']}! Tu pedido *#{pedido_id}* ya salió en camino con nuestro cadete. "
            f"Ten a mano el pago de *${encontrado['total_final']:,.0f}*. ¡Muchas gracias!"
        )

    return {
        "status": "updated",
        "pedido_id": pedido_id,
        "nuevo_estado": data.estado,
        "mensaje_notificacion": mensaje_notificacion,
        "cliente_telefono": encontrado.get("cliente_telefono", "")
    }

# --- MÁQUINA DE ESTADOS Y MOTOR CONVERSACIONAL DE CHATBOT ---

SINTOMAS_CATALOGO = {
    "1": {
        "titulo": "Dolor de Cabeza / Fiebre / Dolores Musculares",
        "sugeridos": ["Tafirol 1g", "Paracetamol 1g Genérico", "Ibupirac 400mg", "Ibuprofeno 400mg Genérico"]
    },
    "2": {
        "titulo": "Acidez / Malestar Estomacal / Gastritis",
        "sugeridos": ["Omeprazol 20mg Genérico", "Gastrotem 20mg"]
    },
    "3": {
        "titulo": "Gripe / Resfrío / Congestión",
        "sugeridos": ["Next Comprimidos", "Qura Plus", "Vitamina C 1g Efervescente Genérica"]
    },
    "4": {
        "titulo": "Alergias y Rinitis",
        "sugeridos": ["Loratadina 10mg Genérico", "Alermed Loratadina"]
    },
    "5": {
        "titulo": "Falta de Sueño / Insomnio / Estrés",
        "sugeridos": ["Melatol Plus Melatonina 3mg", "Melatonina 3mg Pura Genérica"]
    },
    "6": {
        "titulo": "Vitaminas / Cansancio y Defensas",
        "sugeridos": ["Redoxon Vitamina C 1g", "Total Magnesiano Vitalizante", "Magnesio Quelato 500mg Genérico"]
    }
}

SESIONES_CHAT: Dict[str, dict] = {}

def obtener_sesion(sender: str, push_name: str = "Cliente") -> dict:
    if sender not in SESIONES_CHAT:
        SESIONES_CHAT[sender] = {
            "estado": "INICIO",
            "nombre": push_name if push_name and push_name != "Cliente" else "Cliente",
            "telefono": sender.replace("@s.whatsapp.net", "").replace("+", "") if sender else "",
            "candidato_marca": None,
            "candidato_generico": None,
            "producto_elegido": None,
            "sugeridos_sintoma": [],
            "tipo_entrega": "Retiro en mostrador"
        }
    else:
        if push_name and push_name != "Cliente" and SESIONES_CHAT[sender].get("nombre") in ("Cliente", ""):
            SESIONES_CHAT[sender]["nombre"] = push_name
    return SESIONES_CHAT[sender]

async def realizar_busqueda_y_responder(sesion: dict, texto_busqueda: str) -> str:
    q_clean = texto_busqueda.lower().strip()
    if q_clean in STOPWORDS_MEDICAMENTOS or len(q_clean) < 2:
        sesion["estado"] = "MENU_PRINCIPAL"
        return (
            f"👋 *Bienvenido a Farmacia Torres.* 🏥\n\n"
            f"Por favor indica qué deseas hacer:\n\n"
            f"1️⃣ 🔍 Buscar un medicamento (por marca o droga)\n"
            f"2️⃣ 🤒 Consultar por síntomas o malestar\n"
            f"3️⃣ 📸 Enviar receta médica\n"
            f"4️⃣ 📍 Horarios, ubicación y envíos\n"
            f"5️⃣ 👨‍⚕️ Hablar con un farmacéutico\n\n"
            f"_Responde del 1 al 5 o escribe el nombre de lo que buscas._"
        )

    resultados = await buscar_medicamentos(q=texto_busqueda)
    if not resultados:
        sesion["estado"] = "BUSQUEDA_MEDICAMENTO"
        return (
            f"🔍 No pudimos encontrar medicamentos que coincidan con '*{texto_busqueda}*'.\n\n"
            f"¿Podrías verificar el nombre o consultar por el principio activo (ej: Paracetamol, Ibuprofeno)?\n\n"
            f"👉 También puedes ver nuestro catálogo completo aquí:\n{BASE_URL}\n\n"
            f"_O escribe 'menu' para volver al inicio._"
        )

    top = resultados[0]
    meds_todos = load_medicamentos()
    
    alternativa_generica = None
    if not top.get("es_generico"):
        genericos = [
            m for m in meds_todos
            if m.get("es_generico")
            and m.get("principio_activo", "").lower() == top.get("principio_activo", "").lower()
            and m.get("precio", 999999) < top.get("precio", 0)
        ]
        if genericos:
            alternativa_generica = genericos[0]

    if alternativa_generica:
        marca = top
        gen = alternativa_generica
        ahorro = marca["precio"] - gen["precio"]
        receta_txt = "⚠️ Requiere receta médica" if marca.get("requiere_receta") else "✅ Venta libre"

        sesion["estado"] = "SELECCION_GENERICO"
        sesion["candidato_marca"] = marca
        sesion["candidato_generico"] = gen

        return (
            f"💊 *{marca['nombre_comercial']}* (🏷️ Marca Líder)\n"
            f"   Droga: {marca['principio_activo']} ({marca.get('concentracion', '')})\n"
            f"   Laboratorio: {marca.get('laboratorio', 'Comercial')}\n"
            f"   Precio: *${marca['precio']:,.0f}* | Stock: {marca['stock']} unid.\n"
            f"   {receta_txt}\n\n"
            f"💡 *Opción Genérica de Ahorro Recomendada:*\n"
            f"• *{gen['nombre_comercial']}* ({gen.get('laboratorio', 'Klonal')})\n"
            f"  Misma droga y concentración por solo *${gen['precio']:,.0f}*\n"
            f"  👉 *¡Ahorras ${ahorro:,.0f} llevando la opción genérica!*\n\n"
            f"¿Cuál prefieres encargar?\n"
            f"1️⃣ 🟢 Opción Genérica de Ahorro (*${gen['precio']:,.0f}*)\n"
            f"2️⃣ 🏷️ Marca Líder (*${marca['precio']:,.0f}*)\n"
            f"3️⃣ 🔍 Buscar otro medicamento\n"
            f"4️⃣ 🏠 Volver al menú principal\n\n"
            f"_Responde con el número de opción (1 al 4)._"
        )
    else:
        med = top
        receta_txt = "⚠️ Requiere receta médica" if med.get("requiere_receta") else "✅ Venta libre"
        tipo_txt = "🟢 Genérico Económico" if med.get("es_generico") else "🏷️ Marca Comercial"

        sesion["estado"] = "CONFIRMAR_ENCARGO_DIRECTO"
        sesion["producto_elegido"] = med

        return (
            f"💊 *{med['nombre_comercial']}* ({tipo_txt})\n"
            f"   Droga: {med['principio_activo']} ({med.get('concentracion', '')})\n"
            f"   Laboratorio: {med.get('laboratorio', 'Nacional')}\n"
            f"   Precio: *${med['precio']:,.0f}* | Stock: {med['stock']} unid.\n"
            f"   {receta_txt}\n\n"
            f"¿Deseas encargar este producto?\n"
            f"1️⃣ ✅ Sí, encargar ahora\n"
            f"2️⃣ 🔍 Buscar otro medicamento\n"
            f"3️⃣ 🏠 Volver al menú principal\n\n"
            f"_Responde con 1, 2 o 3._"
        )

async def procesar_mensaje_chatbot(sender: str, texto_usuario: str, push_name: str = "Cliente") -> str:
    sesion = obtener_sesion(sender, push_name)
    nombre = sesion.get("nombre", "Cliente")
    texto_raw = texto_usuario.strip()
    texto_lower = texto_raw.lower()

    # 1. Reset / Saludos / Menú
    es_saludo = any(s in texto_lower for s in ["hola", "buenas", "buen dia", "buen día", "buenas tardes", "buenas noches", "inicio", "empezar"])
    es_menu = texto_lower in ["menu", "menú", "volver", "reiniciar", "opciones"]
    
    if es_saludo or es_menu or (sesion["estado"] == "INICIO" and texto_lower in STOPWORDS_MEDICAMENTOS):
        sesion["estado"] = "MENU_PRINCIPAL"
        sesion["producto_elegido"] = None
        sesion["candidato_marca"] = None
        sesion["candidato_generico"] = None
        return (
            f"👋 *¡Hola {nombre}! Bienvenido a Farmacia Torres.* 🏥\n\n"
            f"¿En qué te podemos ayudar hoy?\n\n"
            f"1️⃣ 🔍 *Buscar un medicamento* (precios, stock y genéricos)\n"
            f"2️⃣ 🤒 *Consultar por síntoma o malestar*\n"
            f"3️⃣ 📸 *Enviar receta médica*\n"
            f"4️⃣ 📍 *Horarios, ubicación y formas de pago*\n"
            f"5️⃣ 👨‍⚕️ *Hablar con un profesional farmacéutico*\n\n"
            f"_Responde con el número de opción (1 al 5) o escribe directamente lo que buscas._"
        )

    # Agradecimiento / Despedida
    if any(s == texto_lower or texto_lower.startswith(s) for s in ["gracias", "muchas gracias", "chau", "adios", "adiós", "hasta luego"]):
        sesion["estado"] = "INICIO"
        return f"🙏 ¡De nada, {nombre}! Un placer atenderte en *Farmacia Torres*. Quedamos a tu disposición para cuando nos necesites. ¡Que tengas un excelente día! 🌿"

    estado = sesion.get("estado", "INICIO")

    # --- ESTADO: MENU_PRINCIPAL ---
    if estado == "MENU_PRINCIPAL":
        if texto_lower in ["1", "buscar", "precio", "stock"]:
            sesion["estado"] = "BUSQUEDA_MEDICAMENTO"
            return (
                f"🔍 *Búsqueda de Medicamentos*\n\n"
                f"Por favor, escribe el nombre comercial o la droga que estás buscando (ej: *Tafirol*, *Ibuprofeno*, *Amoxidal*, *Vitamina C*).\n\n"
                f"_O escribe 'menu' para volver._"
            )
        elif texto_lower in ["2", "sintoma", "sintomas", "malestar"]:
            sesion["estado"] = "MENU_SINTOMAS"
            return (
                f"🤒 *¿Qué síntoma o malestar deseas tratar?*\n\n"
                f"1️⃣ Dolor de cabeza o muscular / Fiebre\n"
                f"2️⃣ Acidez o dolor de panza\n"
                f"3️⃣ Gripe, resfrío o dolor de garganta\n"
                f"4️⃣ Alergias y congestión\n"
                f"5️⃣ Dificultad para dormir / Estrés\n"
                f"6️⃣ Vitaminas y defensas\n\n"
                f"_Responde con el número (1 al 6) o escribe 'menu' para volver._"
            )
        elif texto_lower in ["3", "receta", "orden"]:
            return (
                f"📸 *Envío y Validación de Receta Médica*\n\n"
                f"Envíanos la foto clara de tu orden médica por este chat.\n"
                f"Nuestro farmacéutico verificará la cobertura de tu obra social y dosis indicada.\n\n"
                f"👉 También puedes ver nuestro catálogo completo aquí:\n{BASE_URL}\n\n"
                f"_Escribe 'menu' para volver al menú principal._"
            )
        elif texto_lower in ["4", "horario", "horarios", "ubicacion", "ubicación", "direccion", "dirección", "donde"]:
            return (
                f"📍 *Farmacia Torres - Casa Central*\n"
                f"Av. San Martín 1420 (frente a la plaza central)\n\n"
                f"⏰ *Horarios:* Lunes a Sábados de 8:30 a 21:00 hs (Atendemos urgencias de turno).\n"
                f"🛵 *Envíos a domicilio:* Sí, dentro del radio urbano.\n"
                f"💳 *Medios de pago:* Efectivo, Débito, Transferencia y Obras Sociales.\n\n"
                f"_Escribe 'menu' para realizar un pedido o consulta._"
            )
        elif texto_lower in ["5", "farmaceutico", "farmacéutico", "humano", "persona"]:
            sesion["estado"] = "INICIO"
            return (
                f"👨‍⚕️ *Derivando a un profesional farmacéutico de Farmacia Torres...*\n\n"
                f"Hemos notificado a nuestro equipo de mostrador. En breve un profesional te responderá por este mismo chat para asesorarte.\n\n"
                f"_Escribe 'menu' si deseas realizar otra consulta mientras tanto._"
            )
        else:
            return await realizar_busqueda_y_responder(sesion, texto_raw)

    # --- ESTADO: BUSQUEDA_MEDICAMENTO ---
    elif estado == "BUSQUEDA_MEDICAMENTO":
        return await realizar_busqueda_y_responder(sesion, texto_raw)

    # --- ESTADO: MENU_SINTOMAS ---
    elif estado == "MENU_SINTOMAS":
        if texto_lower in SINTOMAS_CATALOGO:
            sint = SINTOMAS_CATALOGO[texto_lower]
            meds_todos = load_medicamentos()
            encontrados = []
            for nom in sint["sugeridos"]:
                for m in meds_todos:
                    if nom.lower() in m["nombre_comercial"].lower():
                        if m not in encontrados:
                            encontrados.append(m)
                            break
            
            if encontrados:
                sesion["estado"] = "SELECCION_MEDICAMENTO_SINTOMA"
                sesion["sugeridos_sintoma"] = encontrados
                lineas = []
                for idx, m in enumerate(encontrados, 1):
                    tipo_txt = "🟢 Genérico Ahorro" if m.get("es_generico") else "🏷️ Marca"
                    lineas.append(f"{idx}️⃣ *{m['nombre_comercial']}* (${m['precio']:,.0f}) - {tipo_txt}")
                
                return (
                    f"🩺 *Opciones de venta libre para {sint['titulo']}:*\n\n" +
                    "\n".join(lineas) +
                    f"\n\n_Escribe el número del producto que deseas encargar (ej: 1) o 'menu' para volver._"
                )
            else:
                return "No encontramos productos disponibles para ese síntoma en este momento. Escribe 'menu' para volver."
        else:
            return "Opción no válida. Por favor responde del 1 al 6 o escribe 'menu' para volver."

    # --- ESTADO: SELECCION_MEDICAMENTO_SINTOMA ---
    elif estado == "SELECCION_MEDICAMENTO_SINTOMA":
        sugeridos = sesion.get("sugeridos_sintoma", [])
        if texto_lower.isdigit() and 1 <= int(texto_lower) <= len(sugeridos):
            elegido = sugeridos[int(texto_lower) - 1]
            sesion["producto_elegido"] = elegido
            sesion["estado"] = "SELECCION_ENTREGA"
            return (
                f"📦 Has seleccionado: *{elegido['nombre_comercial']}* (${elegido['precio']:,.0f}).\n\n"
                f"¿Cómo deseas recibir tu pedido?\n"
                f"1️⃣ Retiro en Mostrador (Av. San Martín 1420)\n"
                f"2️⃣ Envío a Domicilio\n"
                f"3️⃣ Cancelar y volver al menú\n\n"
                f"_Responde con 1, 2 o 3._"
            )
        else:
            return f"Por favor elige una opción del 1 al {len(sugeridos)} o escribe 'menu' para volver."

    # --- ESTADO: SELECCION_GENERICO ---
    elif estado == "SELECCION_GENERICO":
        marca = sesion.get("candidato_marca")
        gen = sesion.get("candidato_generico")
        
        if texto_lower in ["1", "generico", "genérico", "ahorro", "economico", "económico"]:
            sesion["producto_elegido"] = gen
            sesion["estado"] = "SELECCION_ENTREGA"
            return (
                f"✅ *Excelente elección de ahorro.*\n"
                f"Vas a encargar: *{gen['nombre_comercial']}* por *${gen['precio']:,.0f}*.\n\n"
                f"¿Cómo deseas recibir tu pedido?\n"
                f"1️⃣ Retiro en Mostrador (Av. San Martín 1420)\n"
                f"2️⃣ Envío a Domicilio\n"
                f"3️⃣ Cancelar y volver al menú\n\n"
                f"_Responde con 1, 2 o 3._"
            )
        elif texto_lower in ["2", "marca", "lider", "líder", "original"]:
            sesion["producto_elegido"] = marca
            sesion["estado"] = "SELECCION_ENTREGA"
            return (
                f"🏷️ Vas a encargar la marca líder: *{marca['nombre_comercial']}* por *${marca['precio']:,.0f}*.\n\n"
                f"¿Cómo deseas recibir tu pedido?\n"
                f"1️⃣ Retiro en Mostrador (Av. San Martín 1420)\n"
                f"2️⃣ Envío a Domicilio\n"
                f"3️⃣ Cancelar y volver al menú\n\n"
                f"_Responde con 1, 2 o 3._"
            )
        elif texto_lower in ["3", "buscar", "otro"]:
            sesion["estado"] = "BUSQUEDA_MEDICAMENTO"
            return "🔍 Escribe el nombre del otro medicamento que deseas consultar:"
        elif texto_lower in ["4", "cancelar", "menu"]:
            sesion["estado"] = "MENU_PRINCIPAL"
            return "Operación cancelada. Escribe 'menu' para ver las opciones disponibles."
        else:
            return "Por favor responde *1* para la opción genérica económica o *2* para la marca líder (o 'menu' para salir)."

    # --- ESTADO: CONFIRMAR_ENCARGO_DIRECTO ---
    elif estado == "CONFIRMAR_ENCARGO_DIRECTO":
        elegido = sesion.get("producto_elegido")
        if texto_lower in ["1", "si", "sí", "encargar", "pedir", "comprar", "quiero"]:
            sesion["estado"] = "SELECCION_ENTREGA"
            return (
                f"📦 Vas a encargar: *{elegido['nombre_comercial']}* (${elegido['precio']:,.0f}).\n\n"
                f"¿Cómo deseas recibir tu pedido?\n"
                f"1️⃣ Retiro en Mostrador (Av. San Martín 1420)\n"
                f"2️⃣ Envío a Domicilio\n"
                f"3️⃣ Cancelar y volver al menú\n\n"
                f"_Responde con 1, 2 o 3._"
            )
        elif texto_lower in ["2", "buscar", "otro"]:
            sesion["estado"] = "BUSQUEDA_MEDICAMENTO"
            return "🔍 Escribe el nombre del otro medicamento que buscas:"
        else:
            sesion["estado"] = "MENU_PRINCIPAL"
            return "Operación finalizada. Escribe 'menu' para volver a comenzar."

    # --- ESTADO: SELECCION_ENTREGA ---
    elif estado == "SELECCION_ENTREGA":
        if texto_lower in ["1", "retiro", "mostrador", "sucursal"]:
            sesion["tipo_entrega"] = "Retiro en mostrador"
        elif texto_lower in ["2", "envio", "envío", "domicilio", "delivery"]:
            sesion["tipo_entrega"] = "Envío a domicilio"
        elif texto_lower in ["3", "cancelar"]:
            sesion["estado"] = "MENU_PRINCIPAL"
            return "Pedido cancelado. Escribe 'menu' para volver a empezar."
        else:
            sesion["tipo_entrega"] = "Retiro en mostrador"

        sesion["estado"] = "SELECCION_OBRA_SOCIAL"
        return (
            f"🏥 *¿Tenés Obra Social o Prepaga para aplicar cobertura?*\n\n"
            f"1️⃣ Particular (Sin cobertura)\n"
            f"2️⃣ PAMI (50% de cobertura)\n"
            f"3️⃣ OSDE (40% de cobertura)\n"
            f"4️⃣ Swiss Medical (40% de cobertura)\n"
            f"5️⃣ Otra Obra Social (20% orientativo)\n\n"
            f"_Responde con el número (1 al 5) o escribe el nombre de tu obra social._"
        )

    # --- ESTADO: SELECCION_OBRA_SOCIAL (CIERRE TRANSACCIONAL EN BACKEND) ---
    elif estado == "SELECCION_OBRA_SOCIAL":
        os_map = {
            "1": ("Particular (Sin cobertura)", 0),
            "2": ("PAMI", 50),
            "3": ("OSDE", 40),
            "4": ("Swiss Medical", 40),
            "5": ("Otra Obra Social", 20)
        }
        
        if texto_lower in os_map:
            os_nombre, pct_desc = os_map[texto_lower]
        elif "pami" in texto_lower:
            os_nombre, pct_desc = "PAMI", 50
        elif "osde" in texto_lower:
            os_nombre, pct_desc = "OSDE", 40
        elif "swiss" in texto_lower:
            os_nombre, pct_desc = "Swiss Medical", 40
        elif "particular" in texto_lower or "ninguna" in texto_lower or "no" in texto_lower:
            os_nombre, pct_desc = "Particular (Sin cobertura)", 0
        else:
            os_nombre, pct_desc = texto_raw.capitalize(), 20

        elegido = sesion.get("producto_elegido")
        if not elegido:
            sesion["estado"] = "MENU_PRINCIPAL"
            return "Hubo un error al recuperar el producto. Por favor escribe 'menu' para iniciar nuevamente."

        total_bruto = float(elegido["precio"])
        descuento = 0.0
        if pct_desc > 0:
            descuento = total_bruto * (pct_desc / 100.0)
        total_final = max(0.0, total_bruto - descuento)

        pedido_id = f"PED-{random.randint(1000, 9999)}"
        ahora_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        nuevo_pedido = {
            "id": pedido_id,
            "cliente_nombre": nombre,
            "cliente_telefono": sesion.get("telefono") or "WhatsApp",
            "fecha": ahora_str,
            "estado": "pendiente",
            "obra_social": os_nombre,
            "requiere_receta": bool(elegido.get("requiere_receta", False)),
            "items": [{
                "id": elegido["id"],
                "nombre": elegido["nombre_comercial"],
                "cantidad": 1,
                "precio_unitario": elegido["precio"],
                "subtotal": total_bruto,
                "requiere_receta": bool(elegido.get("requiere_receta", False))
            }],
            "total_bruto": total_bruto,
            "descuento_obra_social": descuento,
            "total_final": total_final,
            "observaciones": f"Generado vía Bot WhatsApp ({sesion.get('tipo_entrega', 'Mostrador')})"
        }

        # Guardar en data/pedidos.json (impacta inmediatamente en panel /admin)
        pedidos = load_pedidos()
        pedidos.append(nuevo_pedido)
        save_pedidos(pedidos)

        # Resetear sesión para futuras consultas
        sesion["estado"] = "MENU_PRINCIPAL"
        sesion["producto_elegido"] = None

        aviso_receta = "\n⚠️ *Recordatorio:* Este medicamento requiere receta médica. Por favor preséntala al retirar o envía la foto por este chat." if elegido.get("requiere_receta") else ""
        linea_desc = f"\nDescuento {os_nombre} ({pct_desc}%): -${descuento:,.0f}" if descuento > 0 else ""

        return (
            f"🎉 *¡Pedido #{pedido_id} Confirmado en Farmacia Torres!* 📦\n\n"
            f"👤 *Cliente:* {nombre}\n"
            f"💊 *Medicamento:* 1x {elegido['nombre_comercial']}\n"
            f"🏥 *Cobertura:* {os_nombre}\n"
            f"💰 *Total a abonar:* *${total_final:,.0f}*{linea_desc}\n"
            f"📍 *Modalidad:* {sesion.get('tipo_entrega', 'Retiro en mostrador')}\n"
            f"{aviso_receta}\n\n"
            f"👨‍⚕️ *El equipo de mostrador ya tiene tu orden en el sistema y la está preparando.* "
            f"Te notificaremos cuando esté lista.\n\n"
            f"_¿Deseas consultar algo más? Escribe 'menu' en cualquier momento._"
        )

    else:
        return await realizar_busqueda_y_responder(sesion, texto_raw)

# --- WEBHOOK WHATSAPP ---

@app.post("/api/webhook/whatsapp")
async def webhook_whatsapp(payload: dict):
    try:
        data = payload.get("data", {})
        message = data.get("message", {})
        sender = data.get("key", {}).get("remoteJid", "5491112345678@s.whatsapp.net")
        push_name = data.get("pushName") or payload.get("pushName") or "Cliente"
        
        texto_usuario = (
            message.get("conversation") or 
            message.get("extendedTextMessage", {}).get("text") or 
            ""
        ).strip()

        if not texto_usuario:
            return {"status": "ignored", "reason": "No text content"}

        respuesta = await procesar_mensaje_chatbot(sender, texto_usuario, push_name)

        return {
            "status": "success",
            "sender": sender,
            "query": texto_usuario,
            "response_text": respuesta
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
