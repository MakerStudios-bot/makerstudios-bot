"""
Módulo de integración con Meta Graph API.
Maneja el envío de mensajes a través de Instagram.
"""

import requests
import os
from typing import Optional


class InstagramAPI:
    """Cliente para interactuar con Meta Graph API."""

    def __init__(self, access_token: str, instagram_business_account_id: str):
        """
        Inicializa el cliente de Instagram API.

        Args:
            access_token (str): Page Access Token de Meta
            instagram_business_account_id (str): ID de la cuenta Instagram Business
        """
        self.access_token = access_token
        self.instagram_business_account_id = instagram_business_account_id
        self.api_version = "v18.0"
        self.base_url = f"https://graph.instagram.com/{self.api_version}"

    def enviar_mensaje(self, recipient_id: str, texto: str) -> bool:
        """
        Envía un mensaje DM a través de Instagram.

        Args:
            recipient_id (str): ID del usuario destinatario
            texto (str): Texto del mensaje

        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        url = f"{self.base_url}/{self.instagram_business_account_id}/messages"

        payload = {
            "messaging_type": "RESPONSE",
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "text": texto
            }
        }

        params = {
            "access_token": self.access_token
        }

        try:
            respuesta = requests.post(url, json=payload, params=params, timeout=10)

            if respuesta.status_code in [200, 201]:
                print(f"✓ Mensaje enviado a {recipient_id}")
                return True
            else:
                print(f"✗ Error al enviar mensaje: {respuesta.status_code}")
                print(f"  Respuesta: {respuesta.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"✗ Error de conexión: {e}")
            return False

    def obtener_webhook_id(self) -> Optional[str]:
        """
        Obtiene el ID del webhook (útil para debugging).

        Returns:
            str: ID del webhook o None si hay error
        """
        url = f"{self.base_url}/{self.page_id}/subscribed_apps"
        params = {"access_token": self.access_token}

        try:
            respuesta = requests.get(url, params=params, timeout=10)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                print(f"Apps suscritos al webhook: {datos}")
                return True
            return None
        except Exception as e:
            print(f"Error obteniendo webhook: {e}")
            return None


def crear_cliente_instagram() -> InstagramAPI:
    """
    Factory function para crear un cliente de Instagram
    usando variables de entorno.

    Returns:
        InstagramAPI: Cliente configurado
    """
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    instagram_business_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

    if not token or not instagram_business_account_id:
        raise ValueError("INSTAGRAM_ACCESS_TOKEN e INSTAGRAM_BUSINESS_ACCOUNT_ID son requeridos en .env")

    return InstagramAPI(token, instagram_business_account_id)
