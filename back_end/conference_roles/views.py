import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

from users.models import User
from .models import Conference, ConferenceRole
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
'''esempio richiesta post
{
    "id_user": 1,
    "id_conference": 3,
    "role_user": "reviewer"
}
'''
@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Create a new conference role for a user.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id_user': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user'),
            'id_conference': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference'),
            'role_user': openapi.Schema(type=openapi.TYPE_STRING, description='Role of the user in the conference')
        },
        required=['id_user', 'id_conference', 'role_user']
    ),
    responses={
        201: openapi.Response(description="Role added successfully"),
        400: openapi.Response(description="Missing fields or invalid role"),
        404: openapi.Response(description="User or conference not found"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['POST'])
def create_conference_role(request):
    if request.method == 'POST':
        try:
            # Carica i dati dalla richiesta
            data = json.loads(request.body)
            user_id = data.get('id_user')
            conference_id = data.get('id_conference')
            role = data.get('role_user')

            # Verifica che tutti i campi siano presenti
            if not (user_id and conference_id and role):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            # Verifica se l'utente esiste
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

            # Verifica se la conferenza esiste
            try:
                conference = Conference.objects.get(id=conference_id)
            except Conference.DoesNotExist:
                return JsonResponse({'error': 'Conference not found'}, status=404)

            # Verifica se il ruolo è valido
            valid_roles = dict(ConferenceRole.ROLE_CHOICES).keys()
            if role not in valid_roles:
                return JsonResponse({'error': 'Invalid role'}, status=400)

            # Crea la nuova tupla nella tabella ConferenceRole
            conference_role = ConferenceRole.objects.create(
                user=user,
                conference=conference,
                role=role
            )

            return JsonResponse({
                'message': 'Role added successfully',
                'conference_role_id': conference_role.id
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


'''  esempio richiesta post
POST /user/conferences/?page=2&page_size=10
Content-Type: application/json
{
    "user_id": 1
}
'''
@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Get conferences for a specific user with pagination.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user')
        },
        required=['user_id']
    ),
    responses={
        200: openapi.Response(description="List of conferences for the user"),
        400: openapi.Response(description="Missing user_id or invalid JSON"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['POST'])
def get_user_conferences(request):
    """Restituisce una lista di conferenze di cui l'utente fa parte con paginazione."""

    # Verifica che la richiesta sia POST
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    # Parse del corpo della richiesta per ottenere user_id
    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Verifica che user_id sia fornito
    if not user_id:
        return JsonResponse({"error": "Missing user_id"}, status=400)

    # Estrai il numero di pagina e il limite per la paginazione dai parametri della richiesta
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)

    # Filtra i ruoli conferenza per l'utente specificato e ottieni le conferenze collegate
    user_conferences = ConferenceRole.objects.filter(user_id=user_id).select_related('conference')
    conferences = [role.conference for role in user_conferences]

    # Applica la paginazione
    paginator = Paginator(conferences, page_size)
    page_obj = paginator.get_page(page_number)

    # Crea la risposta con le conferenze per la pagina corrente
    response_data = {
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
        "total_conferences": paginator.count,
        "conferences": [
            {
                "id": conference.id,
                "title": conference.title,
                "description": conference.description,
                "created_at": conference.created_at.isoformat(),
                "deadline": conference.deadline.isoformat(),
            }
            for conference in page_obj
        ],
    }
    return JsonResponse(response_data, status=200)