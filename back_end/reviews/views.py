import json
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Review
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema

'''  esempio richiesta post
POST /reviews/get_user_reviews/?page=2&page_size=10
Content-Type: application/json
{
    "user_id": 1
}
esempio risposta:
{
    "current_page": 1,
    "total_pages": 3,
    "total_reviews": 13,
    "reviews": [
        {
            "paper_title": "Paper Title 1",
            "comment_text": "Very insightful paper!",
            "score": 5,
            "created_at": "2024-10-01T14:30:00Z"
        },
        {
            "paper_title": "Paper Title 2",
            "comment_text": "Interesting findings.",
            "score": 4,
            "created_at": "2024-09-28T10:15:00Z"
        },
    ]
}
'''
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
@api_view(['POST'])
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


'''esempio richiesta post
POST /reviews/get_paper_reviews/?page=2&page_size=10
Content-Type: application/json
{
    "user_id": 1
}
esempio di risposta json della funzione:
{
    "current_page": 1,
    "total_pages": 2,
    "total_reviews": 8,
    "reviews": [
        {
            "user": {
                "id": 3,
                "first_name": "Alice",
                "last_name": "Rossi",
                "email": "alice.rossi@example.com"
            },
            "comment_text": "Ottimo lavoro, molto interessante!",
            "score": 5,
            "created_at": "2024-10-01T14:30:00Z"
        },
        {
            "user": {
                "id": 5,
                "first_name": "Luca",
                "last_name": "Bianchi",
                "email": "luca.bianchi@example.com"
            },
            "comment_text": "Non sono d'accordo con alcune conclusioni.",
            "score": 3,
            "created_at": "2024-09-28T10:15:00Z"
        }
    ]
}
'''
@swagger_auto_schema(
    method='post',
    operation_description="Restituisce una lista di recensioni per un paper specifico con dettagli sugli utenti e paginazione.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['paper_id'],
        properties={
            'paper_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID del paper di cui si vogliono ottenere le recensioni')
        }
    ),
    manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, description="Numero della pagina per la paginazione", type=openapi.TYPE_INTEGER, default=1),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="Numero di elementi per pagina", type=openapi.TYPE_INTEGER, default=10)
    ],
    responses={
        200: openapi.Response(
            description="Lista di recensioni per il paper",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'current_page': openapi.Schema(type=openapi.TYPE_INTEGER, description="Pagina corrente"),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER, description="Numero totale di pagine"),
                    'total_reviews': openapi.Schema(type=openapi.TYPE_INTEGER, description="Numero totale di recensioni"),
                    'reviews': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'user': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID dell'utente"),
                                        'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nome dell'utente"),
                                        'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="Cognome dell'utente"),
                                        'email': openapi.Schema(type=openapi.TYPE_STRING, description="Email dell'utente")
                                    }
                                ),
                                'comment_text': openapi.Schema(type=openapi.TYPE_STRING, description="Testo della recensione"),
                                'score': openapi.Schema(type=openapi.TYPE_INTEGER, description="Punteggio assegnato al paper"),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Data di creazione della recensione")
                            }
                        )
                    )
                }
            )
        ),
        400: "Richiesta non valida",
        405: "Metodo non permesso"
    }
)
@api_view(['POST'])
@csrf_exempt
def get_paper_reviews(request): 
    """Restituisce una lista di recensioni di un paper specifico, con dettagli sugli utenti e paginazione."""

    # Verifica che la richiesta sia POST
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    # Estrai paper_id dal corpo JSON
    try:
        data = json.loads(request.body)
        paper_id = data.get("paper_id")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Verifica che paper_id sia fornito
    if not paper_id:
        return JsonResponse({"error": "Missing paper_id"}, status=400)

    # Filtra le recensioni per il paper specificato
    reviews = Review.objects.filter(paper_id=paper_id).select_related('user')

    # Ottieni i parametri di paginazione dall'URL
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 10)

    # Applica la paginazione
    paginator = Paginator(reviews, page_size)
    page_obj = paginator.get_page(page_number)

    # Costruisci i dati per la risposta JSON
    reviews_data = [
        {
            "user": {
                "id": review.user.id,
                "first_name": review.user.first_name,
                "last_name": review.user.last_name,
                "email": review.user.email
            },
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
