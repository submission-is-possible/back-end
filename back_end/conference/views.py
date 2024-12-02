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

from notifications.models import Notification
from users.models import User  # Importa il modello User dall'app users
from papers.models import Paper
from reviews.models import Review
from .models import Conference  # Importa il modello Conference creato in precedenza
from conference_roles.models import ConferenceRole
from assign_paper_reviewers.models import PaperReviewAssignment
import  assign_paper_reviewers, conference_roles, notifications, papers

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

            reviewersAreAllValid = True

            for reviewer in reviewers or []:
                reviewer_email = reviewer.get('email')
                if not reviewer_email:
                    continue

                try:
                    reviewer_user = User.objects.get(email=reviewer_email)
                except User.DoesNotExist:
                    reviewersAreAllValid = False
                    break

            if not reviewersAreAllValid:
                return JsonResponse({'error': 'One or more reviewers are invalid or do not exist'}, status=400)

            # Create the new conference
            conference = Conference.objects.create(
                title=title,
                admin_id=admin_user,
                created_at=timezone.now(),
                deadline=deadline,
                description=description
            )

            # Create the admin role for the user
            ConferenceRole.objects.create(
                user=admin_user,
                conference=conference,
                role='admin'
            )

            # Send invitations to reviewers
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

                # Create only the notification, the role will be created after acceptance
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

                # Elimina tutte le cascades in cui la conferenza è coinvolta
                assign_paper_reviewers.models.PaperReviewAssignment.objects.filter(conference=conference).delete()
                conference_roles.models.ConferenceRole.objects.filter(conference=conference).delete()
                notifications.models.Notification.objects.filter(conference=conference).delete()
                papers.models.Paper.objects.filter(conference=conference).delete()


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
            reviewers = data.get('reviewers')

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
            if reviewers:
                # Invia gli inviti ai revisori
                for reviewer in reviewers or []:
                    reviewer_email = reviewer.get('email')
                    if not reviewer_email:
                        continue

                    try:
                        reviewer_user = User.objects.get(email=reviewer_email)
                    except User.DoesNotExist:
                        return JsonResponse({'error': f'Reviewer user not found: {reviewer_email}'}, status=404)

                    if reviewer_user == user:
                        return JsonResponse({'error': 'Cannot invite yourself as a reviewer'}, status=400)

                    # check if reviewer is already invited
                    if Notification.objects.filter(
                        user_sender=user,
                        user_receiver=reviewer_user,
                        conference=conference,
                        type=1  # reviewer type
                    ).exists():
                        return JsonResponse({'error': f'Reviewer {reviewer_email} is already invited'}, status=400)

                    # Crea solo la notifica, il ruolo verrà creato dopo l'accettazione
                    Notification.objects.create(
                        user_sender=user,
                        user_receiver=reviewer_user,
                        conference=conference,
                        status=0,  # pending
                        type=1  # reviewer type
                    )

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
    
