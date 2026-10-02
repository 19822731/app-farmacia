#!/usr/bin/env python3
"""
Script de descarga y optimización de imágenes oficiales para el catálogo de Farmacia Torres.
Descarga fotos reales en alta definición de cada producto y las optimiza a formato WebP ultraliviano.
"""

import os
import sys
import json
import io
import shutil
import urllib.request
from PIL import Image, ImageDraw, ImageFont

# Mapeo oficial de imágenes reales por ID de medicamento
IMAGE_SOURCES = {
    "MED-001": "https://farmacityar.vteximg.com.br/arquivos/ids/269191/127358_tafirol-1g.jpg",
    "MED-002": "https://farmacityar.vteximg.com.br/arquivos/ids/278553/232997_paracetamol.jpg",
    "MED-003": "https://farmacityar.vteximg.com.br/arquivos/ids/297459/144552_tafirol500.jpg",
    "MED-004": "https://farmacityar.vteximg.com.br/arquivos/ids/297420/229044_paracetamol500.jpg",
    "MED-005": "https://farmacityar.vteximg.com.br/arquivos/ids/265361/20219_ibupirac.jpg",
    "MED-006": "https://farmacityar.vteximg.com.br/arquivos/ids/297425/118794_ibu-600.jpg",
    "MED-007": "https://farmacityar.vteximg.com.br/arquivos/ids/276427/103866_actron-600.jpg",
    "MED-008": "https://farmacityar.vteximg.com.br/arquivos/ids/297421/240916_ibuprofeno400.jpg",
    "MED-009": "https://farmashop.vteximg.com.br/arquivos/ids/232474/41441_amoxidal-500-mg-16-comprimidos_01_default.jpg",
    "MED-010": "https://farmacityar.vteximg.com.br/arquivos/ids/265452/27443_clavulox-amoxi500.jpg",
    "MED-011": "https://farmashop.vteximg.com.br/arquivos/ids/232470/41444_amoxidal-duo-875-mg-14-comprimidos_01_default.jpg",
    "MED-012": "https://farmashop.vteximg.com.br/arquivos/ids/232470/41444_amoxidal-duo-875-mg-14-comprimidos_01_default.jpg",
    "MED-013": "https://farmacityar.vteximg.com.br/arquivos/ids/267781/105688_lotrial-10.jpg",
    "MED-014": "https://farmacityar.vteximg.com.br/arquivos/ids/273784/223444_enalapril.jpg",
    "MED-015": "https://farmacityar.vteximg.com.br/arquivos/ids/271728/144863_losacor-50.jpg",
    "MED-016": "https://farmacityar.vteximg.com.br/arquivos/ids/273449/203659_losartan.jpg",
    "MED-017": "https://farmacityar.vteximg.com.br/arquivos/ids/274991/32282_gastrotem-20.jpg",
    "MED-018": "https://farmacityar.vteximg.com.br/arquivos/ids/273293/144193_ulcozol-omeprazol.jpg",
    "MED-019": "https://farmacityar.vteximg.com.br/arquivos/ids/234250/136371_aerotina.jpg",
    "MED-020": "https://farmacityar.vteximg.com.br/arquivos/ids/273797/223453_loratadina.jpg",
    "MED-021": "https://farmacityar.vteximg.com.br/arquivos/ids/276119/37927_ventolin.jpg",
    "MED-022": "https://farmacityar.vteximg.com.br/arquivos/ids/271513/128098_salbutral.jpg",
    "MED-023": "https://farmacityar.vteximg.com.br/arquivos/ids/248695/237224_sertal-compuesto.jpg",
    "MED-024": "https://farmacityar.vteximg.com.br/arquivos/ids/295391/220120_alcohol-gel-250.jpg",
    "MED-025": "https://farmacityar.vteximg.com.br/arquivos/ids/275158/22956_redoxon.jpg",
    "MED-026": "https://farmacityar.vteximg.com.br/arquivos/ids/297426/229046_vitamina-c.jpg",
    "MED-027": "https://farmacityar.vteximg.com.br/arquivos/ids/279390/135681_total-magnesiano.jpg",
    "MED-028": "https://farmacityar.vteximg.com.br/arquivos/ids/267822/207038_magnesio-quelato.jpg",
    "MED-029": "https://farmacityar.vteximg.com.br/arquivos/ids/234239/133368_melatol-plus.jpg",
    "MED-030": "https://farmacityar.vteximg.com.br/arquivos/ids/263144/17448_melatonina.jpg"
}

