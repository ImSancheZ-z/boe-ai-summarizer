import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

def enviar_telegram(mensaje):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    if len(mensaje) > 4000:
        mensaje = mensaje[:4000] + "..."
    payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def pedir_resumen_gpt(texto_boe):
    api_key = os.getenv('OPENAI_API_KEY')
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    prompt = (
        "Eres un analista experto en el BOE. Te paso el sumario de hoy organizado por departamentos. "
        "Selecciona las 10 noticias o leyes más importantes para el ciudadano de a pie. "
        "Prioriza ayudas, impuestos, motor, vivienda y normativas generales. "
        "Formatea el resultado con emojis y puntos clave."
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
        return "⚠️ La IA no pudo procesar el texto."

def ejecutar():
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    url_api = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha_hoy}"
    
    print(f"Consultando API: {url_api}")
    response = requests.get(url_api, timeout=30)
    
    if response.status_code != 200:
        enviar_telegram(f"⏳ API en espera ({datetime.now().strftime('%d/%m')}).")
        return

    soup = BeautifulSoup(response.content, 'xml')
    
    # IMPORTANTE: Nueva lógica de extracción basada en tu ejemplo XML
    resumen_para_ia = []
    
    # Navegamos por los items del XML
    items = soup.find_all('item')
    for item in items:
        # Intentamos sacar el departamento para darle contexto a la IA
        depto = item.find_parent('departamento')
        nombre_depto = depto['nombre'] if depto and depto.has_attr('nombre') else "General"
        
        titulo = item.find('titulo')
        if titulo and titulo.text:
            resumen_para_ia.append(f"[{nombre_depto}] {titulo.text.strip()}")

    print(f"Títulos extraídos con éxito: {len(resumen_para_ia)}")

    if len(resumen_para_ia) > 0:
        # Enviamos los datos a GPT (primeros 120 títulos para no pasarnos de rosca)
        texto_ia = "\n".join(resumen_para_ia[:120])
        resumen_final = pedir_resumen_gpt(texto_ia)
        
        enviar_telegram(f"🤖 *TOP 10 BOE - {datetime.now().strftime('%d/%m')}*\n\n{resumen_final}")
    else:
        enviar_telegram("❌ Error técnico: No he podido extraer títulos del XML. Revisa la estructura.")

if __name__ == "__main__":
    ejecutar()
