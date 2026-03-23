#!/usr/bin/env python3
"""
Script de prueba para validar que el bot está correctamente configurado.
Verifica todas las credenciales y conexiones antes de ejecutar en producción.
"""

import os
import sys
import json
from pathlib import Path

def verificar_archivo(ruta, nombre):
    """Verifica que un archivo existe."""
    if Path(ruta).exists():
        print(f"✓ {nombre}: {ruta}")
        return True
    else:
        print(f"✗ {nombre}: NO ENCONTRADO - {ruta}")
        return False

def verificar_env():
    """Verifica que .env existe y tiene las claves necesarias."""
    print("\n🔑 Verificando variables de entorno...")

    variables_requeridas = [
        "INSTAGRAM_ACCESS_TOKEN",
        "INSTAGRAM_APP_SECRET",
        "WEBHOOK_VERIFY_TOKEN",
        "INSTAGRAM_PAGE_ID",
        "ANTHROPIC_API_KEY",
        "EMAIL_SENDER",
        "EMAIL_PASSWORD"
    ]

    from dotenv import load_dotenv
    load_dotenv()

    todas_presentes = True
    for var in variables_requeridas:
        valor = os.getenv(var)
        if valor:
            # Mostrar solo los primeros caracteres por seguridad
            valor_corto = f"{valor[:10]}..." if len(valor) > 10 else valor
            print(f"  ✓ {var}: {valor_corto}")
        else:
            print(f"  ✗ {var}: NO CONFIGURADO")
            todas_presentes = False

    return todas_presentes

def verificar_dependencias():
    """Verifica que todas las dependencias están instaladas."""
    print("\n📦 Verificando dependencias Python...")

    dependencias = ["flask", "requests", "anthropic", "dotenv"]
    todas_instaladas = True

    for dep in dependencias:
        try:
            __import__(dep)
            print(f"  ✓ {dep}: Instalado")
        except ImportError:
            print(f"  ✗ {dep}: NO INSTALADO")
            todas_instaladas = False

    return todas_instaladas

def verificar_config():
    """Verifica que config.json es válido."""
    print("\n⚙️  Verificando config.json...")

    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        nombre = config.get("negocio", {}).get("nombre", "CrystalPro")
        instagram = config.get("negocio", {}).get("instagram", "")
        email_escalado = config.get("escalado", {}).get("notificar_a", "")

        print(f"  ✓ Negocio: {nombre}")
        print(f"  ✓ Instagram: {instagram}")
        print(f"  ✓ Email escalado: {email_escalado}")

        return True
    except FileNotFoundError:
        print("  ✗ config.json NO ENCONTRADO")
        return False
    except json.JSONDecodeError:
        print("  ✗ config.json tiene JSON inválido")
        return False

def test_antropic():
    """Prueba conexión con Anthropic."""
    print("\n🧠 Probando conexión con Anthropic Claude...")

    try:
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("  ✗ ANTHROPIC_API_KEY no configurado")
            return False

        client = Anthropic()

        # Prueba simple
        respuesta = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Responde solo 'OK' si funciona."
                }
            ]
        )

        texto = respuesta.content[0].text
        if texto:
            print(f"  ✓ Conexión exitosa: {texto[:50]}...")
            return True
        else:
            print("  ✗ Respuesta vacía de Claude")
            return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_email():
    """Prueba conexión con Gmail."""
    print("\n📧 Probando conexión con Gmail...")

    try:
        import smtplib

        email = os.getenv("EMAIL_SENDER")
        password = os.getenv("EMAIL_PASSWORD")

        if not email or not password:
            print("  ✗ EMAIL_SENDER o EMAIL_PASSWORD no configurados")
            return False

        servidor = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=5)
        servidor.login(email, password)
        servidor.quit()

        print(f"  ✓ Login exitoso en Gmail: {email}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("  ✗ Credenciales de Gmail incorrectas")
        print("    Usa una 'App Password', no tu contraseña normal")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_instagram():
    """Prueba configuración de Instagram (sin hacer requests)."""
    print("\n📱 Verificando configuración de Instagram...")

    try:
        token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        page_id = os.getenv("INSTAGRAM_PAGE_ID")

        if not token:
            print("  ✗ INSTAGRAM_ACCESS_TOKEN no configurado")
            return False

        if not page_id:
            print("  ✗ INSTAGRAM_PAGE_ID no configurado")
            return False

        # Verificar que el token parece válido (comienza con EA)
        if token.startswith("EA"):
            print(f"  ✓ Token parece válido (comienza con EA)")
        else:
            print("  ⚠️  Token parece inválido (debería comenzar con EA)")
            return False

        print(f"  ✓ Page ID: {page_id}")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    """Función principal de pruebas."""
    print("\n" + "="*60)
    print("🧪 Test de Configuración - CrystalPro Bot")
    print("="*60)

    # Verificar archivos
    print("\n📁 Verificando archivos...")
    archivos_ok = True
    archivos_ok &= verificar_archivo("config.json", "config.json")
    archivos_ok &= verificar_archivo(".env", ".env")
    archivos_ok &= verificar_archivo("requirements.txt", "requirements.txt")

    # Verificar estructura de carpetas
    archivos_ok &= verificar_archivo("bot/claude_agent.py", "bot/claude_agent.py")
    archivos_ok &= verificar_archivo("bot/instagram.py", "bot/instagram.py")
    archivos_ok &= verificar_archivo("bot/email_notifier.py", "bot/email_notifier.py")

    # Pruebas de configuración
    env_ok = verificar_env()
    deps_ok = verificar_dependencias()
    config_ok = verificar_config()

    # Pruebas de conexión (solo si las credenciales están configuradas)
    print("\n🔗 Pruebas de Conexión...")
    anthropic_ok = test_antropic() if env_ok else False
    email_ok = test_email() if env_ok else False
    instagram_ok = test_instagram()

    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)

    todo_ok = archivos_ok and env_ok and deps_ok and config_ok and anthropic_ok and email_ok and instagram_ok

    print(f"Archivos: {'✓' if archivos_ok else '✗'}")
    print(f"Env: {'✓' if env_ok else '✗'}")
    print(f"Dependencias: {'✓' if deps_ok else '✗'}")
    print(f"Config.json: {'✓' if config_ok else '✗'}")
    print(f"Anthropic: {'✓' if anthropic_ok else '✗'}")
    print(f"Email: {'✓' if email_ok else '✗'}")
    print(f"Instagram: {'✓' if instagram_ok else '✗'}")

    print("\n" + "="*60)

    if todo_ok:
        print("✓ Todo está configurado correctamente!")
        print("Puedes ejecutar: python3 app.py")
        return 0
    else:
        print("✗ Hay problemas de configuración.")
        print("Revisa los errores arriba y actualiza tu .env")
        return 1

if __name__ == "__main__":
    sys.exit(main())
