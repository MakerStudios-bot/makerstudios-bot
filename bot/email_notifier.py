"""
Módulo de notificaciones por email.
Envía alertas de escalado cuando se detectan palabras clave que requieren atención humana.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailNotifier:
    """Manejador de notificaciones por email usando Gmail."""

    def __init__(self, email_sender: str, email_password: str):
        """
        Inicializa el notificador de email.

        Args:
            email_sender (str): Email de Gmail (ej: tu_email@gmail.com)
            email_password (str): Contraseña de aplicación de Gmail
        """
        self.email_sender = email_sender
        self.email_password = email_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465

    def enviar_alerta_escalado(
        self,
        destinatario: str,
        sender_id: str,
        mensaje_usuario: str,
        palabra_clave: str,
        historial: list = None
    ) -> bool:
        """
        Envía un email notificando sobre un mensaje que necesita escalado.

        Args:
            destinatario (str): Email donde enviar la alerta
            sender_id (str): ID del usuario en Instagram
            mensaje_usuario (str): Mensaje que triggeó el escalado
            palabra_clave (str): Palabra clave detectada
            historial (list): Historial de la conversación

        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Crear mensaje
            mensaje = MIMEMultipart("alternative")
            mensaje["Subject"] = f"🚨 ESCALADO: Cliente necesita atención - {sender_id}"
            mensaje["From"] = self.email_sender
            mensaje["To"] = destinatario

            # Construir el contenido del email
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Historial de conversación en HTML
            historial_html = "<hr><h3>Historial de conversación:</h3><ul>"
            if historial:
                for msg in historial:
                    rol = "👤 Cliente" if msg.get("rol") == "usuario" else "🤖 Bot"
                    historial_html += f"<li><strong>{rol}:</strong> {msg.get('texto', '')}</li>"
            historial_html += "</ul>"

            # Contenido HTML
            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2 style="color: #d32f2f;">⚠️ Alerta de Escalado</h2>

                    <p><strong>Timestamp:</strong> {timestamp}</p>
                    <p><strong>Palabra clave detectada:</strong> <code>{palabra_clave}</code></p>
                    <p><strong>ID del cliente:</strong> <code>{sender_id}</code></p>

                    <h3>Mensaje del cliente:</h3>
                    <blockquote style="background: #f5f5f5; padding: 10px; border-left: 4px solid #d32f2f;">
                        {mensaje_usuario}
                    </blockquote>

                    {historial_html}

                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        Este mensaje fue generado automáticamente por el bot de CrystalPro.
                        <br>Por favor, contacta al cliente lo antes posible.
                    </p>
                </body>
            </html>
            """

            parte_html = MIMEText(html, "html")
            mensaje.attach(parte_html)

            # Enviar email
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as servidor:
                servidor.login(self.email_sender, self.email_password)
                servidor.sendmail(self.email_sender, destinatario, mensaje.as_string())

            print(f"✓ Email de escalado enviado a {destinatario}")
            return True

        except smtplib.SMTPAuthenticationError:
            print("✗ Error: Credenciales de Gmail incorrectas")
            print("  Verifica que usaste una 'App Password', no tu contraseña normal")
            return False

        except smtplib.SMTPException as e:
            print(f"✗ Error SMTP: {e}")
            return False

        except Exception as e:
            print(f"✗ Error enviando email: {e}")
            return False


def crear_notificador_email() -> EmailNotifier:
    """
    Factory function para crear un notificador de email
    usando variables de entorno.

    Returns:
        EmailNotifier: Notificador configurado
    """
    email_sender = os.getenv("EMAIL_SENDER")
    email_password = os.getenv("EMAIL_PASSWORD")

    if not email_sender or not email_password:
        raise ValueError("EMAIL_SENDER y EMAIL_PASSWORD son requeridos en .env")

    return EmailNotifier(email_sender, email_password)
