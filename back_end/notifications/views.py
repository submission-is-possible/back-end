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

'''esempio richiesta post per creare una notifica
{
    "id_user1": 1,           # utente che invia la notifica
    "id_user2": 2,           # utente che riceve la notifica
    "type": "invited_as_reviewer",
    "title": "Richiesta di revisione",
    "description": "Hai ricevuto una richiesta di revisione per la conferenza X"
}
'''
@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Create a new notification.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id_user1': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user sending the notification'),
            'id_user2': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user receiving the notification'),
            'type': openapi.Schema(type=openapi.TYPE_STRING, description='Type of the notification'),
            'title': openapi.Schema(type=openapi.TYPE_STRING, description='Title of the notification'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description of the notification')
        },
        required=['id_user1', 'id_user2', 'type', 'title', 'description']
    ),
    responses={
        201: openapi.Response(description="Notification created successfully"),
        400: openapi.Response(description="Missing required fields or invalid JSON"),
        404: openapi.Response(description="One or both users not found"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['POST'])
def create_notification(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Verifica presenza campi obbligatori
            required_fields = ['id_user1', 'id_user2', 'type', 'title', 'description']
            if not all(field in data for field in required_fields):
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Verifica esistenza utenti
            try:
                user1 = User.objects.get(id=data['id_user1'])
                user2 = User.objects.get(id=data['id_user2'])
            except User.DoesNotExist:
                return JsonResponse({'error': 'One or both users not found'}, status=404)

            # Crea la notifica
            notification = Notification.objects.create(
                id_user1=user1,
                id_user2=user2,
                type=data['type'],
                title=data['title'],
                description=data['description']
            )

            return JsonResponse({
                'message': 'Notification created successfully',
                'notification_id': notification.id
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Get notifications for a specific user.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user'),
            'page': openapi.Schema(type=openapi.TYPE_INTEGER, description='Page number (optional, default 1)'),
            'page_size': openapi.Schema(type=openapi.TYPE_INTEGER, description='Page size (optional, default 10)')
        },
        required=['user_id']
    ),
    responses={
        200: openapi.Response(description="List of notifications for the user"),
        400: openapi.Response(description="Missing user_id parameter or invalid JSON"),
        404: openapi.Response(description="User not found"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['POST'])
def get_notifications(request):
    """
    Recupera le notifiche per un utente specifico.
    Struttura JSON richiesta:
    {
        "user_id": 1,
        "page": 1,        # opzionale, default 1
        "page_size": 10   # opzionale, default 10
    }
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')

            if not user_id:
                return JsonResponse({'error': 'Missing user_id parameter'}, status=400)

            # Verifica esistenza utente
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

            page_number = data.get('page', 1)
            page_size = data.get('page_size', 10)

            # Ottiene le notifiche dell'utente
            notifications = Notification.objects.filter(id_user2=user_id).order_by('-creation_date')

            # Applica paginazione
            paginator = Paginator(notifications, page_size)
            page_obj = paginator.get_page(page_number)

            response_data = {
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "total_notifications": paginator.count,
                "notifications": [
                    {
                        "id": notif.id,
                        "sender": notif.id_user1.id,
                        "type": notif.type,
                        "title": notif.title,
                        "description": notif.description,
                        "creation_date": notif.creation_date.isoformat(),
                        "read": notif.read
                    }
                    for notif in page_obj
                ]
            }
            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Mark a notification as read.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'notification_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the notification to mark as read')
        },
        required=['notification_id']
    ),
    responses={
        200: openapi.Response(description="Notification marked as read"),
        400: openapi.Response(description="Missing notification_id or invalid JSON"),
        404: openapi.Response(description="Notification not found"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['POST'])
def mark_as_read(request):
    """
    Marca una notifica come letta.
    Struttura JSON richiesta:
    {
        "notification_id": 1
    }
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            notification_id = data.get('notification_id')

            if not notification_id:
                return JsonResponse({'error': 'Missing notification_id'}, status=400)

            try:
                notification = Notification.objects.get(id=notification_id)
                notification.read = True
                notification.save()

                return JsonResponse({'message': 'Notification marked as read'})

            except Notification.DoesNotExist:
                return JsonResponse({'error': 'Notification not found'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Delete a notification.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'notification_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the notification to delete')
        },
        required=['notification_id']
    ),
    responses={
        200: openapi.Response(description="Notification deleted successfully"),
        400: openapi.Response(description="Missing notification_id or invalid JSON"),
        404: openapi.Response(description="Notification not found"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['POST'])
def delete_notification(request):
    """
    Elimina una notifica.
    Struttura JSON richiesta:
    {
        "notification_id": 1
    }
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            notification_id = data.get('notification_id')

            if not notification_id:
                return JsonResponse({'error': 'Missing notification_id'}, status=400)

            try:
                notification = Notification.objects.get(id=notification_id)
                notification.delete()

                return JsonResponse({'message': 'Notification deleted successfully'})

            except Notification.DoesNotExist:
                return JsonResponse({'error': 'Notification not found'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)