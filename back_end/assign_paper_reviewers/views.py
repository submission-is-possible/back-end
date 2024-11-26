from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from conference.models import Conference
from papers.models import Paper
from paper_reviews.models import PaperReviewAssignment
from users.models import User
import json

@csrf_exempt
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