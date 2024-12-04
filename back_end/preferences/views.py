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
from .models import Preference, Paper
from conference.models import Conference

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
    
'''
esempio di richiesta post:
{
    "id_reviewer": 1,
    "id_paper": 101,
    "type_preference": "interested"
}
'''
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id_reviewer': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the reviewer'),
            'id_paper': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the paper'),
            'type_preference': openapi.Schema(type=openapi.TYPE_STRING, description='Type of preference (interested, not_interested, neutral)')
        }
    ),
    responses={
        201: openapi.Response('Preference added successfully'),
        400: 'Bad request',
        403: 'User is not a reviewer for this conference',
        404: 'Reviewer or Paper not found',
        409: 'Preference already exists'
    }
)
@api_view(['POST'])
@csrf_exempt
def add_preference(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        data = json.loads(request.body)
        id_reviewer = data.get('id_reviewer')
        id_paper = data.get('id_paper')
        type_preference = data.get('type_preference')

        if not all([id_reviewer, id_paper, type_preference]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        try:
            reviewer = User.objects.get(id=id_reviewer)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Reviewer not found'}, status=404)

        try:
            paper = Paper.objects.get(id=id_paper)
        except Paper.DoesNotExist:
            return JsonResponse({'error': 'Paper not found'}, status=404)

        # Verifica se l'utente è un reviewer per la conferenza del paper
        is_reviewer = ConferenceRole.objects.filter(
            user=reviewer,
            conference=paper.conference,
            role='reviewer'
        ).exists()

        if not is_reviewer:
            return JsonResponse({'error': 'User is not a reviewer for this conference'}, status=403)

        # Verifica se esiste già una preferenza uguale
        if Preference.objects.filter(reviewer=reviewer, paper=paper, preference=type_preference).exists():
            return JsonResponse({'error': 'Preference already exists'}, status=409)
        
        # Elimina la preferenza opposta se esiste
        opposite_preferences = {
            'interested': ['not_interested'],
            'not_interested': ['interested']
        }
        Preference.objects.filter(
            reviewer=reviewer,
            paper=paper,
            preference__in=opposite_preferences.get(type_preference, [])
        ).delete()

        # Aggiungi la preferenza
        Preference.objects.create(
            paper=paper,
            reviewer=reviewer,
            preference=type_preference
        )

        return JsonResponse({'message': 'Preference added successfully'}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
'''
esempio di richiesta post:
{
    "id_reviewer": 1,
    "id_conference": 42,
    "type_preference": "interested"
}
'''
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id_reviewer': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the reviewer'),
            'id_conference': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference'),
            'type_preference': openapi.Schema(type=openapi.TYPE_STRING, description='Type of preference (interested, not_interested, neutral)')
        }
    ),
    responses={
        200: openapi.Response('Papers retrieved successfully'),
        400: 'Bad request',
        403: 'User is not a reviewer for this conference',
        404: 'Reviewer or Conference not found'
    }
)
@api_view(['POST'])
@csrf_exempt
def get_preference_papers_in_conference_by_reviewer(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        data = json.loads(request.body)
        id_reviewer = data.get('id_reviewer')
        id_conference = data.get('id_conference')
        type_preference = data.get('type_preference')

        if not all([id_reviewer, id_conference, type_preference]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        try:
            reviewer = User.objects.get(id=id_reviewer)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Reviewer not found'}, status=404)

        try:
            conference = Conference.objects.get(id=id_conference)
        except Conference.DoesNotExist:
            return JsonResponse({'error': 'Conference not found'}, status=404)

        # Verifica se l'utente è un reviewer per la conferenza
        is_reviewer = ConferenceRole.objects.filter(
            user=reviewer,
            conference=conference,
            role='reviewer'
        ).exists()

        if not is_reviewer:
            return JsonResponse({'error': 'User is not a reviewer for this conference'}, status=403)

        
        # Prendi tutti i paper della conferenza
        papers = Paper.objects.filter(conference=conference)

        # Filtra i paper in base alle preferenze del reviewer
        paper_ids = Preference.objects.filter(
            reviewer=reviewer,
            paper__in=papers,
            preference=type_preference
        ).values_list('paper_id', flat=True)

        return JsonResponse({'paper_ids': list(paper_ids)}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id_reviewer': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the reviewer'),
            'id_paper': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the paper'),
            'type_preference': openapi.Schema(type=openapi.TYPE_STRING, description='Type of preference (interested, not_interested, neutral)')
        }
    ),
    responses={
        200: openapi.Response('Preference deleted successfully'),
        400: 'Bad request',
        403: 'User is not a reviewer for this conference',
        404: 'Reviewer, Paper, or Preference not found'
    }
)
@api_view(['POST'])
@csrf_exempt
def delete_preference(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        data = json.loads(request.body)
        id_reviewer = data.get('id_reviewer')
        id_paper = data.get('id_paper')
        type_preference = data.get('type_preference')

        if not all([id_reviewer, id_paper, type_preference]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        try:
            reviewer = User.objects.get(id=id_reviewer)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Reviewer not found'}, status=404)

        try:
            paper = Paper.objects.get(id=id_paper)
        except Paper.DoesNotExist:
            return JsonResponse({'error': 'Paper not found'}, status=404)

        # Verifica se l'utente è un reviewer per la conferenza del paper
        is_reviewer = ConferenceRole.objects.filter(
            user=reviewer,
            conference=paper.conference,
            role='reviewer'
        ).exists()

        if not is_reviewer:
            return JsonResponse({'error': 'User is not a reviewer for this conference'}, status=403)

        # Verifica se esiste la preferenza
        try:
            preference = Preference.objects.get(reviewer=reviewer, paper=paper, preference=type_preference)
        except Preference.DoesNotExist:
            return JsonResponse({'error': 'Preference not found'}, status=404)

        # Elimina la preferenza
        preference.delete()

        return JsonResponse({'message': 'Preference deleted successfully'}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)