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
