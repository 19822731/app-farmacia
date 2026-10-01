/**
 * 🏥 WhatsApp Bot para Farmacia Torres
 * Conector nativo en Node.js usando Baileys (No requiere Docker)
 */

const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const pino = require('pino');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const net = require('net');
const { spawn } = require('child_process');

// Logger silencioso para que no ensucie la terminal
const logger = pino({ level: 'silent' });

// Ruta para guardar la sesión del WhatsApp
const AUTH_DIR = path.join(__dirname, 'auth_session');
const BACKEND_URL = 'http://127.0.0.1:8000/api/webhook/whatsapp';
const PUBLIC_URL = process.env.PUBLIC_URL || 'http://localhost:8000';
const MEDICAMENTOS_PATH = path.join(__dirname, 'data', 'medicamentos.json');

// Verificar y arrancar automáticamente el servidor Python si no está activo
function checkAndStartServer() {
  return new Promise((resolve) => {
    const tester = new net.Socket();
    tester.setTimeout(1000);
    tester.once('connect', () => {
      tester.destroy();
      console.log('✅ Servidor Python (Catálogo & Mostrador) activo en http://localhost:8000');
      resolve();
    });
    tester.once('error', () => {
      tester.destroy();
      console.log('⚙️ Iniciando servidor de catálogo y mostrador en segundo plano (http://localhost:8000)...');
      const pyProc = spawn('python3', [path.join(__dirname, 'server.py')], {
        stdio: 'ignore',
        detached: true
      });
      pyProc.unref();
      setTimeout(resolve, 2000);
    });
    tester.once('timeout', () => {
      tester.destroy();
      resolve();
    });
    tester.connect(8000, '127.0.0.1');
  });
}

// Cargar medicamentos para fallback si el backend de Python no estuviera activo
function loadMedicamentosFallback() {
  try {
    if (fs.existsSync(MEDICAMENTOS_PATH)) {
      return JSON.parse(fs.readFileSync(MEDICAMENTOS_PATH, 'utf-8'));
    }
  } catch (e) {}
  return [];
}

// ============================================================================
// 🛡️ CONFIGURACIÓN DE SEGURIDAD (Para no molestar contactos personales)
// ============================================================================
// Si MODO_SEGURO = true:
// - El bot ignora todos los grupos de WhatsApp.
// - En chats individuales, SOLO responde si el mensaje incluye '#farmacia' (ej: '#farmacia Hola' o '#farmacia Tafirol')
//   O si el número está en la lista blanca (WHITELIST_NUMBERS).
// Cuando uses un número exclusivo de la farmacia, cambia MODO_SEGURO a false.
const MODO_SEGURO = true;
const WHITELIST_NUMBERS = [
  // Puedes agregar números de prueba autorizados aquí (ej: '5491122334455')
];

