"""
Aplicación principal Flask.
Maneja el webhook de Meta para recibir DMs de Instagram
y coordina las respuestas automáticas.
"""

import json
import os
import hmac
import hashlib
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from bot.instagram import crear_cliente_instagram
from bot.claude_agent import crear_agent_claude
from bot.email_notifier import crear_notificador_email
from bot.conversation_log import guardar_mensaje, obtener_historial, inicializar_log

# Cargar variables de entorno desde .env
load_dotenv()

# Crear aplicación Flask
app = Flask(__name__)

# Inicializar componentes
try:
    instagram_client = crear_cliente_instagram()
    claude_agent = crear_agent_claude()
    email_notifier = crear_notificador_email()
    inicializar_log()
    print("✓ Componentes inicializados correctamente")
except ValueError as e:
    print(f"✗ Error de inicialización: {e}")
    print("  Asegúrate de tener un archivo .env configurado correctamente")
    exit(1)


@app.route("/", methods=["GET"])
def health_check():
    """Health check del servidor."""
    return jsonify({
        "status": "ok",
        "mensaje": "Bot de MakerStudios activo",
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }), 200


@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    """
    Verifica el webhook con Meta.
    Meta envía un challenge durante la configuración del webhook.
    """
    verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN")

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if not verify_token:
        print("✗ WEBHOOK_VERIFY_TOKEN no está configurado en .env")
        return "Webhook token no configurado", 403

    # Validar el token
    if mode == "subscribe" and token == verify_token:
        print("✓ Webhook verificado con Meta")
        return challenge, 200
    else:
        print(f"✗ Intento de verificación con token incorrecto: {token}")
        return "Token de verificación inválido", 403


@app.route("/webhook", methods=["POST"])
def procesar_webhook():
    """
    Procesa los mensajes entrantes del webhook de Meta.
    """
    # Validar la firma HMAC para asegurar que viene de Meta
    app_secret = os.getenv("INSTAGRAM_APP_SECRET")
    if not app_secret:
        print("✗ INSTAGRAM_APP_SECRET no está configurado")
        return jsonify({"error": "Servidor no configurado"}), 500

    # Obtener la firma del header
    x_hub_signature = request.headers.get("X-Hub-Signature-256", "")

    # Calcular la firma esperada
    payload = request.get_data()  # Obtener bytes RAW del request
    expected_signature = f"sha256={hmac.new(app_secret.encode(), payload, hashlib.sha256).hexdigest()}"

    # Validar que la firma coincida
    if not hmac.compare_digest(x_hub_signature, expected_signature):
        print("✗ Firma HMAC inválida - Posible solicitud no autorizada")
        return jsonify({"error": "Firma inválida"}), 403

    try:
        datos = request.get_json()
    except Exception as e:
        print(f"✗ Error parseando JSON: {e}")
        return jsonify({"error": "JSON inválido"}), 400

    # Procesar el webhook (Meta puede enviar otros eventos además de mensajes)
    if datos.get("object") == "instagram":
        entry = datos.get("entry", [])

        for item in entry:
            messaging_events = item.get("messaging", [])

            for evento in messaging_events:
                procesar_mensaje(evento)

        return jsonify({"status": "ok"}), 200

    return jsonify({"status": "ok"}), 200


def procesar_mensaje(evento: dict):
    """
    Procesa un evento de mensaje individual.

    Args:
        evento (dict): Evento de mensaje del webhook
    """
    # Extraer información del mensaje
    sender_id = evento.get("sender", {}).get("id")
    mensaje = evento.get("message", {})
    texto = mensaje.get("text", "").strip()

    if not sender_id or not texto:
        return  # Ignorar mensajes sin texto (attachments, etc.)

    print(f"\n📨 Nuevo mensaje de {sender_id}: {texto[:50]}...")

    # Guardar el mensaje del usuario en el log
    guardar_mensaje(sender_id, "usuario", texto)

    # Obtener el historial de conversación
    historial = obtener_historial(sender_id)

    # Detectar si necesita escalado
    necesita_escalado, palabra_clave = claude_agent.detectar_palabras_clave_escalado(texto)

    if necesita_escalado:
        print(f"⚠️  Escalado detectado: '{palabra_clave}'")
        manejar_escalado(sender_id, texto, palabra_clave, historial)
    else:
        manejar_respuesta_normal(sender_id, texto, historial)


def manejar_respuesta_normal(sender_id: str, texto: str, historial: list):
    """
    Maneja una conversación normal generando respuesta con Claude.

    Args:
        sender_id (str): ID del usuario
        texto (str): Mensaje del usuario
        historial (list): Historial de conversación
    """
    # Generar respuesta con Claude
    respuesta = claude_agent.generar_respuesta(sender_id, texto)

    # Enviar respuesta a través de Instagram
    if instagram_client.enviar_mensaje(sender_id, respuesta):
        # Guardar la respuesta en el log
        guardar_mensaje(sender_id, "bot", respuesta)
        print(f"✓ Respuesta enviada: {respuesta[:50]}...")
    else:
        print("✗ No se pudo enviar la respuesta")


def manejar_escalado(sender_id: str, texto: str, palabra_clave: str, historial: list):
    """
    Maneja un mensaje que necesita escalado a un humano.

    Args:
        sender_id (str): ID del usuario
        texto (str): Mensaje del usuario
        palabra_clave (str): Palabra clave que triggeró el escalado
        historial (list): Historial de conversación
    """
    # Obtener el mensaje de escalado del config
    config = claude_agent.config
    mensaje_escalado = config.get("escalado", {}).get("mensaje_escalado", "")
    email_destino = config.get("escalado", {}).get("notificar_a", "")

    # Enviar respuesta de escalado al cliente
    if mensaje_escalado:
        if instagram_client.enviar_mensaje(sender_id, mensaje_escalado):
            guardar_mensaje(sender_id, "bot", mensaje_escalado)
            print(f"✓ Mensaje de escalado enviado al cliente")
        else:
            print("✗ No se pudo enviar el mensaje de escalado")

    # Enviar notificación por email al dueño del negocio
    if email_destino:
        email_notifier.enviar_alerta_escalado(
            destinatario=email_destino,
            sender_id=sender_id,
            mensaje_usuario=texto,
            palabra_clave=palabra_clave,
            historial=historial
        )
    else:
        print("⚠️  Email de destino no configurado en config.json")


@app.errorhandler(404)
def no_encontrado(error):
    """Manejador de rutas no encontradas."""
    return jsonify({"error": "Ruta no encontrada"}), 404


@app.errorhandler(500)
def error_interno(error):
    """Manejador de errores internos."""
    print(f"✗ Error interno del servidor: {error}")
    return jsonify({"error": "Error interno del servidor"}), 500


if __name__ == "__main__":
    puerto = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    print("\n" + "="*60)
    print("🚀 Bot de MakerStudios iniciando...")
    print("="*60)
    print(f"Puerto: {puerto}")
    print(f"Debug: {debug}")
    print(f"Negocio: {claude_agent.config.get('negocio', {}).get('nombre', 'MakerStudios')}")
    print("="*60 + "\n")

    app.run(host="0.0.0.0", port=puerto, debug=debug)
