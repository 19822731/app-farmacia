import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional
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

@app.get("/api/medicamentos/buscar")
async def buscar_medicamentos(q: str = Query(..., min_length=2), solo_genericos: bool = False):
    meds = load_medicamentos()
    q_clean = q.lower().strip()
    
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

# --- WEBHOOK WHATSAPP ---

@app.post("/api/webhook/whatsapp")
async def webhook_whatsapp(payload: dict):
    try:
        data = payload.get("data", {})
        message = data.get("message", {})
        sender = data.get("key", {}).get("remoteJid", "")
        
        texto_usuario = (
            message.get("conversation") or 
            message.get("extendedTextMessage", {}).get("text") or 
            ""
        ).strip()

        if not texto_usuario:
            return {"status": "ignored", "reason": "No text content"}

        resultados = await buscar_medicamentos(q=texto_usuario)
        
        if not resultados:
            respuesta = (
                f"No pudimos encontrar medicamentos que coincidan con '{texto_usuario}'.\n"
                f"¿Podrías verificar el nombre o consultar por el principio activo (ej. Paracetamol, Ibuprofeno)?\n"
                f"También puedes ver nuestro catálogo completo aquí: http://localhost:8000"
            )
        else:
            top_3 = resultados[:3]
            lineas = []
            alternativa_generica = None
            meds_todos = load_medicamentos()

            for r in top_3:
                receta_txt = "⚠️ Requiere receta" if r.get("requiere_receta") else "✅ Venta libre"
                tipo_txt = "🟢 Genérico Económico" if r.get("es_generico") else "🏷️ Marca Líder"
                lineas.append(
                    f"💊 *{r['nombre_comercial']}* ({tipo_txt})\n"
                    f"   Droga: {r['principio_activo']} ({r.get('concentracion', '')})\n"
                    f"   Laboratorio: {r.get('laboratorio', 'Nacional')}\n"
                    f"   Precio: *${r['precio']:,.0f}* | Stock: {r['stock']} unid.\n"
                    f"   {receta_txt}"
                )

                # Si el producto consultado es de marca líder, buscar si tenemos el genérico equivalente más económico
                if not r.get("es_generico") and not alternativa_generica:
                    genericos_equivalentes = [
                        m for m in meds_todos
                        if m.get("es_generico")
                        and m.get("principio_activo", "").lower() == r.get("principio_activo", "").lower()
                        and m.get("precio", 999999) < r.get("precio", 0)
                    ]
                    if genericos_equivalentes:
                        alternativa_generica = (r, genericos_equivalentes[0])

            respuesta = f"🔍 *Resultados para '{texto_usuario}':*\n\n" + "\n\n".join(lineas)

            if alternativa_generica:
                marca, gen = alternativa_generica
                ahorro = marca["precio"] - gen["precio"]
                respuesta += (
                    f"\n\n💡 *Opción Genérica de Ahorro Recomendada:*\n"
                    f"• *{gen['nombre_comercial']}* ({gen.get('laboratorio', 'Klonal')})\n"
                    f"  Misma droga ({gen['principio_activo']}) por solo *${gen['precio']:,.0f}*\n"
                    f"  👉 *¡Ahorras ${ahorro:,.0f} llevando la opción genérica!*"
                )

            respuesta += "\n\n¿Deseas encargar la opción genérica económica o la marca líder?"

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
