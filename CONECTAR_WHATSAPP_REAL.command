#!/bin/bash
# ========================================================
# 🏥 Conectar Bot de WhatsApp Real - Farmacia Torres
# ========================================================

cd "$(dirname "$0")"

echo "=========================================================="
echo "🏥 INICIANDO SISTEMA DE FARMACIA TORRES Y BOT DE WHATSAPP..."
echo "=========================================================="

# 1. Verificar si el servidor Python (Catálogo & API) está corriendo
if ! lsof -i :8000 > /dev/null 2>&1; then
    echo "⚙️ Iniciando servidor de catálogo y búsqueda en segundo plano..."
    python3 server.py > /dev/null 2>&1 &
    sleep 2
    echo "✅ Servidor web disponible en http://localhost:8000"
else
    echo "✅ Servidor web ya está activo en http://localhost:8000"
fi

# 2. Iniciar el bot de WhatsApp con Baileys
echo "📱 Iniciando conexión con WhatsApp..."
echo "----------------------------------------------------------"
echo "Generando código QR... Prepárate para escanearlo con tu celular:"
echo "----------------------------------------------------------"

node whatsapp_bot.js
