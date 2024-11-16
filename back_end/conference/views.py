import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from users.models import User  # Importa il modello User dall'app users
from .models import Conference  # Importa il modello Conference creato in precedenza
from conference_roles.models import ConferenceRole
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view
from users.decorators import get_user



@csrf_exempt  # Disabilita temporaneamente il controllo CSRF (per sviluppo locale)
@swagger_auto_schema(
    method='post',
    operation_description="Create a new conference with title, admin_id, deadline, and description.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING, description='Title of the conference'),
            'admin_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference admin'),
            'deadline': openapi.Schema(type=openapi.TYPE_STRING, description='Deadline for the conference'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description of the conference'),
        },
        required=['title', 'admin_id', 'deadline', 'description']
    ),
    responses={
        201: openapi.Response(description="Conference created successfully"),
        400: openapi.Response(description="Missing fields or request body is not valid JSON"),
        404: openapi.Response(description="Admin user not found"),
        405: openapi.Response(description="Only POST requests are allowed"),
    }
)
@api_view(['POST'])
@get_user
def create_conference(request):
    if request.method == 'POST':
        try:
            # Estrai i dati dal body della richiesta
            data = json.loads(request.body)
            title = data.get('title')
            admin_user = request.user
            deadline = data.get('deadline')
            description = data.get('description')

            # Verifica che i campi richiesti siano presenti
            if not (title and deadline and description):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            # Crea la nuova conferenza
            conference = Conference.objects.create(
                title=title,
                admin_id=admin_user,
                created_at=timezone.now(),
                deadline=deadline,
                description=description
            )

            # Crea il ruolo di amministratore per l'utente, crea la tupla nella tabella ConferenceRole
            ConferenceRole.objects.create(
                user=admin_user,
                conference=conference,
                role='admin'
            )

            return JsonResponse({
                'message': 'Conference created successfully',
                'conference_id': conference.id
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a conference by providing the conference_id.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference to delete'),
        },
        required=['conference_id']
    ),
    responses={
        200: openapi.Response(description="Conference deleted successfully"),
        400: openapi.Response(description="Missing conference_id or user_id, or request body is not valid JSON"),
        403: openapi.Response(description="Permission denied. User is not an admin of this conference."),
        404: openapi.Response(description="Conference not found"),
        405: openapi.Response(description="Only POST requests are allowed"),
    }
)
@api_view(['DELETE'])
@get_user
def delete_conference(request):

    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            conference_id = data.get('conference_id')
            user = request.user  #`user_id` deve essere fornito per verificare i permessi dell'utente,
            # se l'utente è admin della conferenza, può eliminarla

            # Verifica che l'ID della conferenza e l'ID utente siano forniti
            if not conference_id:
                return JsonResponse({'error': 'Missing conference_id'}, status=400)

            # Controlla se l'utente ha il ruolo di admin per la conferenza
            try:
                conference = Conference.objects.get(conference_id=conference_id)
                is_admin = ConferenceRole.objects.filter(
                    conference=conference,
                    user=user,
                    role='admin'
                ).exists()

                if not is_admin:
                    return JsonResponse({'error': 'Permission denied. User is not an admin of this conference.'}, status=403)

                # Elimina tutti i ruoli associati alla conferenza in ConferenceRole
                ConferenceRole.objects.filter(conference=conference).delete()

                # Elimina la conferenza se l'utente è admin
                conference.delete()
                return JsonResponse({'message': 'Conference deleted successfully'}, status=200)
            except Conference.DoesNotExist:
                return JsonResponse({'error': 'Conference not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
@swagger_auto_schema(
    method='patch',
    operation_description="Edit (update) a conference by providing its ID and optional fields to update.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference to update'),
            'title': openapi.Schema(type=openapi.TYPE_STRING, description='New title of the conference'),
            'deadline': openapi.Schema(type=openapi.TYPE_STRING, description='New deadline for the conference (ISO format)'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='New description of the conference'),
        },
        required=['conference_id']
    ),
    responses={
        200: openapi.Response(description="Conference updated successfully"),
        400: openapi.Response(description="Missing conference_id or request body is not valid JSON"),
        404: openapi.Response(description="Conference not found"),
        403: openapi.Response(description="Permission denied"),
        405: openapi.Response(description="Only PATCH requests are allowed"),
    }
)
@api_view(['PATCH'])
def edit_conference(request):
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            conference_id = data.get('conference_id')
            title = data.get('title')
            deadline = data.get('deadline')
            description = data.get('description')

            # Verifica che conference_id sia presente
            if not conference_id:
                return JsonResponse({'error': 'Missing conference_id'}, status=400)

            # Verifica che la conferenza esista
            try:
                conference = Conference.objects.get(id=conference_id)
            except Conference.DoesNotExist:
                return JsonResponse({'error': 'Conference not found'}, status=404)

            # Esegui il controllo del ruolo admin per l'utente, come in delete_conference
            user_id = data.get('user_id')
            if not user_id:
                return JsonResponse({'error': 'Missing user_id'}, status=400)
            is_admin = ConferenceRole.objects.filter(
                conference=conference,
                user_id=user_id,
                role='admin'
            ).exists()
            if not is_admin:
                return JsonResponse({'error': 'Permission denied. User is not an admin of this conference.'}, status=403)

            # Aggiorna i campi solo se sono presenti nella richiesta
            if title:
                conference.title = title
            if deadline:
                conference.deadline = deadline
            if description:
                conference.description = description

            conference.save()
            return JsonResponse({'message': 'Conference updated successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    else:
        return JsonResponse({'error': 'Only PATCH requests are allowed'}, status=405)



@csrf_exempt
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a conference by providing its ID and the user ID of the admin.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference to delete'),
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user requesting deletion'),
        },
        required=['conference_id', 'user_id']
    ),
    responses={
        200: openapi.Response(description="Conference deleted successfully"),
        400: openapi.Response(description="Missing required fields or invalid JSON"),
        404: openapi.Response(description="Conference not found"),
        403: openapi.Response(description="Permission denied"),
    }
)
@api_view(['DELETE'])
def delete_conference(request):
    try:
        data = json.loads(request.body)
        conference_id = data.get('conference_id')
        user_id = data.get('user_id')

        # Verifica che i campi richiesti siano presenti
        if not conference_id or not user_id:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Verifica che la conferenza esista
        try:
            conference = Conference.objects.get(id=conference_id)
        except Conference.DoesNotExist:
            return JsonResponse({'error': 'Conference not found'}, status=404)

        # Verifica che l'utente sia un admin della conferenza
        is_admin = ConferenceRole.objects.filter(
            conference=conference,
            user_id=user_id,
            role='admin'
        ).exists()

        if not is_admin:
            return JsonResponse(
                {'error': 'Permission denied. User is not an admin of this conference.'},
                status=403
            )

        # Elimina la conferenza
        conference.delete()
        return JsonResponse({'message': 'Conference deleted successfully'}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




