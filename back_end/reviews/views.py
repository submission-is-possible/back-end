import json
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Review
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

@swagger_auto_schema(
    method='post',
    operation_description="Restituisce una lista di recensioni scritte dall'utente con paginazione.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID dell\'utente'),
        },
        required=['user_id'],
    ),
    responses={
        200: openapi.Response(
            description="Lista di recensioni dell'utente",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "current_page": openapi.Schema(type=openapi.TYPE_INTEGER, description="Pagina corrente"),
                    "total_pages": openapi.Schema(type=openapi.TYPE_INTEGER, description="Numero totale di pagine"),
                    "total_reviews": openapi.Schema(type=openapi.TYPE_INTEGER, description="Numero totale di recensioni"),
                    "reviews": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "paper_title": openapi.Schema(type=openapi.TYPE_STRING, description="Titolo del paper"),
                                "comment_text": openapi.Schema(type=openapi.TYPE_STRING, description="Contenuto della recensione"),
                                "score": openapi.Schema(type=openapi.TYPE_INTEGER, description="Punteggio della recensione"),
                                "created_at": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Data di creazione della recensione"),
                            },
                        ),
                    ),
                },
            ),
        ),
        400: "Bad Request",
        405: "Method Not Allowed",
    },
    manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, description="Numero della pagina", type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="Dimensione della pagina", type=openapi.TYPE_INTEGER),
    ]
)
@csrf_exempt
def get_user_reviews(request):
    """Restituisce una lista di recensioni scritte dall'utente con paginazione."""

    # Verifica che la richiesta sia POST
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
    
    # Estrai user_id dal corpo JSON
    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    # Verifica che user_id sia fornito
    if not user_id:
        return JsonResponse({"error": "Missing user_id"}, status=400)
    
    # Filtra le recensioni per l'utente specificato
    reviews = Review.objects.filter(user_id=user_id)
    
    # Ottieni i parametri di paginazione dall'URL
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 10)
    
    # Applica la paginazione
    paginator = Paginator(reviews, page_size)
    page_obj = paginator.get_page(page_number)
    
    # Costruisci i dati per la risposta JSON
    reviews_data = [
        {
            "paper_title": review.paper.title,
            "comment_text": review.comment_text,
            "score": review.score,
            "created_at": review.created_at.isoformat()
        }
        for review in page_obj
    ]
    
    response_data = {
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
        "total_reviews": paginator.count,
        "reviews": reviews_data
    }
    
    return JsonResponse(response_data, status=200)
