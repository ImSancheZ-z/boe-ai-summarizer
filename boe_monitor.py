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
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # El prompt es la clave: le pedimos que sea útil para el ciudadano
    prompt = (
        "Eres un analista experto en el BOE. De la siguiente lista de títulos, "
        "selecciona y resume los 5 más importantes para el ciudadano medio (ayudas, impuestos, motor, vivienda). "
        "Usa un tono informativo pero directo. Estructura con puntos y emojis."
    )
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": texto_boe}
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ Error con GPT: {str(e)}"

def ejecutar():
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    url_xml = f"https://www.boe.es/diario_boe/xml.php?id=BOE-S-{fecha_hoy}"
    
    response = requests.get(url_xml)
    if response.status_code != 200:
        print("BOE no disponible.")
        return

    soup = BeautifulSoup(response.content, 'xml')
    # Extraemos todos los títulos del sumario
    titulos = [item.find('titulo').text for item in soup.find_all('item') if item.find('titulo')]
    
    # Filtro de seguridad para no enviar 500 páginas a la IA
    palabras_clave = ["ayuda", "subvención", "impuesto", "tráfico", "vehículo", "carretera", "vivienda", "empleo", "pensiones", "motos"]
    interesantes = [t for t in titulos if any(k in t.lower() for k in palabras_clave)]

    if interesantes:
        resumen = pedir_resumen_gpt("\n".join(interesantes))
        enviar_telegram(f"🗞 *RESUMEN INTELIGENTE BOE ({datetime.now().strftime('%d/%m')})*\n\n{resumen}")
    else:
        print("Hoy no hay temas de interés según las palabras clave.")

if __name__ == "__main__":
    ejecutar()
