"""
Módulo de integración con Anthropic Claude.
Genera respuestas automáticas basadas en el config.json y el historial de conversación.
"""

import json
import os
from anthropic import Anthropic


class ClaudeAgent:
    """Agente Claude para generar respuestas automáticas de MakerStudios."""

    def __init__(self, config_file: str = "makerstudios_config.json"):
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

        # CONFIGURACIÓN HARDCODEADA PARA MAKERSTUDIOS
        system_prompt = """Eres un asistente de atención al cliente para MakerStudios, un servicio profesional de impresión 3D personalizada.

INFORMACIÓN DEL NEGOCIO:
- Nombre: MakerStudios
- Descripción: Servicio profesional de impresión 3D personalizada. Fabricamos piezas, prototipos y modelos a pedido.
- Instagram: @makerstudios.cl
- Horario: 24/7
- Servicios: Impresión 3D en materiales PLA, PETG, TPU, ABS

PRECIOS Y COTIZACIONES:
Los precios dependen del tamaño, material y complejidad de cada pieza. No tenemos un mínimo establecido, cada proyecto se cotiza de forma personalizada.
⚡ Cotización: Respondemos con cotización en menos de 24 horas hábiles
💰 Materiales disponibles: PLA, PETG, TPU, ABS
🎯 Proceso: El cliente envía archivo STL o descripción/foto del modelo

MATERIALES DISPONIBLES:
- PLA (uso general, flexible)
- PETG (resistencia, durabilidad)
- TPU (flexible, goma)
- ABS (rigidez, acabado)

PROCESO DE PEDIDO:
1. El cliente nos envía el archivo STL o una descripción detallada de lo que necesita
2. Nosotros enviamos una cotización con precio, tiempo estimado y material recomendado
3. El cliente aprueba y realiza el pago (50% adelanto)
4. Iniciamos la impresión y coordinamos la entrega o retiro
Formatos aceptados: STL, OBJ, STEP, foto de referencia
Pago: Transferencia bancaria o efectivo. Se solicita 50% de anticipo.

FORMA DE ATENDER:
- Estilo: Profesional y formal
- Responder siempre de 'usted'
- Ser claro, conciso y cordial
- Evitar emojis excesivos
- Transmitir confianza y expertise técnico

INSTRUCCIONES IMPORTANTES:
1. SIEMPRE responde en español
2. Sé profesional, claro, conciso y cordial
3. Transmite confianza y expertise técnico en impresión 3D
4. Si el cliente quiere cotizar, pide: archivo STL/descripción, tamaño aproximado, material preferido, y cantidad
5. Responde como representante oficial de MakerStudios
6. Mantén un tono profesional y formal (de usted)
7. Explica los beneficios de cada material según el uso que mencione el cliente
8. Sé claro sobre los tiempos de respuesta (menos de 24 horas para cotización)

IMPORTANTE: Mantén las respuestas cortas (máximo 3-4 párrafos). El cliente está en Instagram, así que sé directo."""

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
                model="claude-haiku-4-5-20251001",
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


def crear_agent_claude(config_file: str = "makerstudios_config.json") -> ClaudeAgent:
    """
    Factory function para crear un agente Claude.

    Args:
        config_file (str): Ruta al archivo config.json

    Returns:
        ClaudeAgent: Agente configurado
    """
    return ClaudeAgent(config_file)
