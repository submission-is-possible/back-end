import base64
import json
from .models import Paper
from users.models import User
from conference.models import Conference
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from datetime import datetime
import os
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger

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
        required=['title', 'paper_file', 'author_id', 'conference_id']
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
        data = json.loads(request.body)
        title = data.get('title')
        paper_file = data.get('paper_file')
        author_id = data.get('author_id')
        conference_id = data.get('conference_id')

        if title is None or author_id is None or conference_id is None:
            return JsonResponse({'error': 'Missing fields'}, status=400)

        paper_file = base64.b64decode(paper_file)
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        paper_file = ContentFile(paper_file, name=f'paper_file_{current_time}.pdf')

        fs = FileSystemStorage(location='papers_pdf')
        filename = fs.save(paper_file.name, paper_file)
        paper_file = fs.url(filename)

        print(paper_file)

        try:
            author = User.objects.get(id=author_id)
            conference = Conference.objects.get(id=conference_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Author not found'}, status=404)
        except Conference.DoesNotExist:
            return JsonResponse({'error': 'Conference not found'}, status=404)

        paper = Paper(title=title, paper_file=paper_file, author_id=author, conference=conference, status_id='submitted')
        paper.save()

        return JsonResponse({'message': 'Paper added successfully',
                             'paper_id': paper.id}, status=201)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Get a all papers from user",
    responses={
        200: openapi.Response(description="Papers found"),
        404: openapi.Response(description="Paper not found")
    }
)
@api_view(['POST'])

@csrf_exempt
def list_papers(request):
    """
    Get paginated list of papers for a specific user.
    
    Example request:
    POST /papers/list/?page=2&page_size=10
    {
        "user_id": 1
    }
    """
    # Verify request method is POST
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
    
    # Parse request body to get user_id
    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    # Verify user_id is provided
    if not user_id:
        return JsonResponse({"error": "Missing user_id"}, status=400)
    
    # Get pagination parameters from request
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)
    
    try:
        # Verify user exists
        user = User.objects.get(id=user_id)
        
        # Get papers for the user
        papers = Paper.objects.filter(author_id=user_id).select_related('conference')
        
        # Create list of papers with their details
        papers_list = []
        for paper in papers:
            papers_list.append({
                "id": paper.id,
                "title": paper.title,
                "paper_file": paper.paper_file.url if paper.paper_file else None,
                "conference_id": paper.conference.id,
                "conference_title": paper.conference.title,
                "status_id": paper.status_id,
                "created_at": paper.conference.created_at.isoformat(),
            })
        
        # Apply pagination
        paginator = Paginator(papers_list, page_size)
        page_obj = paginator.get_page(page_number)
        
        # Create response with papers for current page
        response_data = {
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "total_papers": paginator.count,
            "papers": list(page_obj)
        }
        
        return JsonResponse(response_data, status=200)
        
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
