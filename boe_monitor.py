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
    headers = {"Authorization": f"Bearer {api_key}"}
    prompt = "Eres un analista. Resume los 10 puntos más importantes de este sumario del BOE para ciudadanos comunes. Usa emojis."
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": texto_boe}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

def ejecutar():
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    url_api = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha_hoy}"
    
    print(f"Consultando: {url_api}")
    try:
        response = requests.get(url_api, timeout=30)
        
        # CASO 1: La API aún no tiene los datos del día
        if response.status_code != 200:
            enviar_telegram(f"⏳ *BOE en espera:* La API de datos abiertos aún no ha publicado el sumario de hoy ({datetime.now().strftime('%d/%m')}). Reintentaré más tarde.")
            return

        soup = BeautifulSoup(response.content, 'xml')
        titulos = [t.text for t in soup.find_all('titulo')]
        
        # CASO 2: Hay datos pero no hay títulos (raro, pero posible)
        if not titulos:
            enviar_telegram("⚠️ *Aviso:* Se ha accedido al sumario pero no se han encontrado títulos para analizar.")
            return

        # CASO 3: Éxito total
        texto_para_ia = "\n- ".join(titulos[:120]) # Limitamos para no exceder tokens
        resumen = pedir_resumen_gpt(texto_para_ia)
        enviar_telegram(f"🗞 *RESUMEN BOE {datetime.now().strftime('%d/%m')}*\n\n{resumen}")

    except Exception as e:
        enviar_telegram(f"💥 *Error técnico:* Ha ocurrido un fallo al intentar leer el BOE: `{str(e)}`克服")

if __name__ == "__main__":
    ejecutar()
