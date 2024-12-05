import json
from django.core.paginator import Paginator
from django.http import JsonResponse
from drf_yasg.openapi import Response
from rest_framework import status

from papers.models import Paper
from users.models import User
from .models import Review
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from users.decorators import get_user

import logging
logger = logging.getLogger(__name__)


'''  esempio richiesta post
GET /reviews/get_user_reviews/?page=2&page_size=10
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
    method='get',
    operation_description="Restituisce una lista di recensioni scritte dall'utente con paginazione.",
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
@api_view(['GET'])
@csrf_exempt
@get_user
def get_user_reviews(request):
    """Restituisce una lista di recensioni scritte dall'utente con paginazione."""

    # Verifica che la richiesta sia GET
    if request.method != 'GET':
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)
    
    user = request.user
    
    # Filtra le recensioni per l'utente specificato
    reviews = Review.objects.filter(user=user)
    
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
GET /reviews/get_paper_reviews/?page=2&page_size=10&paper_id=1
Content-Type: application/json
{
    "paper_id": 1
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
    method='get',
    operation_description="Restituisce una lista di recensioni per un paper specifico con dettagli sugli utenti e paginazione.",
    manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, description="Numero della pagina per la paginazione", type=openapi.TYPE_INTEGER, default=1),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="Numero di elementi per pagina", type=openapi.TYPE_INTEGER, default=10),
        openapi.Parameter('paper_id', openapi.IN_QUERY, description='ID del paper di cui si vogliono ottenere le recensioni',type=openapi.TYPE_INTEGER)
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
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Data di creazione della recensione"),
                                'confidence_level': openapi.Schema(type=openapi.TYPE_INTEGER, description="Punteggio assegnato al paper")
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
@api_view(['GET'])
@csrf_exempt
def get_paper_reviews(request): 
    """Restituisce una lista di recensioni di un paper specifico, con dettagli sugli utenti e paginazione."""

    # Verifica che la richiesta sia GET
    if request.method != 'GET':
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)

    paper_id = request.GET.get('paper_id')
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
            "confidence_level": review.confidence_level,
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


import re
## Funzione per rimuovere caratteri speciali dal nome del file
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)



@swagger_auto_schema(
    method='post',
    operation_description="Aggiunge una recensione per un paper specifico.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['paper_id', 'user_id', 'comment_text', 'score'],
        properties={
            'paper_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del paper"),
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER,
                                      description="ID dell'utente che ha scritto la recensione"),
            'comment_text': openapi.Schema(type=openapi.TYPE_STRING, description="Testo della recensione"),
            'score': openapi.Schema(type=openapi.TYPE_INTEGER, description="Punteggio assegnato al paper (1-5)",
                                    minimum=1, maximum=5),
            'confidence_level': openapi.Schema(type=openapi.TYPE_INTEGER, description="Punteggio assegnato al paper (1-5)",
                                    minimum=1, maximum=5)
        }
    ),
    responses={
        201: openapi.Response(
            description="Recensione aggiunta con successo",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'paper_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'comment_text': openapi.Schema(type=openapi.TYPE_STRING),
                    'score': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                    'confidence_level': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            )
        ),
        400: "Richiesta non valida",
        404: "Paper o utente non trovato",
        405: "Metodo non permesso"
    }
)
@api_view(['POST'])
@csrf_exempt
def create_review(request):
    """Aggiunge una recensione per un paper specifico."""
    try:
        data = request.data
        paper_id = data.get('paper_id')
        comment_text = data.get('comment_text')
        score = data.get('score')
        confidence_level = data.get('confidence_level')

        print("DEBUGGING THE CREATE NOW")
        print (request)

        if not all([paper_id, comment_text, score]):
            return JsonResponse({"error": "Tutti i campi sono obbligatori"}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(score, int) or not 1 <= score <= 5:
            return JsonResponse({"error": "Lo score deve essere un numero intero tra 1 e 5"}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(confidence_level, int) or not 1 <= confidence_level <= 5:
            return JsonResponse({"error": "Il confidence level deve essere un numero intero tra 1 e 5"}, status=status.HTTP_400_BAD_REQUEST)



        try:
            paper = Paper.objects.get(id=paper_id)
        except Paper.DoesNotExist:
            return JsonResponse({"error": "Paper non trovato"}, status=status.HTTP_404_NOT_FOUND)


        ##user = request.user
        # cancella poi, è per forzare l'utente
        user = User.objects.get(id=data.get('user_id'))

        if Review.objects.filter(paper=paper, user=user).exists():
            return JsonResponse({"error": "Hai già recensito questo paper"}, status=status.HTTP_400_BAD_REQUEST)

        review = Review.objects.create(paper=paper, user=user, comment_text=comment_text, score=score)
        return JsonResponse({
            "id": review.id,
            "paper_id": review.paper.id,
            "user_id": review.user.id,
            "comment_text": review.comment_text,
            "score": review.score,
            "confidence_level": review.confidence_level,
            "created_at": review.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)





@swagger_auto_schema(
    method='patch',
    operation_description="Aggiorna una recensione esistente.",
    manual_parameters=[
        openapi.Parameter(
            'review_id',
            openapi.IN_PATH,
            description="ID della recensione da aggiornare",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'comment_text': openapi.Schema(type=openapi.TYPE_STRING, description="Nuovo testo della recensione"),
            'score': openapi.Schema(type=openapi.TYPE_INTEGER, description="Nuovo punteggio (1-5)",
                                    minimum=1, maximum=5),
            'confidence_level': openapi.Schema(type=openapi.TYPE_INTEGER, description="Nuovo punteggio (1-5)", minimum=1, maximum=5)
        }
    ),
    responses={
        200: openapi.Response(
            description="Recensione aggiornata con successo",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'paper_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'comment_text': openapi.Schema(type=openapi.TYPE_STRING),
                    'score': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'confidence_level': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
                }
            )
        ),
        400: "Richiesta non valida",
        404: "Recensione non trovata",
        403: "Non autorizzato"
    }
)
@csrf_exempt
@api_view(['PATCH'])
def update_review(request, review_id):
    """Aggiorna una recensione esistente."""
    try:
        data = request.data
        review = Review.objects.get(id=review_id)
        print("DEBUGGING THE UPDATE NOW")
        print (request)


        # Check for user authorization
        if request.user.id != review.user.id:
            return JsonResponse({"error": "Non sei autorizzato a modificare questa recensione"},
                                status=status.HTTP_403_FORBIDDEN)


        # Update fields selectively
        if 'comment_text' in data:
            review.comment_text = data['comment_text']
        if 'score' in data:
            score = data['score']
            if not isinstance(score, int) or not 1 <= score <= 5:
                return JsonResponse({"error": "Lo score deve essere un numero intero tra 1 e 5"},
                                    status=status.HTTP_400_BAD_REQUEST)
            review.score = score
        if 'confidence_level' in data:
            confidence_level = data['confidence_level']
            if not isinstance(confidence_level, int) or not 1 <= confidence_level <= 5:
                return JsonResponse({"error": "Il confidence level deve essere un numero intero tra 1 e 5"},
                                    status=status.HTTP_400_BAD_REQUEST)
            review.confidence_level = confidence_level

        review.save(update_fields=['comment_text', 'score', 'confidence_level'])  # Save only specific fields

        # Prepare response
        return JsonResponse({
            "id": review.id,
            "paper_id": review.paper.id,
            "user_id": review.user.id,
            "comment_text": review.comment_text,
            "score": review.score,
            "confidence_level": review.confidence_level,
            "created_at": review.created_at.isoformat()
        })
    except Review.DoesNotExist:
        return JsonResponse({"error": "Recensione non trovata"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




@swagger_auto_schema(
    method='delete',
    operation_description="Elimina una recensione esistente.",
    manual_parameters=[
        openapi.Parameter(
            'review_id',
            openapi.IN_PATH,
            description="ID della recensione da eliminare",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
    ],
    responses={
        204: "Recensione eliminata con successo",
        404: "Recensione non trovata",
        403: "Non autorizzato"
    }
)
@api_view(['DELETE'])
@csrf_exempt
def delete_review(request, review_id):
    """Elimina una recensione esistente."""
    try:
        print("==== DEBUG DELETE REVIEW ====")
        print(f"Request User: {request.user}")
        print(f"Request User ID: {request.user.id}")
        print(f"Is authenticated: {request.user.is_authenticated}")

        review = Review.objects.get(id=review_id)
        print(f"Review User ID: {review.user.id}")
        print(f"Are IDs equal?: {request.user.id == review.user.id}")
        print("========================")



        if request.user.id != review.user.id:
            return JsonResponse({"error": "Non sei autorizzato a eliminare questa recensione"},
                                status=status.HTTP_403_FORBIDDEN)


        review.delete()
        return JsonResponse({}, status=status.HTTP_204_NO_CONTENT)

    except Review.DoesNotExist:
        return JsonResponse({"error": "Recensione non trovata"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Exception in delete_review: {str(e)}")
        return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




## function that given a review ID, returns the score

@swagger_auto_schema(
    method='get',
    operation_description="Restituisce il punteggio di una recensione dato il suo ID.",
    manual_parameters=[
        openapi.Parameter(
            'review_id',
            openapi.IN_PATH,
            description="ID della recensione di cui si vuole ottenere il punteggio",
            type=openapi.TYPE_INTEGER,
            required=True
        ),
    ],
    responses={
        200: openapi.Response(
            description="Punteggio della recensione",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'score': openapi.Schema(type=openapi.TYPE_INTEGER, description="Punteggio della recensione")
                }
            )
        ),
        404: "Recensione non trovata",
        400: "Richiesta non valida"
    }
)
@api_view(['GET'])
@csrf_exempt
def get_review_score(request, review_id):
    """Restituisce il punteggio di una recensione dato il suo ID."""
    try:
        # Recupera la recensione tramite l'ID
        review = Review.objects.get(id=review_id)

        # Prepara e restituisce la risposta con il punteggio
        return JsonResponse({"score": review.score}, status=status.HTTP_200_OK)
    except Review.DoesNotExist:
        # Se la recensione non esiste, restituisce un errore 404
        return JsonResponse({"error": "Recensione non trovata"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Per eventuali altri errori, restituisce un errore generico
        return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


