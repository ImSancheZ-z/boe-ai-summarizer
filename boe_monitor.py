import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta

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
        return f"⚠️ La IA no pudo procesar el texto. Error: {str(e)[:100]}"

def obtener_boe(fecha):
    """Intenta obtener el BOE de una fecha específica"""
    fecha_str = fecha.strftime('%Y%m%d')
    url_api = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha_str}"
    
    print(f"Consultando API: {url_api}")
    
    try:
        response = requests.get(url_api, timeout=30)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            return response, fecha
        else:
            return None, None
            
    except Exception as e:
        print(f"Error en petición: {e}")
        return None, None

def ejecutar():
    # Intentar primero con hoy
    hoy = datetime.now()
    response, fecha_usada = obtener_boe(hoy)
    
    # Si falla, intentar con ayer
    if response is None:
        print("BOE de hoy no disponible, intentando con ayer...")
        ayer = hoy - timedelta(days=1)
        response, fecha_usada = obtener_boe(ayer)
    
    # Si ninguno funciona, avisar y salir
    if response is None:
        enviar_telegram(f"⏳ BOE aún no publicado ({hoy.strftime('%d/%m')}). Reintentando más tarde...")
        return
    
    print(f"✅ BOE obtenido correctamente para {fecha_usada.strftime('%d/%m/%Y')}")
    
    try:
        soup = BeautifulSoup(response.content, 'xml')
        
        # Verificar que el XML se parseó correctamente
        if not soup.find('sumario'):
            print("⚠️ No se encontró el tag <sumario> en el XML")
            enviar_telegram(f"⚠️ Estructura XML inesperada ({fecha_usada.strftime('%d/%m')})")
            return
        
        resumen_para_ia = []
        
        # Navegamos por las secciones
        secciones = soup.find_all('seccion')
        print(f"Secciones encontradas: {len(secciones)}")
        
        for seccion in secciones:
            nombre_seccion = seccion.get('nombre', 'Sin sección')
            
            # Dentro de cada sección, buscamos departamentos
            departamentos = seccion.find_all('departamento')
            
            for depto in departamentos:
                nombre_depto = depto.get('nombre', 'Sin departamento')
                
                # Dentro de cada departamento, buscamos epígrafes
                epigrafes = depto.find_all('epigrafe')
                
                for epigrafe in epigrafes:
                    # Dentro de cada epígrafe, buscamos items
                    items = epigrafe.find_all('item')
                    
                    for item in items:
                        titulo = item.find('titulo')
                        if titulo and titulo.text:
                            # Formato: [Departamento] Título
                            resumen_para_ia.append(f"[{nombre_depto}] {titulo.text.strip()}")
        
        print(f"Títulos extraídos: {len(resumen_para_ia)}")
        
        if len(resumen_para_ia) > 0:
            # Enviamos los datos a GPT (primeros 120 títulos)
            texto_ia = "\n".join(resumen_para_ia[:120])
            resumen_final = pedir_resumen_gpt(texto_ia)
            
            # Indicar si es de hoy o de ayer
            emoji_fecha = "📅" if fecha_usada.date() == hoy.date() else "📆"
            enviar_telegram(f"🤖 *TOP 10 BOE - {fecha_usada.strftime('%d/%m')}* {emoji_fecha}\n\n{resumen_final}")
        else:
            enviar_telegram(f"❌ No se extrajeron títulos del XML ({fecha_usada.strftime('%d/%m')})")
            
    except Exception as e:
        print(f"Error procesando XML: {e}")
        import traceback
        traceback.print_exc()
        enviar_telegram(f"❌ Error procesando datos: {str(e)[:100]}")

if __name__ == "__main__":
    ejecutar()
