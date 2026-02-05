import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

def enviar_telegram(mensaje):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Telegram tiene un límite de 4096 caracteres
    if len(mensaje) > 4000:
        mensaje = mensaje[:4000] + "..."
    payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def pedir_resumen_gpt(texto_boe):
    api_key = os.getenv('OPENAI_API_KEY')
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    prompt = (
        "Eres un analista experto. Resume las 10 noticias o leyes más importantes de este sumario del BOE "
        "para ciudadanos comunes. Usa emojis, puntos clave y un lenguaje claro."
    )
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": texto_boe}
        ],
        "temperature": 0.5
    }
    
    response = requests.post(url, headers=headers, json=data)
    try:
        return response.json()['choices'][0]['message']['content']
    except:
        return "⚠️ La IA recibió los datos pero no pudo generar el resumen."

def ejecutar():
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    # Usamos exactamente la URL que me has pasado
    url_api = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha_hoy}"
    
    print(f"Consultando API: {url_api}")
    response = requests.get(url_api, timeout=30)
    
    if response.status_code != 200:
        enviar_telegram(f"⏳ El BOE aún no responde en la API ({datetime.now().strftime('%d/%m')}).")
        return

    # Usamos 'xml' para que BeautifulSoup entienda las etiquetas del BOE
    soup = BeautifulSoup(response.content, 'xml')
    
    # IMPORTANTE: Buscamos todos los textos dentro de las etiquetas <titulo>
    # En la API que pasaste, están dentro de <item>
    titulos = []
    for item in soup.find_all('item'):
        t = item.find('titulo')
        if t and t.text:
            titulos.append(t.text.strip())

    print(f"Títulos encontrados: {len(titulos)}")

    if len(titulos) > 0:
        # Enviamos los títulos a la IA (limitamos a los 100 primeros para no saturar)
        texto_ia = "\n- ".join(titulos[:100])
        resumen = pedir_resumen_gpt(texto_ia)
        enviar_telegram(f"🗞 *RESUMEN INTELIGENTE BOE*\n\n{resumen}")
    else:
        # Si llegamos aquí, es que la estructura del XML ha vuelto a cambiar
        enviar_telegram("❌ Error: He leído el XML pero no he podido extraer los títulos. Revisa el código.")

if __name__ == "__main__":
    ejecutar()
