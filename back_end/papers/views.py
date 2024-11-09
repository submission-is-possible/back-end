from .models import Paper
from users.models import User
from conference.models import Conference
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
import json

@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Create a new paper.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING, description='Title of the paper'),
            'paper_file': openapi.Schema(type=openapi.TYPE_FILE, description='File of the paper'),
            'author_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the author'),
            'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference')
        },
        required=['title', 'paper_file', 'author_id', 'conference_id', 'status']
    ),
    responses={
        201: openapi.Response(description="Paper added successfully"),
        400: openapi.Response(description="Missing fields or request body is not valid JSON"),
        404: openapi.Response(description="Author or conference not found")
    }
)
@api_view(['POST'])

@csrf_exempt
def create_paper(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            paper_file = data.get('paper_file')
            author_id = data.get('author_id')
            conference_id = data.get('conference_id')

            if not (title and author_id and conference_id):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            try:
                author = User.objects.get(id=author_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'Author not found'}, status=404)

            try:
                conference = Conference.objects.get(id=conference_id)
            except Conference.DoesNotExist:
                return JsonResponse({'error': 'Conference not found'}, status=404)

            paper = Paper.objects.create(
                title=title,
                paper_file=paper_file,
                author=author,
                conference=conference,
                status='submitted'
            )
            return JsonResponse({
                'message': 'Paper added successfully',
                'paper_id': paper.id
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSONMissing fields or request body is not valid JSON'}, status=400)