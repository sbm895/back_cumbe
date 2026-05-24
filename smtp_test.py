# test_smtp.py
import smtplib

HOST = "smtp.gmail.com"
PORT = 587
USER = "erandreh@gmail.com"
PASSWORD = "irididbedexhsapa"

try:
    with smtplib.SMTP(HOST, PORT) as server:
        server.set_debuglevel(1)  # muestra todo el handshake
        server.starttls()
        server.login(USER, PASSWORD)
        print("✅ Login exitoso")
except Exception as e:
    print(f"❌ Error: {e}")