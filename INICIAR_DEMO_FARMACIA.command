#!/bin/bash
# Script de inicio rápido para Farmacia WhatsApp Bot & Catálogo
cd "$(dirname "$0")"
echo "=========================================================="
echo "🏥 Iniciando Servidor de Farmacia, Bot & Catálogo Web..."
echo "=========================================================="
echo "Abriendo en http://localhost:8000 ..."
sleep 1
open "http://localhost:8000"
python3 server.py
