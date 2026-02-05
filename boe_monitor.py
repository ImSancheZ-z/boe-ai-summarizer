import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

def enviar_telegram(mensaje):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def pedir_resumen_gpt(texto_boe):
    api_key = os.getenv('OPENAI_API_KEY')
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    prompt = "Eres un analista experto. Resume los 10 puntos más importantes de este BOE. Usa emojis."
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": texto_boe}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

def ejecutar():
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    url_api = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha_hoy}"
    
    # Headers vitales para que el BOE no nos bloquee
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Consultando: {url_api}")
    response = requests.get(url_api, headers=headers, timeout=30)
    
    # Si da error, enviamos el código exacto para saber qué pasa
    if response.status_code != 200:
        enviar_telegram(f"⏳ Error {response.status_code}: El BOE bloqueó la conexión o no hay datos aún.")
        return

    soup = BeautifulSoup(response.content, 'xml')
    # Extracción ultra-segura de títulos
    titulos = [t.text.strip() for t in soup.find_all('titulo') if t.text]
    
    if len(titulos) > 5:
        resumen = pedir_resumen_gpt("\n".join(titulos[:150]))
        enviar_telegram(f"🗞 *TOP 10 BOE - {datetime.now().strftime('%d/%m')}*\n\n{resumen}")
    else:
        enviar_telegram(f"⚠️ Se conectó bien, pero solo encontré {len(titulos)} títulos.")

if __name__ == "__main__":
    ejecutar()
