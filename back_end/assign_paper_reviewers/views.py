from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema, logger
from drf_yasg import openapi
from rest_framework.decorators import api_view

from conference.models import Conference
from papers.models import Paper
from assign_paper_reviewers.models import PaperReviewAssignment
from users.decorators import get_user
from users.models import User
from conference_roles.models import ConferenceRole


'''
esempio di richiesta post:
{
  "current_user_id": 1,
  "conference_id": 42,
  "paper_id": 101,
  "reviewer_email": desanti@gmail.com
}
'''
@csrf_exempt
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'current_user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the current user'),
            'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference'),
            'paper_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the paper'),
            'reviewer_email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the reviewer to assign to the paper'),
        },
    ),
    responses={
        201: 'Reviewers assigned successfully.',
        400: 'Bad request: Missing required fields.',
        403: 'Permission denied: Only the conference admin can assign reviewers.',
        404: 'Not found: Paper not found in this conference.',
    }
)
@api_view(['POST'])
def assign_reviewer_to_paper(request):
    """
    Assegna uno o più reviewers a un paper di una conferenza.
    """
    data = request.data
    current_user_id = data.get("current_user_id")
    conference_id = data.get("conference_id")
    paper_id = data.get("paper_id")
    reviewer_email = data.get("reviewer_email")

    # Controllo dei dati obbligatori
    if not all([current_user_id, conference_id, paper_id, reviewer_email]):
        return JsonResponse({"error": "Missing required fields."}, status=400)

    # Controllo se l'utente corrente è l'admin della conferenza
    try:
        conference = Conference.objects.get(id=conference_id, admin_id=current_user_id)
    except Conference.DoesNotExist:
        return JsonResponse({"error": "Unauthorized. Only the admin can assign reviewers."}, status=403)

    # Trovo l'utente tramite l'email
    try:
        reviewer = User.objects.get(email=reviewer_email)
    except User.DoesNotExist:
        return JsonResponse({"error": "Reviewer not found."}, status=404)
    
    # Controllo se l'utente è un reviewer nella conferenza
    is_reviewer = ConferenceRole.objects.filter(
        conference=conference, role='reviewer', user=reviewer
    ).exists()

    if not is_reviewer:
        return JsonResponse({"error": "User is not a reviewer for this conference."}, status=400)

    # Verifico l'esistenza del paper
    try:
        paper = Paper.objects.get(id=paper_id, conference=conference)
    except Paper.DoesNotExist:
        return JsonResponse({"error": "Paper not found in this conference."}, status=400)

    # Assegno il reviewer al paper
    PaperReviewAssignment.objects.create(
        reviewer=reviewer,
        paper=paper,
        conference=conference,
        status="assigned"
    )

    return JsonResponse(
        {
            "message": "Reviewers assigned successfully."
        },status=201)


'''
esempio di richiesta post:
{
  "current_user_id": 1,
  "conference_id": 42,
  "paper_id": 101,
  "reviewer_email":
}
'''
@csrf_exempt
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'current_user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the current user'),
            'conference_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the conference'),
            'paper_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the paper'),
            'reviewer_email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the reviewer to remove')
        },
    ),
    responses={
        201: 'Reviewers removed successfully.',
        400: 'Bad request: Missing required fields.',
        403: 'Permission denied: Only the conference admin can remove reviewers.',
        404: 'Not found: Reviewer not found.',
    }
)
@api_view(['POST'])
def remove_reviewer_from_paper(request):
    """
    Rimuove un reviewers da un paper di una conferenza.
    """
    data = request.data
    current_user_id = data.get("current_user_id")
    conference_id = data.get("conference_id")
    paper_id = data.get("paper_id")
    reviewer_email = data.get("reviewer_email")

    # Controllo dei dati obbligatori
    if not all([current_user_id, conference_id, paper_id, reviewer_email]):
        return JsonResponse({"error": "Missing required fields."}, status=400)

    # Controllo se l'utente corrente è l'admin della conferenza
    try:
        conference = Conference.objects.get(id=conference_id, admin_id=current_user_id)
    except Conference.DoesNotExist:
        return JsonResponse({"error": "Unauthorized. Only the admin can remove reviewers."}, status=403)

    # Trovo l'utente tramite l'email
    try:
        reviewer = User.objects.get(email=reviewer_email)
    except User.DoesNotExist:
        return JsonResponse({"error": "Reviewer not found."}, status=404)
    
    # Controllo se l'utente è un reviewer nella conferenza
    is_reviewer = ConferenceRole.objects.filter(
        conference=conference, role='reviewer', user=reviewer
    ).exists()

    if not is_reviewer:
        return JsonResponse({"error": "User is not a reviewer for this conference."}, status=400)

    # Verifico l'esistenza del paper
    try:
        paper = Paper.objects.get(id=paper_id, conference=conference)
    except Paper.DoesNotExist:
        return JsonResponse({"error": "Paper not found in this conference."}, status=400)

    # Rimuovo il reviewer dal paper
    PaperReviewAssignment.objects.filter(
        reviewer=reviewer,
        paper=paper,
        conference=conference
    ).delete()

    return JsonResponse(
        {
            "message": "Reviewers removed successfully."
        },status=201)


@csrf_exempt
#@get_user
@swagger_auto_schema(
    method='GET',
    responses={
        200: 'Lista dei revisori assegnati al paper.',
        403: 'Permission denied: Only the conference admin can view reviewers.',
        404: 'Not found: No reviewers assigned to this paper.',
    }
)
@api_view(['GET'])
def get_all_reviewers_assigned_to_paper_for_conference(request, conference_id, paper_id):
    '''
    Restituisce tutti i revisori assegnati ad un paper specifico di una conferenza.
    '''

    # Controllo se il paper esiste
    paper = get_object_or_404(Paper, id=paper_id, conference=conference_id)

    # Controllo se la conferenza esiste
    conference = get_object_or_404(Conference, id=conference_id)

    '''
            # SE LA SESSIONE VA, DECOMMENTARE QUESTO BLOCCO DI CODICE #
    
    # Controllo se l'utente corrente è l'admin della conferenza
    if conference.admin_id != request.user.id:
        return JsonResponse({"error": "Unauthorized. Only the admin can view reviewers."}, status=403)
    '''

    try:
        # Trovo tutti i revisori assegnati al paper
        reviewers = PaperReviewAssignment.objects.filter(paper=paper, conference=conference).select_related('reviewer')
    except PaperReviewAssignment.DoesNotExist:
        return JsonResponse({"error": "No reviewers assigned to this paper."}, status=404)

    try:
        # Restituisco i revisori
        return JsonResponse(
            {
                "reviewers": [
                    {
                        "id": reviewer.reviewer.id,
                        "email": reviewer.reviewer.email,
                        "first_name": reviewer.reviewer.first_name,
                        "last_name": reviewer.reviewer.last_name
                    }
                    for reviewer in reviewers
                ]
            }
        )
    except Exception as e:
        # Log dell'errore
        logger.error(f"Error retrieving reviewers: {e}")
        return JsonResponse({"error": str(e)}, status=500)