'''
Tutti i paper che un reviewer ha recensito in una conferenza Endpoint
URL: POST /api/conference/papers/reviewer/?page=1&page_size=10
Request Body:
{
    "user_id": 123,
    "conference_id": 456
}

Response:
{
    "current_page": 1,
    "total_pages": 3,
    "total_papers": 25,
    "papers": [
        {
            "id": 1,
            "title": "Blockchain Applications in Supply Chain",
            "author": "John Smith",
            "paper_status": "accepted",
            "review_status": "assigned"
        },
        // ... altri paper
    ]
}
'''
@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Get papers assigned to a specific user in a conference.",
    manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        },
        required=['user_id', 'conference_id']
    ),
    responses={
        200: openapi.Response(description="List of assigned papers"),
        400: openapi.Response(description="Invalid request"),
        403: openapi.Response(description="User not authorized"),
    }
)
@api_view(['POST'])
@get_user
def get_paper_inconference_reviewer(request):
    """Return all papers assigned to a reviewer in a conference, with pagination."""
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        user_id = request.data.get('user_id')
        conference_id = request.data.get('conference_id')

        # Verifica che l'utente sia reviewer nella conferenza
        is_reviewer = ConferenceRole.objects.filter(
            user_id=user_id,
            conference_id=conference_id,
            role='reviewer'
        ).exists()

        if not is_reviewer:
            return JsonResponse({
                "error": "User is not a reviewer in this conference"
            }, status=403)

        # Ottieni tutti i paper assegnati al reviewer in questa conferenza
        assignments = PaperReviewAssignment.objects.filter(
            reviewer_id=user_id,
            conference_id=conference_id
        ).select_related('paper', 'paper__author_id') #Ottimizza le query al database effettuando un join SQL 
        #per pre-caricare i dati relativi: paper: Recupera l'oggetto Paper associato a ciascuna assegnazione di revisione.
                                # paper__author_id: Recupera anche il campo author_id (l'autore del paper) dell'oggetto Paper.

        # Paginazione
        page_number = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        paginator = Paginator(assignments, page_size)
        page_obj = paginator.get_page(page_number)

        papers_data = [{
            "id": assignment.paper.id,
            "title": assignment.paper.title,
            "author": assignment.paper.author_id.last_name + " " + assignment.paper.author_id.first_name,
            "status": assignment.paper.status_id,  # status del paper (submitted/accepted/rejected)
            "paper_file": assignment.paper.paper_file.url if assignment.paper.paper_file else None,
        } for assignment in page_obj]

        return JsonResponse({
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "total_papers": paginator.count,
            "papers": papers_data
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

'''
paper che un Author ha submittato nella conferenza Endpoint
URL: POST /api/conference/papers/author/?page=1&page_size=10
Request Body:
{
    "user_id": 789,
    "conference_id": 456
}

Response:
{
    "current_page": 1,
    "total_pages": 2,
    "total_papers": 15,
    "papers": [
        {
            "id": 1,
            "title": "Neural Networks in Natural Language Processing",
            "status": "accepted",
            "author": {
                "id": 789,
                "name": "John Smith"
            }
        },
        // ... altri paper
    ]
}
'''
@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Get papers authored by a specific user in a conference.",
    manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        },
        required=['user_id', 'conference_id']
    ),
    responses={
        200: openapi.Response(description="List of authored papers"),
        400: openapi.Response(description="Invalid request"),
        403: openapi.Response(description="User not authorized"),
    }
)
@api_view(['POST'])
@get_user
def get_paper_inconference_author(request):
    """Return papers authored by the user in a specific conference with pagination."""
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        user_id = request.user.id
        conference_id = request.data.get('conference_id')

        # Verifica che l'utente sia author nella conferenza
        is_author = ConferenceRole.objects.filter(
            user_id=user_id,
            conference_id=conference_id,
            role='author'
        ).exists()

        if not is_author:
            return JsonResponse({
                "error": "User is not an author in this conference"
            }, status=403)

        # Ottieni i paper dell'autore
        authored_papers = Paper.objects.filter(
            conference_id=conference_id,
            author_id=user_id
        )

        # Pagination
        page_number = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        paginator = Paginator(authored_papers, page_size)
        page_obj = paginator.get_page(page_number)

        papers_data = [{
            "id": paper.id,
            "title": paper.title,
            "status": paper.status_id,
            "author": paper.author_id.last_name + " " + paper.author_id.first_name,
            "paper_file": paper.paper_file.url if paper.paper_file else None,
        } for paper in page_obj]

        return JsonResponse({
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "total_papers": paginator.count,
            "papers": papers_data
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

'''
Admin Endpoint --> ritorna tutti i paper di quella conferenza
URL: POST /api/conference/papers/admin/?page=1&page_size=10
Request Body:
{
    "user_id": 999,
    "conference_id": 456
}

Response:
{
    "current_page": 1,
    "total_pages": 5,
    "total_papers": 50,
    "papers": [
        {
            "id": 1,
            "title": "Blockchain Applications in Supply Chain",
            "status": "under_review",
            "author": {
                "id": 789,
                "name": "John Smith"
            }
        },
        // ... altri paper
    ]
}
'''
@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Get all papers in a conference (admin only).",
    manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        },
        required=['user_id', 'conference_id']
    ),
    responses={
        200: openapi.Response(description="List of all conference papers"),
        400: openapi.Response(description="Invalid request"),
        403: openapi.Response(description="User not authorized"),
    }
)
@api_view(['POST'])
@get_user
def get_paper_inconference_admin(request):
    """Return all papers in a conference for admin with pagination."""
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    try:
        user_id = request.user.id
        conference_id = request.data.get('conference_id')

        # Verifica che l'utente sia admin nella conferenza
        is_admin = ConferenceRole.objects.filter(
            user_id=user_id,
            conference_id=conference_id,
            role='admin'
        ).exists()

        if not is_admin:
            return JsonResponse({
                "error": "User is not an admin in this conference"
            }, status=403)

        # Ottieni tutti i paper della conferenza
        all_papers = Paper.objects.filter(
            conference_id=conference_id
        ).select_related('author_id')

        # Pagination
        page_number = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        paginator = Paginator(all_papers, page_size)
        page_obj = paginator.get_page(page_number)

        papers_data = [{
            "id": paper.id,
            "title": paper.title,
            "status": paper.status_id,
            "author": paper.author_id.last_name + " " + paper.author_id.first_name,
            "paper_file": paper.paper_file.url if paper.paper_file else None,
        } for paper in page_obj]

        return JsonResponse({
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "total_papers": paginator.count,
            "papers": papers_data
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)