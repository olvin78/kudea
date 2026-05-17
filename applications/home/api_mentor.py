from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .knowledge_base import search_knowledge
import json

@csrf_exempt
@require_POST
def mentor_query(request):
    try:
        data = json.loads(request.body)
        query = data.get('query', '')
        
        if not query:
            return JsonResponse({'error': 'No se ha proporcionado ninguna consulta.'}, status=400)
            
        # Limpiar consulta para detectar saludos comunes
        query_clean = query.lower().strip().replace("?", "").replace("¿", "").replace("!", "").replace("¡", "")
        greetings = ["hola", "buenas", "hello", "hi", "que tal", "buenos dias", "buenas tardes", "buenas noches", "quien eres", "mentor"]
        
        if query_clean in greetings:
            saludo_html = (
                "### 👋 ¡Hola! Soy **Kudea Mentor**, tu copiloto de Inteligencia de Negocio.\n\n"
                "Estoy aquí para ayudarte a dominar y operar Kudea sin esfuerzo. Puedes preguntarme sobre:\n\n"
                "1. 💰 **Ventas y TPV**: Cómo cobrar, aplicar descuentos en ticket o productos, y eliminar ítems.\n"
                "2. 🔓 **Control de Caja**: Aperturas de caja (¡ahora con PIN de seguridad!) y arqueos diarios.\n"
                "3. 📦 **Inventario y Stock**: Reponer mercancía, crear artículos y alertas de stock bajo.\n"
                "4. ⏱️ **Personal**: Fichajes QR de tus empleados y control horario.\n\n"
                "*¿En qué te puedo ayudar hoy? Escribe tu duda o haz clic en alguna de las sugerencias de abajo.*"
            )
            return JsonResponse({
                'respuesta': saludo_html,
                'tipo': 'saludo'
            })
            
        # Buscar en la memoria local
        results = search_knowledge(query)
        
        if not results:
            return JsonResponse({
                'respuesta': 'Lo siento, no tengo información específica sobre eso en mi memoria actual. ¿Podrías ser más específico?',
                'contexto': 'Intenta buscar palabras como "ventas", "iva", "descuentos" o "caja".'
            })
            
        # Formatear la respuesta del mentor
        principal = results[0]
        respuesta_texto = principal['respuesta_completa']
            
        return JsonResponse({
            'respuesta': respuesta_texto,
            'tipo': principal['tipo']
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
