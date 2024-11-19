import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from notifications.models import Notification
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
    operation_description="Create a new conference with title, admin_id, deadline, description, authors, and reviewers.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING, description='Title of the conference'),
            'admin_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference admin'),
            'deadline': openapi.Schema(type=openapi.TYPE_STRING, description='Deadline for the conference'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description of the conference'),
            'authors': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description='List of author emails'),
            'reviewers': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description='List of reviewer emails'),
        },
        required=['title', 'admin_id', 'deadline', 'description', 'authors', 'reviewers']
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

            authors = data.get('authors') #lista di email di autori da invitare
            reviewers = data.get('reviewers') #lista di email di revisori da invitare

            # Verifica che i campi richiesti siano presenti
            if not (title and deadline and description):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            # Verifica se l'utente (admin) esiste
            try:
                admin_user = User.objects.get(id=admin_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'Admin user not found'}, status=404)

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

            # Invita gli autori
            for author_email in authors:
                try:
                    author = User.objects.get(email=author_email) #cerca l'utente con l'email fornita
                except User.DoesNotExist:
                    return JsonResponse({'error': 'Author user not found'}, status=404)
                ConferenceRole.objects.create(
                    user=author,
                    conference=conference,
                    role='author'
                )
                Notification.objects.create(
                    user_sender=admin_user, # L'utente admin invia la notifica
                    user_receiver=author, # L'utente autore riceve la notifica
                    conference=conference,
                    status=0,  # status=0 significa che la notifica è in attesa di risposta (pending)
                    type=0  # author type
                )

            # Invita i revisori
            for reviewer_email in reviewers:
                try:
                    reviewer = User.objects.get(email=reviewer_email)
                except User.DoesNotExist:
                    return JsonResponse({'error': 'Reviewer user not found'}, status=404)
                ConferenceRole.objects.create(
                    user=reviewer,
                    conference=conference,
                    role='reviewer'
                )
                Notification.objects.create(
                    user_sender=admin_user,
                    user_receiver=reviewer,
                    conference=conference,
                    status=0,
                    type=1  # reviewer type
                )
            print("sono qui")
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
                conference = Conference.objects.get(id=conference_id)
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
@get_user
def edit_conference(request):
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            print (data)
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
            user = request.user
            is_admin = ConferenceRole.objects.filter(
                conference=conference,
                user=user,
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


