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
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error enviando telegram: {e}")

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
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error en GPT: {e}")
        return f"⚠️ La IA no pudo procesar el texto."

def ejecutar():
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    url_api = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha_hoy}"
    
    print(f"Consultando API: {url_api}")
    
    # Headers para que el BOE acepte la petición
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/xml, text/xml, */*',
        'Accept-Language': 'es-ES,es;q=0.9'
    }
    
    try:
        response = requests.get(url_api, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"Error {response.status_code}")
            enviar_telegram(f"⏳ BOE no disponible aún ({datetime.now().strftime('%d/%m')})")
            return
            
    except requests.exceptions.RequestException as e:
        print(f"Error de red: {e}")
        enviar_telegram(f"❌ Error de conexión al BOE")
        return
    
    try:
        soup = BeautifulSoup(response.content, 'xml')
        
        if not soup.find('sumario'):
            enviar_telegram(f"⚠️ Error en estructura del XML")
            return
        
        resumen_para_ia = []
        
        # Extraer títulos navegando la estructura XML
        secciones = soup.find_all('seccion')
        print(f"Secciones encontradas: {len(secciones)}")
        
        for seccion in secciones:
            departamentos = seccion.find_all('departamento')
            
            for depto in departamentos:
                nombre_depto = depto.get('nombre', 'Sin departamento')
                epigrafes = depto.find_all('epigrafe')
                
                for epigrafe in epigrafes:
                    items = epigrafe.find_all('item')
                    
                    for item in items:
                        titulo = item.find('titulo')
                        if titulo and titulo.text:
                            resumen_para_ia.append(f"[{nombre_depto}] {titulo.text.strip()}")
        
        print(f"Títulos extraídos: {len(resumen_para_ia)}")
        
        if len(resumen_para_ia) > 0:
            # Enviar a GPT (máximo 120 títulos)
            texto_ia = "\n".join(resumen_para_ia[:120])
            resumen_final = pedir_resumen_gpt(texto_ia)
            
            enviar_telegram(f"🤖 *TOP 10 BOE - {datetime.now().strftime('%d/%m/%Y')}*\n\n{resumen_final}")
            print("✅ Resumen enviado correctamente")
        else:
            enviar_telegram(f"⚠️ No se encontraron noticias en el BOE de hoy")
            
    except Exception as e:
        print(f"Error procesando: {e}")
        enviar_telegram(f"❌ Error al procesar el BOE")

if __name__ == "__main__":
    ejecutar()
