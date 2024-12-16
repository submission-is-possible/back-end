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
from users.decorators import get_user
from reviews.models import ReviewTemplateItem

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
POST /conference_roles/get_user_conferences/?page=2&page_size=10
Content-Type: application/json
{
    "user_id": 1
}

esempio risposta
{
    "current_page": 2,
    "total_pages": 3,
    "total_conferences": 25,
    "conferences": [
        {
            "id": 1,
            "title": "Conference 1",
            "description": "Description 1",
            "created_at": "2021-01-01T00:00:00",
            "deadline": "2021-06-01T00:00:00",
            "roles": ["admin", "author"]
        },
        {
            "id": 2,
            "title": "Conference 2",
            "description": "Description 2",
            "created_at": "2021-02-01T00:00:00",
            "deadline": "2021-07-01T00:00:00",
            "roles": ["reviewer"]
        },
        ...
    ]
}
'''



@csrf_exempt
@swagger_auto_schema(
    method='get',
    operation_description="Get conferences for a specific user with pagination.",
    responses={
        200: openapi.Response(description="Conference details or list of conferences for the user"),
        400: openapi.Response(description="Missing user_id or invalid JSON"),
        404: openapi.Response(description="Conference not found or access denied"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['GET'])
@get_user
def get_user_conferences(request):
    """Restituisce una lista di conferenze di cui l'utente fa parte con paginazione."""
    # Verifica che la richiesta sia GET
    if request.method != 'GET':
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)

        #data = json.loads(request.body)
    user = request.user #data.get("user_id")

    # Extract page number and page size for pagination from request parameters
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)

    # Filtra i ruoli conferenza per l'utente specificato e ottieni le conferenze collegate
    user_conferences = ConferenceRole.objects.filter(user=user).select_related('conference')

    # Create a data structure to organize conferences and roles
    conferences_dict = {}
    for role in user_conferences:
        conf_id = role.conference.id
        if conf_id not in conferences_dict:
            templateItems = ReviewTemplateItem.objects.filter(conference_id = conf_id )
            template = []
            for templateItem in templateItems:
                template.append({
                    'id':templateItem.id,
                    'label':templateItem.label,
                    'description':templateItem.description,
                    'has_comment':templateItem.has_comment,
                    'has_score':templateItem.has_score,
                    'comment':'',
                    'score':0,
                })
            conferences_dict[conf_id] = {
                "id": role.conference.id,
                "title": role.conference.title,
                "description": role.conference.description,
                "created_at": role.conference.created_at.isoformat(),
                "deadline": role.conference.deadline.isoformat(),
                "roles": [],
                "user_id": role.conference.admin_id.id,
                'papers_deadline': role.conference.papers_deadline,
                'status': role.conference.status,
                'reviewTemplate': template
            }
        conferences_dict[conf_id]["roles"].append(role.role)

    # Apply pagination
    paginator = Paginator(list(conferences_dict.values()), page_size)
    page_obj = paginator.get_page(page_number)

    # Create the response with the conferences for the current page
    response_data = {
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
        "total_conferences": paginator.count,
        "conferences": list(page_obj)
    }

    print(paginator.count)

    return JsonResponse(response_data, status=200)


@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Assign the role of author to a user for a specific conference.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id_user': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user'),
            'id_conference': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference')
        },
        required=['id_user', 'id_conference']
    ),
    responses={
        201: openapi.Response(description="Role assigned successfully"),
        400: openapi.Response(description="Missing fields"),
        404: openapi.Response(description="User or conference not found"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['POST'])
def assign_author_role(request):
    if request.method == 'POST':
        try:
            # Carica i dati dalla richiesta
            data = json.loads(request.body)
            user_id = data.get('id_user')
            conference_id = data.get('id_conference')

            # Verifica che tutti i campi siano presenti
            if not (user_id and conference_id):
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

            # Crea la nuova tupla nella tabella ConferenceRole
            conference_role = ConferenceRole.objects.get_or_create(
                user=user,
                conference=conference,
                role='author'
            )

            return JsonResponse({
                'message': 'Role assigned successfully'
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