async function startWhatsAppBot() {
  // Asegurar que el servidor web de la farmacia esté corriendo
  await checkAndStartServer();

  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

  const sock = makeWASocket({
    auth: state,
    logger,
    printQRInTerminal: false,
    browser: ['Farmacia Bot', 'Chrome', '1.0.0']
  });

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.log('\n======================================================');
      console.log('📲 ESCANEA ESTE CÓDIGO QR CON TU WHATSAPP:');
      console.log('   (Abre WhatsApp > Ajustes / Dispositivos vinculados > Vincular)');
      console.log('======================================================\n');
      qrcode.generate(qr, { small: true });
      console.log('Esperando escaneo...\n');
    }

    if (connection === 'close') {
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const errorMsg = lastDisconnect?.error?.message || '';
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

      if (errorMsg.includes('ENOTFOUND')) {
        console.log('⚠️ Esperando conexión con los servidores de WhatsApp... Reintentando en 5 segundos.');
      } else {
        console.log(`⚠️ Conexión cerrada (${statusCode || errorMsg}). Reconectando...`);
      }

      if (shouldReconnect) {
        setTimeout(startWhatsAppBot, 5000);
      } else {
        console.log('❌ Sesión cerrada por el usuario. Elimina la carpeta auth_session para volver a escanear un nuevo QR.');
      }
    } else if (connection === 'open') {
      console.log('\n======================================================');
      console.log('✅ ¡WHATSAPP CONECTADO EXITOSAMENTE A LA FARMACIA!');
      if (MODO_SEGURO) {
        console.log('🛡️ MODO SEGURO ACTIVO:');
        console.log('   - Ignorando grupos.');
        console.log('   - Solo responderá a mensajes que incluyan "#farmacia"');
        console.log('   - Ejemplo de prueba: "#farmacia Hola" o "#farmacia Ibuprofeno"');
      } else {
        console.log('⚡ Modo Negocio: Respondiendo a todos los chats individuales.');
      }
      console.log('======================================================\n');
    }
  });

  // Escuchar mensajes entrantes
  sock.ev.on('messages.upsert', async (m) => {
    // Permitir notify (mensajes externos) y append (mensajes propios sincronizados)
    if (m.type !== 'notify' && m.type !== 'append') return;

    for (const msg of m.messages) {
      // Si el mensaje es propio (enviado por ti mismo), permitirlo únicamente si incluye '#farmacia'
      // Esto te permite probar el bot escribiéndote a ti mismo en WhatsApp ("Tú / Mensajes a mí mismo") sin bucles.
      if (msg.key.fromMe) {
        const textoSelf = (
          msg.message?.conversation ||
          msg.message?.extendedTextMessage?.text ||
          ''
        ).trim().toLowerCase();
        if (!textoSelf.includes('#farmacia')) {
          continue;
        }
      }
      if (msg.key.remoteJid.endsWith('@broadcast')) continue; // Ignorar estados
      if (msg.key.remoteJid.endsWith('@g.us')) continue; // 🛡️ Ignorar SIEMPRE grupos de WhatsApp

      const remoteJid = msg.key.remoteJid;
      const pushName = msg.pushName || 'Cliente';
      const senderPhone = remoteJid.replace(/[^0-9]/g, '');
      const isWhitelisted = WHITELIST_NUMBERS.length > 0 && WHITELIST_NUMBERS.some(n => senderPhone.includes(n));

      // Extraer texto o pie de foto
      const textoOriginal = (
        msg.message?.conversation ||
        msg.message?.extendedTextMessage?.text ||
        msg.message?.imageMessage?.caption ||
        ''
      ).trim();

      const tieneDisparador = textoOriginal.toLowerCase().includes('#farmacia') || 
                             textoOriginal.toLowerCase().startsWith('farmacia') ||
                             textoOriginal.includes('Nuevo Pedido');

      // 🛡️ Filtro de seguridad: Si no es número autorizado ni tiene la clave, ignorar silenciosamente
      if (MODO_SEGURO && !isWhitelisted && !tieneDisparador) {
        continue; // No responder a amigos ni familiares
      }

      console.log(`📩 [WhatsApp ${m.type}] Mensaje detectado de ${pushName}: "${textoOriginal}"`);

      // Al responderse a uno mismo, no citar el mensaje propio para evitar bloqueos de WhatsApp
      const quoteOpt = msg.key.fromMe ? {} : { quoted: msg };

      // Detectar si envió imagen (ej. receta médica)
      if (msg.message?.imageMessage) {
        console.log(`📸 Imagen/Receta médica recibida de ${pushName} (${remoteJid})`);
        const respuestaReceta = 
          `👋 ¡Hola ${pushName}!\n\n` +
          `📸 *Recibimos la foto de tu orden/receta médica en Farmacia Torres.*\n` +
          `Un farmacéutico la está revisando en este momento para verificar:\n` +
          `• Cobertura de tu obra social / prepaga\n` +
          `• Stock de la dosis indicada\n\n` +
          `En breves minutos te confirmamos por este mismo chat. ¡Gracias por tu paciencia!`;

        await sock.sendMessage(remoteJid, { text: respuestaReceta }, quoteOpt);
        continue;
      }

      if (!textoOriginal) continue;

      // Limpiar el prefijo '#farmacia' para procesar la consulta real
      let texto = textoOriginal
        .replace(/#farmacia/gi, '')
        .replace(/^farmacia:?/gi, '')
        .trim();

      // Si solo enviaron "#farmacia", tratarlo como saludo/menú
      if (!texto) texto = 'hola';

      console.log(`💬 Consulta procesada para ${pushName}: "${texto}"`);
      const textoLower = texto.toLowerCase();

      // Si es un pedido generado desde la web (empieza con "👋 *Nuevo Pedido")
      if (texto.includes('Nuevo Pedido') || texto.includes('Detalle de medicamentos')) {
        const respuestaPedido = 
          `🎉 *¡Muchas gracias por enviar tu pedido a Farmacia Torres, ${pushName}!* 📦\n\n` +
          `Hemos recibido el detalle de tu compra. Nuestro equipo está separando los medicamentos en mostrador.\n` +
          `Te confirmaremos el total final y los detalles de retiro o envío en unos minutos.`;
        await sock.sendMessage(remoteJid, { text: respuestaPedido }, quoteOpt);
        continue;
      }

      // Procesar vía backend Python (Máquina de estados conversacional y registro de pedidos)
      let respuestaFinal = '';
      try {
        const response = await axios.post(BACKEND_URL, {
          data: {
            key: { remoteJid },
            pushName: pushName,
            message: { conversation: texto }
          }
        }, { timeout: 4000 });

        if (response.data && response.data.response_text) {
          respuestaFinal = response.data.response_text;
        }
      } catch (err) {
        // Fallback local si el backend de Python está apagado
        const meds = loadMedicamentosFallback();
        const matches = meds.filter(m => 
          m.nombre_comercial.toLowerCase().includes(textoLower) || 
          m.principio_activo.toLowerCase().includes(textoLower) ||
          m.categoria.toLowerCase().includes(textoLower)
        );

        if (matches.length > 0) {
          const listado = matches.slice(0, 3).map(m => {
            const receta = m.requiere_receta ? '⚠️ Requiere receta' : '✅ Venta libre';
            const tipo = m.es_generico ? '🟢 Genérico' : '🏷️ Marca';
            return `💊 *${m.nombre_comercial}* (${tipo})\n   Droga: ${m.principio_activo} ${m.concentracion ? `(${m.concentracion})` : ''}\n   Precio: *$${m.precio.toLocaleString('es-AR')}* | Stock: ${m.stock} u.\n   ${receta}`;
          }).join('\n\n');

          respuestaFinal = `🔍 *Resultados para "${texto}":*\n\n${listado}\n\n¿Deseas encargar alguno o consultar por otra marca?`;
        } else {
          respuestaFinal = 
            `No encontramos medicamentos que coincidan con "${texto}".\n` +
            `Prueba escribiendo el nombre comercial o la droga (ej. *Tafirol*, *Ibuprofeno*).\n` +
            `También puedes revisar el catálogo online en: ${PUBLIC_URL}`;
        }
      }

      // Enviar respuesta
      if (respuestaFinal) {
        await sock.sendMessage(remoteJid, { text: respuestaFinal }, quoteOpt);
      }
    }
  });
}

// Ejecutar
startWhatsAppBot().catch(err => {
  console.error('Error fatal al iniciar bot de WhatsApp:', err);
});