def crear_imagen_fallback(med, destino_path):
    """Crea una imagen estilizada si falla la descarga."""
    size = (400, 400)
    img = Image.new("RGB", size, color=(248, 250, 252)) # slate-50
    draw = ImageDraw.Draw(img)
    
    # Fondo con borde redondeado simulado
    draw.rectangle([(10, 10), (390, 390)], outline=(226, 232, 240), width=2)
    
    # Cruz médica / icono farmacia estilizado
    cx, cy = 200, 160
    color_cruz = (5, 150, 105) if med.get("es_generico") else (15, 23, 42)
    draw.rectangle([(cx - 40, cy - 12), (cx + 40, cy + 12)], fill=color_cruz)
    draw.rectangle([(cx - 12, cy - 40), (cx + 12, cy + 40)], fill=color_cruz)
    
    # Textos de respaldo
    nombre = med.get("nombre_comercial", "")
    lab = med.get("laboratorio", "")
    draw.text((200, 240), nombre, fill=(30, 41, 59), anchor="mm")
    draw.text((200, 270), lab, fill=(100, 116, 139), anchor="mm")
    tipo = "Genérico Ahorro" if med.get("es_generico") else "Marca Líder"
    draw.text((200, 310), f"[{tipo}]", fill=color_cruz, anchor="mm")
    
    img.save(destino_path, format="WEBP", quality=85)

def procesar_imagen(bytes_data, destino_path):
    """Convierte a WebP centrado en lienzo cuadrado de 400x400 con fondo blanco."""
    img = Image.open(io.BytesIO(bytes_data))
    img = img.convert("RGBA")
    
    # Redimensionar proporcionalmente para que entre en 380x380
    img.thumbnail((380, 380), Image.Resampling.LANCZOS)
    
    # Crear lienzo blanco de 400x400
    canvas = Image.new("RGBA", (400, 400), (255, 255, 255, 255))
    offset = ((400 - img.width) // 2, (400 - img.height) // 2)
    canvas.paste(img, offset, img)
    
    # Guardar en WebP
    final_rgb = canvas.convert("RGB")
    final_rgb.save(destino_path, format="WEBP", quality=88, method=6)

def main():
    target_dir_static = "static/img/medicamentos"
    target_dir_public = "public/img/medicamentos"
    os.makedirs(target_dir_static, exist_ok=True)
    os.makedirs(target_dir_public, exist_ok=True)
    
    with open("data/medicamentos.json", "r", encoding="utf-8") as f:
        medicamentos = json.load(f)
        
    print(f"=== Procesando {len(medicamentos)} medicamentos ===")
    
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    
    actualizados = []
    for med in medicamentos:
        mid = med["id"]
        filename = f"{mid.lower()}.webp"
        path_static = os.path.join(target_dir_static, filename)
        path_public = os.path.join(target_dir_public, filename)
        
        url = IMAGE_SOURCES.get(mid)
        exito = False
        
        if url:
            try:
                print(f"[{mid}] Descargando: {med['nombre_comercial']}...")
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                    procesar_imagen(data, path_static)
                    shutil.copyfile(path_static, path_public)
                    exito = True
                    print(f"[{mid}] ✅ Guardado OK ({os.path.getsize(path_static)} bytes)")
            except Exception as e:
                print(f"[{mid}] ⚠️ Error en descarga ({e}). Generando fallback estilizado.")
        
        if not exito:
            crear_imagen_fallback(med, path_static)
            shutil.copyfile(path_static, path_public)
            print(f"[{mid}] 🛡️ Fallback generado ({os.path.getsize(path_static)} bytes)")
            
        med["imagen"] = f"/static/img/medicamentos/{filename}"
        actualizados.append(med)
        
    # Guardar archivos JSON actualizados
    for p in ["data/medicamentos.json", "static/data/medicamentos.json", "public/data/medicamentos.json"]:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(actualizados, f, ensure_ascii=False, indent=2)
        print(f"✅ Catálogo actualizado: {p}")
        
    print("=== PROCESAMIENTO COMPLETADO EXITOSAMENTE ===")

if __name__ == "__main__":
    main()
