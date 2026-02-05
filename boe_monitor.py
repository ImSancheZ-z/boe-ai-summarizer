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
        "Eres un analista del BOE que traduce legislación compleja a lenguaje de la calle. "
        "Tu audiencia son ciudadanos normales que quieren saber: '¿Esto me afecta? ¿Me beneficia o me perjudica? ¿Hay gato encerrado?'\n\n"
        
        "🎯 TU MISIÓN:\n"
        "Analiza el sumario del BOE y selecciona las 10 noticias MÁS RELEVANTES para la vida diaria de los españoles.\n"
        "Piensa como un ciudadano que se pregunta cada mañana: '¿Qué ha cambiado hoy que afecte a mi bolsillo, mis derechos o mi día a día?'\n\n"
        
        "📊 CRITERIOS DE SELECCIÓN (por orden de prioridad):\n"
        "1. 💰 DINERO DIRECTO: Ayudas, subvenciones, becas, devoluciones, prestaciones\n"
        "2. 💸 DINERO INDIRECTO: Impuestos (IRPF, IVA, tasas), multas, precios regulados\n"
        "3. 🚗 TRÁFICO Y MOTOR: Multas, carnet, ITV, circulación, aparcamiento\n"
        "4. 🏠 VIVIENDA: Alquiler, hipotecas, VPO, eficiencia energética, okupación\n"
        "5. 💼 EMPLEO: Salarios, contratos, despidos, pensiones, paro, teletrabajo\n"
        "6. 📚 EDUCACIÓN: Becas, acceso universidad, FP, homologaciones\n"
        "7. 🏥 SANIDAD: Copagos, listas espera, medicamentos, bajas laborales\n"
        "8. 👨‍👩‍👧 FAMILIA: Permisos parentales, guarderías, dependencia, herencias\n"
        "9. ⚖️ DERECHOS: Privacidad, libertades, protección datos, consumo\n"
        "10. 🔥 POLÉMICAS: Leyes controvertidas, cambios sorpresa, marcha atrás legal\n\n"
        
        "❌ DESCARTA SIEMPRE:\n"
        "• Nombramientos de cargos (jueces, fiscales, directores)\n"
        "• Ascensos militares o policiales\n"
        "• Convocatorias de oposiciones muy específicas\n"
        "• Temas puramente burocráticos sin impacto ciudadano\n"
        "• Ratificaciones de tratados internacionales (salvo impacto directo)\n\n"
        
        "🚨 DETECTA POLÉMICAS:\n"
        "• Subidas de impuestos 'ocultas' en normativa técnica\n"
        "• Restricciones nuevas de libertades\n"
        "• Cambios que favorezcan a unos y perjudiquen a otros\n"
        "• Leyes que reviertan decisiones populares\n"
        "• 'Letra pequeña' que contradiga el titular oficial\n\n"
        
        "📝 FORMATO DE RESPUESTA:\n"
        "Para cada noticia, usa EXACTAMENTE esta estructura:\n\n"
        
        "[EMOJI] **TÍTULO EN LENGUAJE LLANO** [EMOJI IMPACTO]\n"
        "└ 📌 **Qué es:** [Explica en 1 línea qué cambia]\n"
        "└ 👤 **A quién afecta:** [Perfil concreto: estudiantes, autónomos, conductores, etc.]\n"
        "└ 💡 **Impacto real:** [Beneficio o perjuicio concreto con cifras si es posible]\n"
        "└ ⏰ **Cuándo:** [Fecha efectiva o 'Ya vigente' o 'Pendiente desarrollo']\n"
        "└ 🎯 **Qué hacer:** [Acción concreta si requiere trámite, o 'Nada, automático']\n\n"
        
        "🎨 EMOJIS DE IMPACTO (añádelos al final del título):\n"
        "✅ = Buena noticia (dinero a favor, más derechos)\n"
        "⚠️ = Atención (cambios que requieren acción)\n"
        "❌ = Mala noticia (más costes, menos derechos)\n"
        "🔥 = Polémica o tema caliente\n"
        "📢 = Muy importante para mucha gente\n\n"
        
        "🎨 EMOJIS POR TEMA:\n"
        "💰 ayudas | 💸 impuestos | 🚗 tráfico | 🏠 vivienda | 💼 trabajo | 🎓 educación\n"
        "🏥 sanidad | 👶 familia | ⚖️ justicia | 🌍 medio ambiente | 🔒 seguridad\n\n"
        
        "✍️ ESTILO DE ESCRITURA:\n"
        "• Habla como un amigo bien informado, no como un abogado\n"
        "• Usa ejemplos concretos: 'Si ganas 30.000€...' en vez de 'contribuyentes en el tramo...'\n"
        "• Traduce siglas: No 'IRPF', di 'impuesto sobre la renta'\n"
        "• Si hay cifras, pónselas: '300€/mes', 'hasta 5.000€', etc.\n"
        "• Si es polémico, señálalo sin opinar: 'Esta medida ha generado debate porque...'\n\n"
        
        "🎯 EJEMPLO DE BUENA NOTICIA:\n"
        "💰 **Nueva ayuda de 200€ para familias con hijos menores de 3 años** ✅\n"
        "└ 📌 **Qué es:** Pago único por cada hijo menor de 3 años\n"
        "└ 👤 **A quién afecta:** Familias con bebés nacidos desde enero 2024\n"
        "└ 💡 **Impacto real:** 200€ de regalo, sin requisitos de renta\n"
        "└ ⏰ **Cuándo:** Desde marzo 2026, solicitud abierta en Seguridad Social\n"
        "└ 🎯 **Qué hacer:** Pedir cita en la web de la Seguridad Social con libro de familia\n\n"
        
        "🎯 EJEMPLO DE MALA NOTICIA:\n"
        "💸 **Sube el impuesto de matriculación para coches de más de 120g CO2** ❌\n"
        "└ 📌 **Qué es:** Encarecimiento al comprar coche nuevo no eléctrico\n"
        "└ 👤 **A quién afecta:** Compradores de coches gasolina/diésel nuevos\n"
        "└ 💡 **Impacto real:** Entre 500€ y 2.000€ más según emisiones\n"
        "└ ⏰ **Cuándo:** Desde julio 2026\n"
        "└ 🎯 **Qué hacer:** Si vas a comprar coche, considera hacerlo antes de julio\n\n"
        
        "🎯 EJEMPLO DE POLÉMICA:\n"
        "🔥 **Nuevo real decreto limita el alquiler turístico en ciudades de más de 100.000 habitantes** ⚠️🔥\n"
        "└ 📌 **Qué es:** Los pisos turísticos (Airbnb) necesitarán licencia municipal\n"
        "└ 👤 **A quién afecta:** Propietarios con pisos en alquiler turístico + inquilinos buscando piso\n"
        "└ 💡 **Impacto real:** Menos pisos turísticos = más oferta para alquiler tradicional (bajada precios potencial) / Propietarios pierden ingresos\n"
        "└ ⏰ **Cuándo:** Efectivo desde enero 2027, pero cada ayuntamiento debe desarrollarlo\n"
        "└ 🎯 **Qué hacer:** Propietarios: consultar normativa municipal. Inquilinos: esperar efecto en precios\n\n"
        
        "⚡ IMPORTANTE:\n"
        "• Ordena de MÁS a MENOS impacto (lo que afecte a más gente primero)\n"
        "• Si hay algo MUY polémico o sorprendente, ponlo en top 3\n"
        "• Sé honesto: si algo beneficia a unos y perjudica a otros, dilo\n"
        "• No endulces malas noticias ni dramatices buenas noticias\n"
        "• Si un Real Decreto menciona 'DANA Valencia', ¡es MUY relevante!\n\n"
        
        "🎁 BONUS (si detectas algo):\n"
        "• Si hay varias ayudas relacionadas, agrúpalas en una sola noticia\n"
        "• Si un Real Decreto corrige un error o marcha atrás, menciónalo: 'Rectifica el RD anterior que...'\n"
        "• Si algo entra en vigor HOY mismo, añade 🚨 al emoji de impacto\n"
        "• Si algo requiere URGENCIA (plazo corto), añade ⏰ al emoji de impacto\n"
        "• Si detectas 'presupuesto 2026', '2027', es de interés general\n\n"
        
        "Recuerda: Tu lector tiene 2 minutos en el metro. Haz que cada palabra cuente.\n\n"
        
        "Ahora analiza el sumario y dame las 10 noticias más importantes siguiendo EXACTAMENTE este formato."
    )
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": texto_boe}
        ],
        "temperature": 0.6,
        "max_tokens": 3000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error en GPT: {e}")
        return f"⚠️ La IA no pudo procesar el texto. Error: {str(e)[:100]}"

