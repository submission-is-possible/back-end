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


@csrf_exempt
@swagger_auto_schema(
    methods=['POST'],
    operation_description="Create a new notification.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_sender': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user sending the notification'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING)
            }),
            'user_receiver': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user receiving the notification'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING)
            }),
            'conference': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference'),
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'admin_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'created_at': openapi.Schema(type=openapi.TYPE_STRING),
                'deadline': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING)
            }),
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
@api_view(['POST'])
def create_notification(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_sender_data = data.get('user_sender')
            user_receiver_data = data.get('user_receiver')
            conference_data = data.get('conference')
            notification_type = data.get('type')

            if not (user_sender_data and user_receiver_data and conference_data and notification_type is not None):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            try:
                user_sender = User.objects.get(id=user_sender_data['id'])
            except User.DoesNotExist:
                return JsonResponse({'error': 'User sender not found'}, status=404)

            try:
                user_receiver = User.objects.get(id=user_receiver_data['id'])
            except User.DoesNotExist:
                return JsonResponse({'error': 'User receiver not found'}, status=404)

            try:
                conference = Conference.objects.get(id=conference_data['id'])
            except Conference.DoesNotExist:
                return JsonResponse({'error': 'Conference not found'}, status=404)

            notification = Notification.objects.create(
                user_sender=user_sender,
                user_receiver=user_receiver,
                conference=conference,
                status=0,
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



@csrf_exempt
@swagger_auto_schema(
    methods=['POST'],
    operation_description="Retrieve a paginated list of notifications received by a user.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user receiving the notifications')
        },
        required=['user_id']
    ),
    responses={
        200: openapi.Response(description="A paginated list of received notifications", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "current_page": openapi.Schema(type=openapi.TYPE_INTEGER),
                "total_pages": openapi.Schema(type=openapi.TYPE_INTEGER),
                "total_notifications": openapi.Schema(type=openapi.TYPE_INTEGER),
                "notifications": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "user_sender": openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "email": openapi.Schema(type=openapi.TYPE_STRING)
                        }),
                        "user_receiver": openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "email": openapi.Schema(type=openapi.TYPE_STRING)
                        }),
                        "conference": openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "title": openapi.Schema(type=openapi.TYPE_STRING),
                            "description": openapi.Schema(type=openapi.TYPE_STRING),
                            "created_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                            "deadline": openapi.Schema(type=openapi.TYPE_STRING, format="date-time")
                        }),
                        "status": openapi.Schema(type=openapi.TYPE_STRING),
                        "type": openapi.Schema(type=openapi.TYPE_STRING),
                        "created_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time")
                    }
                ))
            }
        )),
        400: openapi.Response(description="Invalid JSON or missing user_id"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['POST'])
def get_notifications_received(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not user_id:
        return JsonResponse({"error": "Missing user_id"}, status=400)

    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)

    notifications = Notification.objects.filter(user_receiver_id=user_id).select_related('user_sender','conference').order_by('-created_at')

    paginator = Paginator(notifications, page_size)
    page_obj = paginator.get_page(page_number)

    response_data = {
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
        "total_notifications": paginator.count,
        "notifications": [
            {
                "id": notification.id,
                "user_sender": {
                    "id": notification.user_sender.id,
                    "email": notification.user_sender.email
                },
                "user_receiver": {
                    "id": notification.user_receiver.id,
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
    print(response_data)
    return JsonResponse(response_data, status=200)


@csrf_exempt
@swagger_auto_schema(
    methods=['POST'],
    operation_description="Delete a notification by ID and user ID.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user attempting to delete the notification'),
            'id_notification': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the notification to be deleted')
        },
        required=['user_id', 'id_notification']
    ),
    responses={
        200: openapi.Response(description="Notification deleted successfully"),
        400: openapi.Response(description="Invalid JSON or missing fields"),
        404: openapi.Response(description="User or notification not found"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['POST'])
def delete_notification(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            notification_id = data.get('id_notification')
            # Check if the user_id and notification_id are present
            if not (user_id and notification_id):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

            try:
                notification = Notification.objects.get(id=notification_id, user_receiver=user)
            except Notification.DoesNotExist:
                return JsonResponse({'error': 'Notification not found or does not belong to the user'}, status=404)

            notification.delete()

            return JsonResponse({'message': 'Notification deleted successfully'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
@swagger_auto_schema(
    methods=['PATCH'],
    operation_description="Update a notification status and swap sender and receiver.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id_notification': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the notification to update'),
            'status': openapi.Schema(type=openapi.TYPE_STRING, description='New status of the notification (accept/reject)')
        },
        required=['id_notification', 'status']
    ),
    responses={
        200: openapi.Response(description="Notification updated successfully"),
        400: openapi.Response(description="Invalid data or status"),
        404: openapi.Response(description="Notification not found"),
        405: openapi.Response(description="Only PATCH requests are allowed")
    }
)
@api_view(['PATCH'])
def update_notification(request):
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            notification_id = data.get('id_notification')
            status = data.get('status')

            if not (notification_id and status):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            status_mapping = {
                'accept': 1,
                'reject': -1
            }

            if status not in status_mapping:
                return JsonResponse({'error': 'Invalid status value'}, status=400)

            try:
                notification = Notification.objects.get(id=notification_id)
            except Notification.DoesNotExist:
                return JsonResponse({'error': 'Notification not found'}, status=404)

            user_sender = notification.user_sender
            user_receiver = notification.user_receiver
            notification.user_sender = user_receiver
            notification.user_receiver = user_sender

            notification.status = status_mapping[status]
            notification.save()

            return JsonResponse({'message': 'Notification updated successfully'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only PATCH requests are allowed'}, status=405)
