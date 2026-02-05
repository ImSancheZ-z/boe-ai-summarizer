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
    prompt = "Eres un analista experto. Resume las 10 noticias más importantes de este sumario del BOE para ciudadanos comunes. Usa emojis y puntos clave."
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": texto_boe}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

def ejecutar():
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    # Cambiamos a la URL de sumario XML directo, que es la que mejor funciona con BeautifulSoup
    url_xml = f"https://www.boe.es/diario_boe/xml.php?id=BOE-S-{fecha_hoy}"
    
    print(f"Consultando XML: {url_xml}")
    response = requests.get(url_xml, timeout=30)
    
    if response.status_code != 200:
        enviar_telegram(f"⏳ El BOE XML aún no está disponible ({datetime.now().strftime('%d/%m')}).")
        return

    # Usamos el parser de XML
    soup = BeautifulSoup(response.content, 'xml')
    
    # En el XML de sumario, los títulos están en etiquetas <titulo>
    # Buscamos todos los títulos de las disposiciones
    titulos = [t.text for t in soup.find_all('titulo')]
    
    print(f"Títulos extraídos: {len(titulos)}")

    if len(titulos) > 10: # Si hay suficientes títulos
        # Cogemos una muestra representativa (los primeros 150 títulos suelen ser los importantes)
        texto_para_ia = "\n- ".join(titulos[:150])
        resumen = pedir_resumen_gpt(texto_para_ia)
        enviar_telegram(f"🗞 *TOP 10 BOE - {datetime.now().strftime('%d/%m')}*\n\n{resumen}")
    else:
        enviar_telegram("ℹ️ El BOE de hoy parece estar vacío o no contiene disposiciones relevantes.")

if __name__ == "__main__":
    ejecutar()
