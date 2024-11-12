import json
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from users.models import User
from .models import Notification
from rest_framework.decorators import api_view
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from conference.models import Conference


@api_view(['POST'])
@swagger_auto_schema(
    method='post',
    operation_description="Create a new notification.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_sender': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user sending the notification'),
            'user_receiver': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user receiving the notification'),
            'conference': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference'),
            'type': openapi.Schema(type=openapi.TYPE_INTEGER, description='Type of the notification')
        },
        required=['user_sender', 'user_receiver', 'conference', 'type']
    ),
    responses={
        201: openapi.Response(description="Notification created successfully"),
        400: openapi.Response(description="Missing fields or invalid JSON"),
        404: openapi.Response(description="User or conference not found"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@csrf_exempt
def create_notification(request):
    if request.method == 'POST':
        try:
            # Estrai i dati dal body della richiesta
            data = json.loads(request.body)
            user_sender_id = data.get('user_sender')
            user_receiver_id = data.get('user_receiver')
            conference_id = data.get('conference')
            notification_type = data.get('type')

            # Verifica che i campi richiesti siano presenti
            if not (user_sender_id and user_receiver_id and conference_id and notification_type is not None):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            # Verifica se gli utenti esistono
            try:
                user_sender = User.objects.get(id=user_sender_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User sender not found'}, status=404)

            try:
                user_receiver = User.objects.get(id=user_receiver_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User receiver not found'}, status=404)

            # Verifica se la conferenza esiste
            try:
                conference = Conference.objects.get(id=conference_id)
            except Conference.DoesNotExist:
                return JsonResponse({'error': 'Conference not found'}, status=404)

            # Crea la nuova notifica
            notification = Notification.objects.create(
                user_sender=user_sender,
                user_receiver=user_receiver,
                conference=conference,
                status=0,  # Setta lo stato a 'pending' di default
                type=notification_type,
                created_at=timezone.now()
            )

            return JsonResponse({
                'message': 'Notification created successfully',
                'notification_id': notification.id
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@api_view(['POST'])
@swagger_auto_schema(
    method='post',
    operation_description="Get a list of notifications received by the user with pagination.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user receiving the notifications')
        },
        required=['user_id']
    ),
    responses={
        200: openapi.Response(description="Notifications found"),
        400: openapi.Response(description="Missing fields or invalid JSON"),
        404: openapi.Response(description="User not found"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@csrf_exempt
def get_notifications_received(request):
    """Restituisce una lista di notifiche ricevute dall'utente con paginazione."""

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

    # Filtra le notifiche ricevute per l'utente specificato e ordinale per data di creazione
    notifications = Notification.objects.filter(user_receiver_id=user_id).select_related('user_sender','conference').order_by('-created_at')

    # Applica la paginazione
    paginator = Paginator(notifications, page_size)
    page_obj = paginator.get_page(page_number)

    # Crea la risposta con le notifiche per la pagina corrente
    response_data = {
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
        "total_notifications": paginator.count,
        "notifications": [
            {
                "id": notification.id,
                "user_sender": {
                    "id": notification.user_sender.id,
                    "username": notification.user_sender.username,
                    "email": notification.user_sender.email
                },
                "user_receiver": {
                    "id": notification.user_receiver.id,
                    "username": notification.user_receiver.username,
                    "email": notification.user_receiver.email
                },
                "conference": {
                    "id": notification.conference.id,
                    "title": notification.conference.title,
                    "description": notification.conference.description,
                    "created_at": notification.conference.created_at.isoformat(),
                    "deadline": notification.conference.deadline.isoformat()
                },
                "status": notification.get_status_display(),
                "type": notification.get_type_display(),
                "created_at": notification.created_at.isoformat()
            }
            for notification in page_obj
        ]
    }
    return JsonResponse(response_data, status=200)


@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Delete a notification.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user'),
            'id_notification': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the notification')
        },
        required=['user_id', 'id_notification']
    ),
    responses={
        200: openapi.Response(description="Notification deleted successfully"),
        400: openapi.Response(description="Missing fields or invalid JSON"),
        404: openapi.Response(description="User or notification not found"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['POST'])
def delete_notification(request):
    if request.method == 'POST':
        try:
            # Estrai i dati dal body della richiesta
            data = json.loads(request.body)
            user_id = data.get('user_id')
            notification_id = data.get('id_notification')

            # Verifica che i campi richiesti siano presenti
            if not (user_id and notification_id):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            # Verifica se l'utente esiste
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

            # Verifica se la notifica esiste e appartiene all'utente
            try:
                notification = Notification.objects.get(id=notification_id, user_receiver=user)
            except Notification.DoesNotExist:
                return JsonResponse({'error': 'Notification not found or does not belong to the user'}, status=404)

            # Elimina la notifica
            notification.delete()

            return JsonResponse({'message': 'Notification deleted successfully'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)



@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Update the status of a notification.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id_notification': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the notification'),
            'status': openapi.Schema(type=openapi.TYPE_STRING, description='New status of the notification')
        },
        required=['id_notification', 'status']
    ),
    responses={
        200: openapi.Response(description="Notification updated successfully"),
        400: openapi.Response(description="Missing fields, invalid JSON, or invalid status value"),
        404: openapi.Response(description="Notification not found"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['POST'])
def update_notification(request):
    if request.method == 'POST':
        try:
            # Estrai i dati dal body della richiesta
            data = json.loads(request.body)
            notification_id = data.get('id_notification')
            status = data.get('status')

            # Verifica che i campi richiesti siano presenti
            if not (notification_id and status):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            # Mappa dei valori di status dalle stringhe ai valori numerici
            status_mapping = {
                'accept': 1,
                'reject': -1
            }

            # Verifica se il valore dello status è valido
            if status not in status_mapping:
                return JsonResponse({'error': 'Invalid status value'}, status=400)

            # Verifica se la notifica esiste
            try:
                notification = Notification.objects.get(id=notification_id)
            except Notification.DoesNotExist:
                return JsonResponse({'error': 'Notification not found'}, status=404)

            # Inverti mittente e destinatario
            user_sender = notification.user_sender
            user_receiver = notification.user_receiver
            notification.user_sender = user_receiver
            notification.user_receiver = user_sender

            # Aggiorna lo status
            notification.status = status_mapping[status]

            # Salva le modifiche
            notification.save()

            return JsonResponse({'message': 'Notification updated successfully'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