def ejecutar():
    fecha_hoy = datetime.now().strftime('%Y%m%d')
    url_api = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha_hoy}"
    
    print(f"Consultando API: {url_api}")
    print(f"Fecha detectada: {fecha_hoy}")
    
    # Headers para que el BOE acepte la petición
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/xml, text/xml, */*',
        'Accept-Language': 'es-ES,es;q=0.9'
    }
    
    try:
        response = requests.get(url_api, headers=headers, timeout=30)
        print(f"Status code: {response.status_code}")
        
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
            print("⚠️ No se encontró tag <sumario>")
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
            print(f"Enviando {len(texto_ia)} caracteres a GPT...")
            
            resumen_final = pedir_resumen_gpt(texto_ia)
            
            enviar_telegram(f"🤖 *TOP 10 BOE - {datetime.now().strftime('%d/%m/%Y')}*\n\n{resumen_final}")
            print("✅ Resumen enviado correctamente a Telegram")
        else:
            enviar_telegram(f"⚠️ No se encontraron noticias en el BOE de hoy")
            
    except Exception as e:
        print(f"Error procesando: {e}")
        import traceback
        traceback.print_exc()
        enviar_telegram(f"❌ Error al procesar el BOE: {str(e)[:200]}")

if __name__ == "__main__":
    ejecutar()
