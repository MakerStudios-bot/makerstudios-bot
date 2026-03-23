"""
Módulo de integración con Anthropic Claude.
Genera respuestas automáticas basadas en el config.json y el historial de conversación.
"""

import json
import os
from anthropic import Anthropic


class ClaudeAgent:
    """Agente Claude para generar respuestas automáticas de CrystalPro."""

    def __init__(self, config_file: str = "config.json"):
        """
        Inicializa el agente Claude.

        Args:
            config_file (str): Ruta al archivo config.json
        """
        # Cargar la configuración del negocio
        with open(config_file, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        # Inicializar cliente Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY es requerido en .env")

        self.client = Anthropic()

        # Almacenar el historial de conversaciones por sender_id
        self.historiales = {}

        # Construir el system prompt basado en config.json
        self.system_prompt = self._construir_system_prompt()

    def _construir_system_prompt(self) -> str:
        """
        Construye el system prompt a partir del config.json.

        Returns:
            str: System prompt para Claude
        """
        config = self.config
        negocio = config.get("negocio", {})
        tono = config.get("tono", {})
        precios = config.get("precios", {})
        como_pedir = config.get("como_pedir", {})

        # Extraer información
        nombre = negocio.get("nombre", "CrystalPro")
        descripcion = negocio.get("descripcion", "")
        instagram = negocio.get("instagram", "")
        horario = negocio.get("horario_atencion", "")

        estilo = tono.get("estilo", "")
        instrucciones_tono = tono.get("instrucciones", "")

        precio_desc = precios.get("descripcion", "")
        materiales = ", ".join(precios.get("materiales_disponibles", []))
        pasos = "\n".join(como_pedir.get("pasos", []))

        system_prompt = f"""Eres un asistente de atención al cliente para {nombre}, un servicio profesional de limpieza de ventanas y ventanales.

INFORMACIÓN DEL NEGOCIO:
- Nombre: {nombre}
- Descripción: {descripcion}
- Instagram: {instagram}
- Horario: {horario}
- Área de cobertura: La Serena
- Servicios: Limpieza de ventanas, ventanales, y vidrios. Rápido, sin manchas y sin complicaciones.

PRECIOS Y OFERTAS:
{precio_desc}
🎯 OFERTA PRINCIPAL: $38.000 por 10 ventanas/ventanales (Incluye vidrios limpios sin manchas)
💰 Ventanas adicionales: Se cotiza según cantidad y tamaño
⚡ Cotización: Respondemos en menos de 2 horas

PROCESO DE CONTRATACIÓN:
{pasos}

FORMA DE ATENDER:
- Estilo: {estilo}
- {instrucciones_tono}

INSTRUCCIONES IMPORTANTES:
1. Siempre responde en español
2. Sé profesional, claro, conciso y amigable
3. Usa emojis apropiados para hacer la conversación más visual y amigable (🪟, ✨, 💰, ⚡, 👍, etc.)
4. SIEMPRE menciona la oferta de $38.000 por 10 ventanas cuando el cliente pregunte sobre servicios o precios
5. Si el cliente quiere cotizar, pide: cantidad de ventanas, ubicación (zona), y tamaño aproximado
6. Responde como representante oficial de {nombre}
7. Sé proactivo en ofrecer agendar online o contacto por WhatsApp
8. Mantén un tono de confianza y profesionalismo

IMPORTANTE: Mantén las respuestas cortas (máximo 3-4 párrafos). El cliente está en Instagram, así que sé directo y usa emojis."""

        return system_prompt

    def generar_respuesta(self, sender_id: str, mensaje_usuario: str) -> str:
        """
        Genera una respuesta usando Claude basada en el mensaje del usuario
        y el historial de la conversación.

        Args:
            sender_id (str): ID único del usuario
            mensaje_usuario (str): Mensaje del usuario

        Returns:
            str: Respuesta generada por Claude
        """
        # Inicializar historial si no existe
        if sender_id not in self.historiales:
            self.historiales[sender_id] = []

        # Agregar el mensaje del usuario al historial
        self.historiales[sender_id].append({
            "role": "user",
            "content": mensaje_usuario
        })

        # Mantener solo los últimos 10 mensajes para no exceder límites de token
        historial_limitado = self.historiales[sender_id][-20:]

        try:
            # Llamar a Claude con el historial
            respuesta = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                system=self.system_prompt,
                messages=historial_limitado
            )

            # Extraer el texto de la respuesta
            texto_respuesta = respuesta.content[0].text

            # Guardar la respuesta en el historial
            self.historiales[sender_id].append({
                "role": "assistant",
                "content": texto_respuesta
            })

            return texto_respuesta

        except Exception as e:
            print(f"✗ Error generando respuesta: {e}")
            return f"Disculpa, tuve un problema procesando tu mensaje. Por favor, intenta de nuevo."

    def detectar_palabras_clave_escalado(self, texto: str) -> tuple[bool, str]:
        """
        Detecta si el mensaje contiene palabras clave que requieren escalado.

        Args:
            texto (str): Texto del mensaje

        Returns:
            tuple: (necesita_escalado: bool, palabra_clave: str)
        """
        palabras_clave = self.config.get("escalado", {}).get("trigger_palabras", [])
        texto_lower = texto.lower()

        for palabra in palabras_clave:
            if palabra.lower() in texto_lower:
                return True, palabra

        return False, ""

    def detectar_saludo(self, texto: str) -> bool:
        """
        Detecta si el mensaje es un saludo inicial.

        Args:
            texto (str): Texto del mensaje

        Returns:
            bool: True si es un saludo
        """
        saludos = [
            "hola", "buenos días", "buenos tardes", "buenas noches",
            "buenos noches", "buen día", "buena tarde", "buena noche",
            "hi", "hello", "hey", "qué tal", "cómo estás", "cómo está"
        ]
        texto_lower = texto.lower().strip()

        # Detectar si el mensaje es principalmente un saludo
        for saludo in saludos:
            if saludo in texto_lower:
                return True

        return False


def crear_agent_claude(config_file: str = "config.json") -> ClaudeAgent:
    """
    Factory function para crear un agente Claude.

    Args:
        config_file (str): Ruta al archivo config.json

    Returns:
        ClaudeAgent: Agente configurado
    """
    return ClaudeAgent(config_file)
