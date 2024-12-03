import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import csv
import io
from django.core.paginator import Paginator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view
from users.decorators import get_user

from conference_roles.models import ConferenceRole
from users.models import User
from .models import Preference

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Conference id'),
            'preferences': openapi.Schema(type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                                                            'paper': openapi.Schema(type=openapi.TYPE_INTEGER, description='paper to review'),
                                                            'preference': openapi.Schema(type=openapi.TYPE_INTEGER, description='preference to paper')
                                        }))
        }
    ),
    responses={
        201: openapi.Response('preferences saved successfully'),
        400: 'Bad request',
        405: 'Only POST requests are allowed',
        403: 'User is not a reviewer in this conference'
    }
)
@api_view(['POST'])
@csrf_exempt
#@get_user
def save_preferences(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
    
    data = json.loads(request.body)
    preferences = data.get('preferences')
    conference_id = data.get('conference_id')
    try:
        user = request.user
        user = User.objects.get(id = 2)
        print(user)
        print(request)
        if not conference_id:
            return JsonResponse({'error': 'Missing conference_id'}, status=400)

        is_reviewer = ConferenceRole.objects.filter(
            user=user,
            conference_id=conference_id,
            role='reviewer'
        ).exists()

        if not is_reviewer:
            return JsonResponse({
                "error": "User is not a reviewer in this conference"
            }, status=403)
        


        for preference in preferences or []:
            paper_id = preference.get('paper')
            preference = preference.get('preference')
            if not paper_id or not preference:
                continue

            Preference.objects.create(   
                paper_id = paper_id,
                reviewer = user,
                preference = preference
            )
        return JsonResponse({
            'message': 'Preferences saved'
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

"""
@swagger_auto_schema(
    method='get',
    manual_parameters=[
            openapi.Parameter(
                'conference_id',
                openapi.IN_PATH,
                description="id of the conference",
                type=openapi.TYPE_INTEGER, 
                required=True 
            ),
        ],
    responses={
        201: openapi.Response(description="Preferences found"),
        400: 'Bad request',
        405: 'Only GET requests are allowed',
        403: 'User is not a reviewer in this conference',
    }
)
@api_view(['GET'])
@csrf_exempt
@get_user
def get_preferences(request):
    if request.method != 'GET':
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)
    
    conference_id = request.GET.get('conference_id')

    try:
        user = request.user
        
        if not conference_id:
            return JsonResponse({'error': 'Missing conference_id'}, status=400)
        
        is_reviewer = ConferenceRole.objects.filter(
            user=user,
            conference_id=conference_id,
            role='reviewer'
        ).exists()

        if not is_reviewer:
            return JsonResponse({
                "error": "User is not a reviewer in this conference"
            }, status=403)

"""