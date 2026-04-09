"""
Módulo para manejar el estado persistente de usuarios escalados.
Guarda qué usuarios están esperando atención humana.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path


ESCALATED_USERS_FILE = Path(__file__).parent.parent / "makerstudios_escalated_users.json"


def inicializar_archivo_escalados():
    """Inicializa el archivo de usuarios escalados si no existe."""
    if not ESCALATED_USERS_FILE.exists():
        ESCALATED_USERS_FILE.write_text(json.dumps({}, indent=2), encoding="utf-8")


def marcar_usuario_escalado(sender_id: str, palabra_clave: str):
    """
    Marca un usuario como escalado.

    Args:
        sender_id (str): ID del usuario
        palabra_clave (str): Palabra clave que triggeró el escalado
    """
    inicializar_archivo_escalados()

    try:
        with open(ESCALATED_USERS_FILE, "r", encoding="utf-8") as f:
            escalados = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        escalados = {}

    escalados[sender_id] = {
        "escalado_en": time.time(),
        "escalado_por": palabra_clave
    }

    with open(ESCALATED_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(escalados, f, indent=2, ensure_ascii=False)

    print(f"✓ Usuario {sender_id} marcado como escalado por: '{palabra_clave}'")


def usuario_esta_escalado(sender_id: str) -> bool:
    """
    Verifica si un usuario está en estado escalado.

    Args:
        sender_id (str): ID del usuario

    Returns:
        bool: True si el usuario está escalado, False caso contrario
    """
    inicializar_archivo_escalados()

    try:
        with open(ESCALATED_USERS_FILE, "r", encoding="utf-8") as f:
            escalados = json.load(f)
        return sender_id in escalados
    except (json.JSONDecodeError, FileNotFoundError):
        return False


def desescalar_usuario(sender_id: str):
    """
    Quita el estado de escalado de un usuario.
    (Útil para uso futuro o administrativo)

    Args:
        sender_id (str): ID del usuario
    """
    inicializar_archivo_escalados()

    try:
        with open(ESCALATED_USERS_FILE, "r", encoding="utf-8") as f:
            escalados = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        escalados = {}

    if sender_id in escalados:
        del escalados[sender_id]
        with open(ESCALATED_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(escalados, f, indent=2, ensure_ascii=False)
        print(f"✓ Usuario {sender_id} desescalado")
    else:
        print(f"ℹ Usuario {sender_id} no estaba escalado")


def obtener_usuarios_escalados() -> dict:
    """Obtiene el diccionario completo de usuarios escalados."""
    inicializar_archivo_escalados()

    try:
        with open(ESCALATED_USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}
