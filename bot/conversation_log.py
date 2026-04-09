"""
Módulo de logging de conversaciones.
Guarda todos los mensajes en conversations.json para auditoría y análisis.
"""

import json
import os
from datetime import datetime
from threading import Lock

# Lock para thread-safety en operaciones de archivo
log_lock = Lock()

CONVERSATIONS_FILE = "makerstudios_conversations.json"


def inicializar_log():
    """Inicializa el archivo de conversaciones si no existe."""
    if not os.path.exists(CONVERSATIONS_FILE):
        with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump({"conversaciones": {}}, f, ensure_ascii=False, indent=2)


def guardar_mensaje(sender_id, rol, texto):
    """
    Guarda un mensaje en el log de conversaciones.

    Args:
        sender_id (str): ID del usuario que envía el mensaje
        rol (str): "usuario" o "bot"
        texto (str): Contenido del mensaje
    """
    with log_lock:
        # Asegurar que el archivo existe
        inicializar_log()

        # Leer el archivo actual
        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)

        # Asegurar que existe la conversación del sender
        if sender_id not in datos["conversaciones"]:
            datos["conversaciones"][sender_id] = []

        # Agregar el nuevo mensaje con timestamp
        mensaje = {
            "timestamp": datetime.now().isoformat(),
            "rol": rol,
            "texto": texto
        }

        datos["conversaciones"][sender_id].append(mensaje)

        # Escribir el archivo actualizado
        with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)


def obtener_historial(sender_id, limite=10):
    """
    Obtiene el historial de conversación de un usuario.

    Args:
        sender_id (str): ID del usuario
        limite (int): Número máximo de mensajes a retornar (últimos N)

    Returns:
        list: Lista de mensajes con formato [{timestamp, rol, texto}]
    """
    with log_lock:
        inicializar_log()

        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)

        # Retornar el historial del usuario o lista vacía si no existe
        historial = datos["conversaciones"].get(sender_id, [])

        # Retornar solo los últimos `limite` mensajes
        return historial[-limite:]


def contar_conversaciones():
    """Retorna el número total de conversaciones únicas."""
    with log_lock:
        inicializar_log()

        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)

        return len(datos["conversaciones"])
