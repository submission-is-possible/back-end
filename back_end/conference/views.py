import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from notifications.models import Notification
from users.models import User  # Importa il modello User dall'app users
from papers.models import Paper
from reviews.models import Review
from .models import Conference  # Importa il modello Conference creato in precedenza
from conference_roles.models import ConferenceRole
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view
from users.decorators import get_user
import csv
import io
from django.core.paginator import Paginator


# create_conference view
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING, description='Title of the conference'),
            'deadline': openapi.Schema(type=openapi.TYPE_STRING, description='Deadline for submissions'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description of the conference'),
            'reviewers': openapi.Schema(type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                                            'email': openapi.Schema(type=openapi.TYPE_STRING,
                                                                    description='Email of reviewer')
                                        }))
        }
    ),
    responses={
        201: openapi.Response('Conference created successfully'),
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
            data = json.loads(request.body)
            title = data.get('title')
            deadline = data.get('deadline')
            description = data.get('description')
            reviewers = data.get('reviewers')

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

            # Crea il ruolo di amministratore per l'utente
            ConferenceRole.objects.create(
                user=admin_user,
                conference=conference,
                role='admin'
            )

            # Invia gli inviti ai revisori
            for reviewer in reviewers or []:
                reviewer_email = reviewer.get('email')
                if not reviewer_email:
                    continue

                try:
                    reviewer_user = User.objects.get(email=reviewer_email)
                except User.DoesNotExist:
                    return JsonResponse({'error': f'Reviewer user not found: {reviewer_email}'}, status=404)

                if reviewer_user == admin_user:
                    return JsonResponse({'error': 'Cannot invite yourself as a reviewer'}, status=400)

                # Crea solo la notifica, il ruolo verrà creato dopo l'accettazione
                Notification.objects.create(
                    user_sender=admin_user,
                    user_receiver=reviewer_user,
                    conference=conference,
                    status=0,  # pending
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


@swagger_auto_schema(
    method='get',
    operation_description='Get all conferences using pagination',
    responses={
        200: openapi.Response('Conferences retrieved successfully'),
        404: 'No conferences found',
        405: 'Method not allowed',
    }
)
@api_view(['GET'])
@csrf_exempt
def get_conferences(request):
    if request.method == 'GET':
        page_number = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
    
        conferences = Conference.objects.all().order_by('created_at')
        conferences_list = []
        for conference in conferences:
            conferences_list.append({
                'id': conference.id,
                'title': conference.title,
                'deadline': conference.deadline,
                'description': conference.description,
                'admin_id': conference.admin_id.email,
                'created_at': conference.created_at
            })

        paginator = Paginator(conferences_list, page_size)
        page = paginator.get_page(page_number)

        response_data = {
            "current_page": page.number,
            "total_pages": paginator.num_pages,
            "total_conferences": paginator.count,
            "conferences": list(page)
        }

        return JsonResponse(response_data, safe=False, status=200)
    else:
        return JsonResponse({'error': 'Only GET requests are allowed'}, status=405)
    

''' esempio json di ritorno della funzione:
CASO UTENTE AUTHOR
{
    "current_page": 1,
    "total_pages": 1,
    "total_papers": 2,
    "user_roles": ["author"],
    "papers": [
        {
            "id": 1,
            "title": "Machine Learning Applications in Healthcare",
            "status": "submitted",
            "author": {
                "id": 123,
                "name": "Mario Rossi"
            }
        },
        {
            "id": 4,
            "title": "Deep Learning for Image Recognition",
            "status": "accepted",
            "author": {
                "id": 123,
                "name": "Mario Rossi"
            }
        }
    ]
}

CASO UTENTE REVIEWER
{
    "current_page": 1,
    "total_pages": 2,
    "total_papers": 3,
    "user_roles": ["reviewer"],
    "papers": [
        {
            "id": 2,
            "title": "Blockchain Technology in Finance",
            "status": "submitted",
            "author": {
                "id": 456,
                "name": "Giuseppe Verdi"
            },
            "review": {
                "score": 8,
                "comment": "Excellent analysis of blockchain applications. Some minor improvements needed in methodology section.",
                "created_at": "2024-11-25T14:30:00Z"
            }
        },
        {
            "id": 5,
            "title": "IoT Security Challenges",
            "status": "rejected",
            "author": {
                "id": 789,
                "name": "Anna Bianchi"
            },
            "review": {
                "score": 4,
                "comment": "The security analysis lacks depth and current references.",
                "created_at": "2024-11-24T09:15:00Z"
            }
        }
    ]
}

CASO UTENTE ADMIN
{
    "current_page": 1,
    "total_pages": 3,
    "total_papers": 8,
    "user_roles": ["admin"],
    "papers": [
        {
            "id": 1,
            "title": "Machine Learning Applications in Healthcare",
            "status": "submitted",
            "author": {
                "id": 123,
                "name": "Mario Rossi"
            }
        },
        {
            "id": 2,
            "title": "Blockchain Technology in Finance",
            "status": "submitted",
            "author": {
                "id": 456,
                "name": "Giuseppe Verdi"
            }
        },
        {
            "id": 3,
            "title": "Cloud Computing Optimization",
            "status": "accepted",
            "author": {
                "id": 789,
                "name": "Anna Bianchi"
            }
        },
        {
            "id": 4,
            "title": "Deep Learning for Image Recognition",
            "status": "accepted",
            "author": {
                "id": 123,
                "name": "Mario Rossi"
            }
        }
    ]
}

CASO UTENTE RUOLI MULTIPLI
{
    "current_page": 1,
    "total_pages": 2,
    "total_papers": 4,
    "user_roles": ["author", "reviewer"],
    "papers": [
        {
            "id": 1,
            "title": "Machine Learning Applications in Healthcare",
            "status": "submitted",
            "author": {
                "id": 123,
                "name": "Mario Rossi"
            }
        },
        {
            "id": 2,
            "title": "Blockchain Technology in Finance",
            "status": "submitted",
            "author": {
                "id": 456,
                "name": "Giuseppe Verdi"
            },
            "review": {
                "score": 8,
                "comment": "Excellent analysis of blockchain applications.",
                "created_at": "2024-11-25T14:30:00Z"
            }
        }
    ]
}
'''
@csrf_exempt
@swagger_auto_schema(
    method='get',
    operation_description="Get papers for a specific user in a conference based on their role.",
    manual_parameters=[
        openapi.Parameter(
            'page', openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER
        ),
        openapi.Parameter(
            'page_size', openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER
        ),
    ],
    responses={
        200: openapi.Response(description="List of papers based on user's role"),
        400: openapi.Response(description="Missing parameters or invalid JSON"),
        403: openapi.Response(description="User not authorized for this conference"),
        404: openapi.Response(description="Conference not found"),
        405: openapi.Response(description="Method not allowed")
    }
)
@api_view(['GET'])
def get_conference_papers_by_user_role(request):
    """
    Return papers based on user's role in the conference with pagination.
    Expects user_id and conference_id in the request body.
    """
    if request.method != 'GET':
        return JsonResponse({"error": "Only GET requests are allowed"}, status=405)

    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        conference_id = data.get('conference_id')

        if not user_id or not conference_id:
            return JsonResponse({
                "error": "Both user_id and conference_id are required"
            }, status=400)

        # Get user roles in the conference
        user_roles = ConferenceRole.objects.filter(
            user_id=user_id,
            conference_id=conference_id
        )

        if not user_roles.exists():
            return JsonResponse({
                "error": "User is not associated with this conference"
            }, status=403)

        # Get papers based on user roles
        papers_query = None
        user_roles_list = [role.role for role in user_roles]

        if 'admin' in user_roles_list:
            # Admin sees all papers in the conference
            papers_query = Paper.objects.filter(conference_id=conference_id)
        
        elif 'reviewer' in user_roles_list:
            # Reviewer sees papers they've reviewed
            reviewed_papers = Review.objects.filter(
                user_id=user_id,
                paper__conference_id=conference_id
            ).values_list('paper_id', flat=True)
            papers_query = Paper.objects.filter(id__in=reviewed_papers)
        
        elif 'author' in user_roles_list:
            # Author sees their own papers
            papers_query = Paper.objects.filter(
                conference_id=conference_id,
                author_id=user_id
            )

        if papers_query is None:
            return JsonResponse({
                "error": "Invalid role configuration"
            }, status=400)

        # Pagination
        page_number = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        
        paginator = Paginator(papers_query, page_size)
        page_obj = paginator.get_page(page_number)

        # Prepare paper data
        papers_data = []
        for paper in page_obj:
            paper_data = {
                "id": paper.id,
                "title": paper.title,
                "status": paper.status_id,
                "author": {
                    "id": paper.author_id.id,
                    "name": f"{paper.author_id.first_name} {paper.author_id.last_name}"
                }
            }
            
            # Add review information if user is a reviewer
            if 'reviewer' in user_roles_list:
                review = Review.objects.filter(
                    paper_id=paper.id,
                    user_id=user_id
                ).first()
                if review:
                    paper_data["review"] = {
                        "score": review.score,
                        "comment": review.comment_text,
                        "created_at": review.created_at.isoformat()
                    }
            
            papers_data.append(paper_data)

        response_data = {
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "total_papers": paginator.count,
            "user_roles": user_roles_list,
            "papers": papers_data
        }

        return JsonResponse(response_data, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
