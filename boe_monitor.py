import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# Función para Telegram
def enviar_telegram(mensaje):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def obtener_sumario_xml():
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    url = f"https://www.boe.es/diario_boe/xml.php?id=BOE-S-{fecha_hoy}"
    
    try:
        response = requests.get(url, timeout=20)
        if response.status_code != 200: return None
        return BeautifulSoup(response.content, 'xml')
    except:
        return None

def ejecutar():
    soup = obtener_sumario_xml()
    if not soup:
        print("BOE no disponible todavía.")
        return

    # Extraemos todos los títulos del día para la IA
    items = soup.find_all('item')
    todos_los_titulos = [item.find('titulo').text for item in items if item.find('titulo')]
    
    # --- FASE 1: Filtro previo (para no gastar tokens de IA innecesarios) ---
    keywords = ["ayuda", "subvención", "impuesto", "carretera", "vivienda", "empleo", "pensiones", "motos", "tráfico"]
    interesantes = [t for t in todos_los_titulos if any(k in t.lower() for k in keywords)]

    if interesantes:
        # Aquí es donde en el siguiente paso conectaremos con la API de IA
        texto_para_ia = "\n".join(interesantes)
        
        # Por ahora, te enviamos el "bruto" filtrado
        mensaje = f"🗞 **BOE {datetime.now().strftime('%d/%m/%Y')}**\n\n"
        mensaje += "\n\n".join(interesantes[:10])
        enviar_telegram(mensaje)

if __name__ == "__main__":
    ejecutar()
