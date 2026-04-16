import json, requests, datetime, os, sys

GEMINI_KEY = os.environ['GEMINI_KEY']
JSONBIN_KEY = os.environ['JSONBIN_KEY']
REPORTES_BIN = os.environ['REPORTES_BIN']
TRACKER_BIN = os.environ['TRACKER_BIN']

HEADERS_BIN = {'X-Master-Key': JSONBIN_KEY, 'Content-Type': 'application/json'}

EQUIPO_DATA = {
    'Agustin':  {'equipo':'Guion','rol':'Guionista','horario':'9-17hs','esperado':'20-25 guiones/semana + notas + placas','tareas':'4-5 guiones por dia, una nota por guion, una placa prediseniada por guion'},
    'Juan':     {'equipo':'Guion','rol':'Guionista','horario':'9-17hs','esperado':'20-25 guiones/semana + notas + placas + twitter','tareas':'4-5 guiones por dia, twitter, notas propias + las de Alfredo, placas propias + las de Alfredo'},
    'Alfredo':  {'equipo':'Guion','rol':'Guionista/Tecnico/Locutor','horario':'9-15.30/16hs','esperado':'19 guiones/semana + tecnica + grabaciones','tareas':'Asegura funcionamiento estudios, 3 guiones antes del almuerzo, ~19 guiones/semana, grabaciones'},
    'Clara':    {'equipo':'Digital','rol':'CM','horario':'14-17/18hs (part-time)','esperado':'Copies diarios + 4 placas/semana + informes + programacion redes','tareas':'Copy por video, programar videos en redes, placas (4/semana), informes jueves y viernes, Abzurdo de la semana, tema marca'},
    'Malena':   {'equipo':'Digital','rol':'Disenadora','horario':'14-17/18hs o 9.15-13hs (part-time)','esperado':'Portadas + 4 placas/semana + newsletter + 5 noticias + informes','tareas':'Portadas, calendarizar videos, placas, newsletter, 5 noticias, informes jueves y viernes, tema marca'},
    'Sofia':    {'equipo':'Digital','rol':'Lider','horario':'10-17hs','esperado':'Liderazgo activo: temas + decisiones editoriales + correcciones + marca','tareas':'Busqueda de temas, reorganizacion del dia, decisiones de contenido, correcciones, marca, calendarizacion, supervisar informes'},
    'Candela':  {'equipo':'Produccion','rol':'Productora','horario':'9.30-10.15 / 17-18.20hs','esperado':'32 videos producidos/semana + coordinacion CP + recursos','tareas':'Organiza videos, coordina CP, pasa crudos, busca recursos para editores, coyunturas, 32 videos/semana'},
    'Luciana':  {'equipo':'Produccion','rol':'Productora','horario':'9/9.30-17hs','esperado':'32 videos producidos/semana + coordinacion CP + recursos','tareas':'Organiza videos, coordina CP, pasa crudos, busqueda de recursos, coyunturas, 32 videos/semana'},
    'Manuel':   {'equipo':'Paid Media','rol':'Paid Media','horario':'9/9.20-17hs','esperado':'100-150 pautas/semana en Meta/Google/TikTok/YT + informes','tareas':'Chequeo pauta, armar pautado, planificar presupuesto, pautar 100-150/semana, informes, diagrama prioridades jueves'},
    'Victoria': {'equipo':'Paid Media','rol':'Paid Media','horario':'8-9 / 15-17hs (jornada completa flexible)','esperado':'100-150 pautas/semana en Meta/Google/TikTok/YT + informes','tareas':'Chequeo pauta, armar pautado, planificar presupuesto, pautar 100-150/semana, informes'},
}

# Nombres alternativos por si tienen tilde en el tracker
NOMBRE_MAP = {
    'Agust\u00edn': 'Agustin',
    'Sof\u00eda': 'Sofia',
}

def get_week_key(date):
    day = date.weekday()
    days_to_friday = (day - 4) % 7
    friday = date - datetime.timedelta(days=days_to_friday)
    return friday.strftime('%Y-%m-%d')

def week_label(key):
    d = datetime.datetime.strptime(key, '%Y-%m-%d')
    end = d + datetime.timedelta(days=6)
    return f"{d.strftime('%d/%m')}-{end.strftime('%d/%m')}"

def jsonbin_get(bin_id):
    r = requests.get(f'https://api.jsonbin.io/v3/b/{bin_id}/latest', headers=HEADERS_BIN)
    r.raise_for_status()
    return r.json()

def jsonbin_put(bin_id, data):
    r = requests.put(f'https://api.jsonbin.io/v3/b/{bin_id}', headers=HEADERS_BIN, json=data)
    r.raise_for_status()
    return r.json()

today = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
prev_week = get_week_key(today - datetime.timedelta(weeks=1))
label = week_label(prev_week)
print(f"Semana a analizar: {label} ({prev_week})")

tracker_resp = jsonbin_get(TRACKER_BIN)
tracker = tracker_resp['record'].get('datos', {})

reportes_resp = jsonbin_get(REPORTES_BIN)
reportes_data = reportes_resp['record'].get('reportes', {})

if prev_week in reportes_data:
    print("Reporte ya existe. Saliendo.")
    sys.exit(0)

personas = []
for nombre_tracker, user_data in tracker.items():
    if nombre_tracker == '__inactive':
        continue
    nombre_key = NOMBRE_MAP.get(nombre_tracker, nombre_tracker)
    info = EQUIPO_DATA.get(nombre_key)
    if not info:
        print(f"Usuario no encontrado en EQUIPO_DATA: {nombre_tracker}")
        continue
    semana = user_data.get(prev_week)
    if not semana:
        continue
    objs = semana.get('objetivos', [])
    confs = semana.get('confirmaciones', [])
    cumplidos = sum(1 for c in confs if c.get('cumplido'))
    no_cumplidos = sum(1 for c in confs if not c.get('cumplido'))
    justificaciones = [c.get('justificacion', '') for c in confs if not c.get('cumplido') and c.get('justificacion')]
    personas.append({
        'nombre': nombre_tracker,
        'equipo': info['equipo'],
        'rol': info['rol'],
        'horario': info['horario'],
        'esperado': info['esperado'],
        'tareas': info['tareas'],
        'objetivos': objs,
        'cumplidos': cumplidos,
        'no_cumplidos': no_cumplidos,
        'sin_confirmar': len(objs) - len(confs),
        'justificaciones': justificaciones,
        'total_objetivos': len(objs)
    })

if not personas:
    print("No hay datos de personas para esta semana. Saliendo.")
    sys.exit(0)

print(f"Personas encontradas: {[p['nombre'] for p in personas]}")

prompt = f"""Sos un agente senior especializado en analisis de performance, productividad y rendimiento de equipos de trabajo. Tu analisis es directo, real, sin suavizar nada. Cuando algo esta mal lo decis. Cuando algo esta bien tambien.

CONTEXTO DEL EQUIPO - RATIO:
{json.dumps(EQUIPO_DATA, ensure_ascii=False, indent=2)}

DATOS DE LA SEMANA {label}:
{json.dumps(personas, ensure_ascii=False, indent=2)}

Genera un analisis completo en formato JSON con esta estructura exacta. Usa comillas dobles para todas las claves y valores de string. No uses caracteres especiales que rompan el JSON:
{{
  "semana": "{label}",
  "equipos": [
    {{
      "nombre": "nombre del equipo",
      "integrantes": [
        {{
          "nombre": "nombre",
          "cumplimiento": "analisis del nivel de cumplimiento de objetivos",
          "productividad": "analisis de productividad esperada vs lograda",
          "balance": "balance real de la semana directo y sin filtros",
          "score": 7,
          "sugerencias": ["sugerencia 1", "sugerencia 2"],
          "calidad_objetivos": "evaluacion de si los objetivos son claros medibles exigentes y suficientes"
        }}
      ],
      "mvp": {{
        "nombre": "nombre del MVP",
        "justificacion": "por que es el MVP de la semana"
      }},
      "balance_area": "analisis del area como unidad como estuvo la semana"
    }}
  ],
  "analisis_general": {{
    "analisis_cuali": "analisis cualitativo del equipo completo directo y real",
    "balance": "positivo",
    "score_semana": 7,
    "sugerencias": ["sugerencia 1", "sugerencia 2", "sugerencia 3"]
  }},
  "alertas": [
    {{
      "titulo": "titulo de la alerta",
      "descripcion": "descripcion de que esta pasando y por que es urgente"
    }}
  ]
}}

Responde SOLO con el JSON valido, sin texto adicional, sin markdown, sin backticks."""

gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_KEY}'
gemini_body = {
    'contents': [{'parts': [{'text': prompt}]}],
    'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 8000}
}

print("Llamando a Gemini...")
resp = requests.post(gemini_url, json=gemini_body)
resp.raise_for_status()
data = resp.json()

text = data['candidates'][0]['content']['parts'][0]['text']
text = text.replace('```json', '').replace('```', '').strip()

print("Respuesta recibida, parseando JSON...")
analisis = json.loads(text)
print("JSON parseado correctamente.")

reportes_data[prev_week] = analisis
jsonbin_put(REPORTES_BIN, {'reportes': reportes_data})
print(f"Reporte guardado para semana {prev_week}.")
