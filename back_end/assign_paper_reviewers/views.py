from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from conference.models import Conference
from papers.models import Paper
from paper_reviews.models import PaperReviewAssignment
from users.models import User
from conference_roles.models import ConferenceRole
from assign_paper_reviewers.models import PaperReviewer
import json
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view

'''
esempio di richiesta post:
{
  "current_user_id": 1,
  "conference_id": 42,
  "paper_id": 101,
  "reviewer_ids": [7, 8, 9]
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
            'reviewer_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER), description='List of reviewer IDs to be assigned')
        },
    ),
    responses={
        201: 'Reviewers assigned successfully.',
        400: 'Bad request: Missing required fields or invalid reviewer IDs.',
        403: 'Permission denied: Only the conference admin can assign reviewers.',
        404: 'Not found: Paper not found in this conference.',
    }
)
@api_view(['POST'])
def assign_reviewers_to_paper(request):
    """
    Assegna uno o più reviewers a un paper di una conferenza.
    """
    data = request.data
    current_user_id = data.get("current_user_id")
    conference_id = data.get("conference_id")
    paper_id = data.get("paper_id")
    reviewer_ids = data.get("reviewer_ids")

    # Controllo dei dati obbligatori
    if not all([current_user_id, conference_id, paper_id, reviewer_ids]):
        return JsonResponse({"error": "Missing required fields."}, status=400)

    # Controllo se l'utente corrente è l'admin della conferenza
    try:
        conference = Conference.objects.get(id=conference_id, admin_id=current_user_id)
    except Conference.DoesNotExist:
        return JsonResponse({"error": "Unauthorized. Only the admin can assign reviewers."}, status=403)

    # Controllo se tutti i reviewer_ids sono reviewer nella conferenza
    valid_reviewers = ConferenceRole.objects.filter(
        conference=conference, role='reviewer', user_id__in=reviewer_ids
    ).values_list('user_id', flat=True)

    invalid_reviewers = set(reviewer_ids) - set(valid_reviewers)
    if invalid_reviewers:
        return JsonResponse(
            {"error": f"Invalid reviewer IDs: {list(invalid_reviewers)}"},
            status=400
        )

    # Verifico l'esistenza del paper
    try:
        paper = Paper.objects.get(id=paper_id, conference=conference)
    except Paper.DoesNotExist:
        return JsonResponse({"error": "Paper not found in this conference."}, status=400)

    # Assegno i reviewers al paper
    assignments = []
    for reviewer_id in reviewer_ids:
        PaperReviewer.objects.create(
            reviewer_id=reviewer_id,
            paper=paper,
            conference=conference,
            status="assigned"
        )
        assignments.append({
            "reviewer_id": reviewer_id,
            "status": "assigned"
        })

    return JsonResponse(
        {
            "message": "Reviewers assigned successfully.",
            "assignments": assignments
        },status=201)