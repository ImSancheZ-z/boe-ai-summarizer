import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

def enviar_telegram(mensaje):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Fragmentamos si el mensaje es muy largo para Telegram
    if len(mensaje) > 4000:
        mensaje = mensaje[:4000] + "..."
    payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def pedir_resumen_gpt(texto_boe):
    api_key = os.getenv('OPENAI_API_KEY')
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    prompt = (
        "Eres un analista experto en el BOE. Te proporciono el sumario oficial de hoy. "
        "Selecciona las 10 noticias, leyes o ayudas más relevantes para la ciudadanía y el sector motor/motos. "
        "Explica por qué son importantes en una frase corta. Usa emojis y un formato limpio."
    )
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": texto_boe}
        ],
        "temperature": 0.3 # Mayor precisión
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ Error con la IA: {str(e)}"

def ejecutar():
    # Usamos la API de Datos Abiertos que has indicado
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    url_api = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha_hoy}"
    
    print(f"Consultando API: {url_api}")
    response = requests.get(url_api, timeout=30)
    
    if response.status_code != 200:
        print("El BOE de hoy no está disponible en la API.")
        return

    # Procesamos el XML de la API
    soup = BeautifulSoup(response.content, 'xml')
    
    # En esta API, los títulos suelen estar dentro de etiquetas <titulo> dentro de <item>
    items = soup.find_all('item')
    titulos_sumario = []
    
    for item in items:
        t = item.find('titulo')
        if t:
            titulos_sumario.append(t.text)

    if titulos_sumario:
        texto_para_ia = "\n- ".join(titulos_sumario)
        # Enviamos todo el índice a GPT-4o mini
        resumen_ia = pedir_resumen_gpt(texto_para_ia)
        
        mensaje_final = f"🗞 *BOE INTELIGENTE ({datetime.now().strftime('%d/%m')})*\n\n{resumen_ia}"
        enviar_telegram(mensaje_final)
    else:
        print("No se encontraron títulos en el XML de la API.")

if __name__ == "__main__":
    ejecutar()
