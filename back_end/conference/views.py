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
import csv
import io

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING, description='Title of the conference'),
            'deadline': openapi.Schema(type=openapi.TYPE_STRING, description='Deadline for submissions'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description of the conference'),
            'reviewers': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of reviewer')
            }))
        }
    ),
    responses={
        201: openapi.Response('Conference created successfully', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the created conference')
            }
        )),
        400: 'Bad request',
        405: 'Method not allowed'
    }
)
@api_view(['POST'])
@csrf_exempt
@get_user
def create_conference(request):
    if request.method == 'POST':
        try:
            # Estrai i dati dal body della richiesta
            data = json.loads(request.body)
            title = data.get('title')
            deadline = data.get('deadline')
            description = data.get('description')

            reviewers = data.get('reviewers') #lista di email di revisori da invitare

            # Verifica che i campi richiesti siano presenti
            if not (title and deadline and description):
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            if reviewers is None:
                return JsonResponse({'error': 'Authors and reviewers must be provided, even if empty'}, status=400)

            admin_user = request.user

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

            # Invita i revisori (se ci sono)
            for reviewer in reviewers or []:
                reviewer_email = reviewer.get('email')  # Ottieni l'email dal dizionario
                if not reviewer_email:
                    continue  # Salta se manca l'email
                try:
                    reviewer_user = User.objects.get(email=reviewer_email)
                except User.DoesNotExist:
                    return JsonResponse({'error': f'Reviewer user not found: {reviewer_email}'}, status=404)
                
                #devo assicurarmi che non invito me stesso come revisore, non avrebbe senso
                if reviewer_user == admin_user:
                    return JsonResponse({'error': 'Cannot invite yourself as a reviewer'}, status=400)
                
                # se sto invitando un revisore, devo assegnarli il ruolo di revisore
                ConferenceRole.objects.create(
                    user=reviewer_user,
                    conference=conference,
                    role='reviewer'
                )
                # inoltre devo creare una notifica per il revisore, in modo che possa accettare o rifiutare l'invito
                Notification.objects.create(
                    user_sender=admin_user,  # L'utente admin invia la notifica
                    user_receiver=reviewer_user,  # Il revisore riceve la notifica
                    conference=conference,
                    status=0,  # status=0 significa che la notifica è in attesa di risposta (pending)
                    type=1  # reviewer type
                )

            return JsonResponse({
                'message': 'Conference created successfully',
                'conference_id': conference.id
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


@swagger_auto_schema(
    method='delete',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference to delete')
        }
    ),
    responses={
        200: 'Conference deleted successfully',
        400: 'Bad request',
        403: 'Permission denied',
        404: 'Conference not found',
        405: 'Method not allowed'
    }
)
@api_view(['DELETE'])
@csrf_exempt
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

@swagger_auto_schema(
    method='patch',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference to edit'),
            'title': openapi.Schema(type=openapi.TYPE_STRING, description='New title of the conference'),
            'deadline': openapi.Schema(type=openapi.TYPE_STRING, description='New deadline for submissions'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='New description of the conference')
        }
    ),
    responses={
        200: 'Conference updated successfully',
        400: 'Bad request',
        403: 'Permission denied',
        404: 'Conference not found',
        405: 'Method not allowed'
    }
)
@api_view(['PATCH'])
@csrf_exempt
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

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'csv_file': openapi.Schema(type=openapi.TYPE_FILE, description='CSV file containing reviewer emails')
        }
    ),
    responses={
        200: openapi.Response('Email addresses extracted successfully', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'emails': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING, description='Email address'))
            }
        )),
        400: 'Bad request',
        405: 'Method not allowed'
    }
)
@api_view(['POST'])
@csrf_exempt
def upload_reviewers_csv(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    if 'csv_file' not in request.FILES:
        return JsonResponse({'error': 'No CSV file provided'}, status=400)
    
    csv_file = request.FILES['csv_file']

    # Check if file is CSV
    if not csv_file.name.endswith('.csv'):
        return JsonResponse({'error': 'File must be a CSV'}, status=400)
    
    try:
        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'iso-8859-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                # Reset file pointer
                csv_file.seek(0)
                content = csv_file.read().decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            return JsonResponse({'error': 'Unable to decode CSV file'}, status=400)
        
        # Try different dialect detection
        sample = content[:1024]
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        
        csv_reader = csv.reader(io.StringIO(content), dialect)
        
        # Extract emails from CSV
        emails = []
        for row in csv_reader:
            if row:  # Check if row is not empty
                email = row[0].strip()  # Assuming email is in the first column
                if '@' in email:  # Basic email validation
                    emails.append(email)
        
        if not emails:
            return JsonResponse({'error': 'No valid email addresses found in CSV'}, status=400)
            
        return JsonResponse({'emails': emails})
    
    except Exception as e:
        return JsonResponse({'error': f'Error processing CSV: {str(e)}'}, status=400)



