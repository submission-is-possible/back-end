import base64
import json
from .models import Paper
from users.models import User
from conference.models import Conference
from conference_roles.models import ConferenceRole
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from datetime import datetime
import os
from django.conf import settings
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.http import FileResponse
from users.decorators import get_user


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
        required=['title', 'paper_file', 'author', 'conference']
    ),
    responses={
        201: openapi.Response(description="Paper added successfully"),
        400: openapi.Response(description="Missing fields or request body is not valid JSON"),
        404: openapi.Response(description="Author or conference not found")
    }
)
@api_view(['POST'])
@csrf_exempt
@get_user
def create_paper(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        title = data.get('title')
        paper_file = data.get('paper_file')
        conference_id = data.get('conference_id')

        if title is None or conference_id is None:
            return JsonResponse({'error': 'Missing fields'}, status=400)

        paper_file = base64.b64decode(paper_file)
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        paper_file = ContentFile(paper_file, name=f'paper_file_{current_time}.pdf')

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'papers', 'paper'))
        filename = fs.save(paper_file.name, paper_file)
        paper_file = fs.url(filename)

        try:
            author = request.user
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
                "conference": paper.conference.id,
                "conference_title": paper.conference.title,
                "status": paper.status_id,
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


@csrf_exempt
@swagger_auto_schema(
    method='get',
    operation_description="Get papers of conference visible to user",
    responses={
        200: openapi.Response(description="Papers found"),
        404: openapi.Response(description="Papers not found")
    }
)
@api_view(['GET'])
@get_user
def list_conf_papers(request):
    if request.method != 'GET':
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)
    
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)
    conference_id = request.GET.get('conf')
    
    try:

        user = request.user
        conferenceRole = ConferenceRole.objects.get(user = user, conference_id = conference_id)
        # Get papers for the user
        if conferenceRole.role == 'admin': # se user è admin estrai tutti i paper 
            papers = Paper.objects.filter(conference_id=conference_id).select_related('conference')         
        if conferenceRole.role == 'author': # se user è autore estrai solo i paper che ha scritto
            papers = Paper.objects.filter(conference_id=conference_id, author_id=request.user)
        # se user è reviwer estrarre solo i paper che può revisionare
        
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


@csrf_exempt
@swagger_auto_schema(
    method='get',
    operation_description="View PDF paper file in browser",
    responses={
        200: openapi.Response(description="PDF file served successfully"),
        404: openapi.Response(description="Paper file not found"),
        400: openapi.Response(description="Invalid filename")
    }
)
@api_view(['GET'])
def view_paper_pdf(request, filename):
    """
    Serve a PDF file from the papers/paper directory for viewing in the browser.
    
    Args:
        request: The HTTP request object
        filename: The name of the PDF file to serve
    
    Returns:
        FileResponse: The PDF file response that can be viewed in the browser
        JsonResponse: Error response if file is not found or invalid
    """
    try:
        # Sanitize the filename to prevent directory traversal
        filename = os.path.basename(filename)
        
        # Construct the file path using the same structure as in the URL
        file_path = os.path.join(settings.MEDIA_ROOT, 'papers', 'paper', filename)
        
        # Verify the file exists
        if not os.path.exists(file_path):
            return JsonResponse({"error": f"File not found: {filename}"}, status=404)
        
        # Verify it's a PDF file
        if not filename.lower().endswith('.pdf'):
            return JsonResponse({"error": "Invalid file type"}, status=400)
        
        # Open the file - FileResponse will handle closing it
        try:
            pdf_file = open(file_path, 'rb')
            response = FileResponse(
                pdf_file,
                content_type='application/pdf',
                filename=filename,
                as_attachment=False  # This ensures it displays in browser
            )
        except FileNotFoundError:
            return JsonResponse({"error": f"File not found: {filename}"}, status=404)

        
        # Add cache headers to improve performance
        response['Cache-Control'] = 'public, max-age=3600'
        
        return response
            
    except Exception as e:
        return JsonResponse({"error": f"Error serving PDF: {str(e)}"}, status=500)