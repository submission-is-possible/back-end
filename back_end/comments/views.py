from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.utils import json

import users.decorators
from comments.models import Comment
from reviews.models import Review
from users.models import User


## funzione che crea un commento per una recensione
@swagger_auto_schema(
    method='post',
    operation_description="Create a new comment for a review.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id_review': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the review'),
            'text': openapi.Schema(type=openapi.TYPE_STRING, description='Text of the comment')
        },
        required=['id_review', 'text']
    ),
    responses={
        201: openapi.Response(description="Comment added successfully"),
        400: openapi.Response(description="Missing fields"),
        404: openapi.Response(description="Review not found"),
        405: openapi.Response(description="Only POST requests are allowed")
    }
)
@api_view(['POST'])
@csrf_exempt
def create_comment(request):
    """
    Create a new comment for a review.
    """
    if request.method == 'POST':
        try:
            # Parse the incoming JSON
            data = json.loads(request.body)
            review_id = data.get('id_review')
            comment_text = data.get('text')

            # Validate required fields
            if not review_id or not comment_text:
                return JsonResponse({'error': 'Missing fields'}, status=400)

            # Verify the review exists
            try:
                review = Review.objects.get(id=review_id)
            except Review.DoesNotExist:
                return JsonResponse({'error': 'Review not found'}, status=404)

            # Get the logged-in user
            user = request.user
            if not user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=403)

            # Create and save the comment
            comment = Comment.objects.create(
                user=user,
                review=review,
                comment_text=comment_text
            )

            return JsonResponse({
                'id': comment.id,
                'review_id': comment.review.id,
                'user_id': comment.user.id,
                'comment_text': comment.comment_text,
                'created_at': comment.created_at.isoformat()
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'detail': f'Method "{request.method}" not allowed.'}, status=405)



## funzione che restituisce tutti i commenti di una recensione
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all comments.",
    responses={
        200: openapi.Response(description="List of comments"),
    }
)
@api_view(['GET'])
def get_all_comments(request):
    """
    Retrieve all comments.
    """
    if request.method == 'GET':
        comments = Comment.objects.all()
        comments_data = [
            {
                'id': comment.id,
                'review_id': comment.review.id,
                'user_id': comment.user.id,
                'comment_text': comment.comment_text,
                'created_at': comment.created_at.isoformat()
            }
            for comment in comments
        ]
        return JsonResponse(comments_data, safe=False, status=200)

    return JsonResponse({'detail': f'Method "{request.method}" not allowed.'}, status=405)


## funzione che restituisce un commento specifico
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a specific comment by ID.",
    responses={
        200: openapi.Response(description="Comment details"),
        404: openapi.Response(description="Comment not found"),
    }
)
@api_view(['GET'])
def get_comment_by_id(request, comment_id):
    """
    Retrieve a specific comment by ID.
    """
    if request.method == 'GET':
        try:
            comment = Comment.objects.get(id=comment_id)
            comment_data = {
                'id': comment.id,
                'review_id': comment.review.id,
                'user_id': comment.user.id,
                'comment_text': comment.comment_text,
                'created_at': comment.created_at.isoformat()
            }
            return JsonResponse(comment_data, status=200)

        except Comment.DoesNotExist:
            return JsonResponse({'error': 'Comment not found'}, status=404)

    return JsonResponse({'detail': f'Method "{request.method}" not allowed.'}, status=405)


## funzione che modifica un commento
@swagger_auto_schema(
    method='patch',
    operation_description="Update an existing comment by ID.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'comment_text': openapi.Schema(type=openapi.TYPE_STRING, description="Updated text for the comment")
        },
        required=['comment_text']
    ),
    responses={
        200: openapi.Response(description="Comment updated successfully"),
        400: openapi.Response(description="Invalid input"),
        404: openapi.Response(description="Comment not found"),
        403: openapi.Response(description="Unauthorized"),
    }
)
@api_view(['PATCH'])
def update_comment(request, comment_id):
    """
    Update an existing comment by ID.
    """
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)
            comment_text = data.get('comment_text')

            if not comment_text:
                return JsonResponse({'error': 'Invalid input: comment_text is required'}, status=400)

            try:
                comment = Comment.objects.get(id=comment_id)

                # Check if the current user is the author of the comment
                if request.user != comment.user:
                    return JsonResponse({'error': 'Unauthorized'}, status=403)

                # Update the comment
                comment.comment_text = comment_text
                comment.save()

                return JsonResponse({
                    'id': comment.id,
                    'review_id': comment.review.id,
                    'user_id': comment.user.id,
                    'comment_text': comment.comment_text,
                    'updated_at': comment.created_at.isoformat()
                }, status=200)

            except Comment.DoesNotExist:
                return JsonResponse({'error': 'Comment not found'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'detail': f'Method "{request.method}" not allowed.'}, status=405)


## funzione che restituisce tutti i commenti di un paper (SIP 125
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all comments for a specific paper.",
    responses={
        200: openapi.Response(description="List of comments for the paper"),
        404: openapi.Response(description="Paper not found"),
    }
)
@api_view(['GET'])
def get_comments_by_paper(request, paper_id):
    """
    Retrieve all comments for a specific paper.
    """
    if request.method == 'GET':
        try:
            # Verifica se il paper esiste
            reviews = Review.objects.filter(paper_id=paper_id)

            if not reviews.exists():
                return JsonResponse({'error': 'Paper not found'}, status=404)

            # Recupera tutti i commenti associati al paper
            comments = Comment.objects.filter(review__in=reviews)

            # Serializza i commenti
            comments_data = [
                {
                    'id': comment.id,
                    'review_id': comment.review.id,
                    'user_id': comment.user.id,
                    'comment_text': comment.comment_text,
                    'created_at': comment.created_at.isoformat()
                }
                for comment in comments
            ]

            return JsonResponse(comments_data, safe=False, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'detail': f'Method "{request.method}" not allowed.'}, status=405)



## delete di un commento
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a specific comment by ID.",
    responses={
        204: openapi.Response(description="Comment deleted successfully"),
        404: openapi.Response(description="Comment not found"),
    }
)
@api_view(['DELETE'])
def delete_comment(request, comment_id):
    """
    Delete a specific comment by ID.
    """
    if request.method == 'DELETE':
        try:
            # Recupera il commento
            comment = Comment.objects.get(id=comment_id)
            comment.delete()
            return JsonResponse({'success': 'Comment deleted successfully'}, status=204)
        except Comment.DoesNotExist:
            return JsonResponse({'error': 'Comment not found'}, status=404)

    return JsonResponse({'detail': f'Method "{request.method}" not allowed.'}, status=405)



## delete di tutti i commenti per un paper
@swagger_auto_schema(
    method='delete',
    operation_description="Delete all comments associated with a specific paper.",
    responses={
        204: openapi.Response(description="All comments for the paper deleted successfully"),
        404: openapi.Response(description="Paper not found"),
    }
)
@api_view(['DELETE'])
def delete_comments_by_paper(request, paper_id):
    """
    Delete all comments associated with a specific paper.
    """
    if request.method == 'DELETE':
        try:
            reviews = Review.objects.filter(paper_id=paper_id)
            if not reviews.exists():
                return JsonResponse({'error': 'Paper not found'}, status=404)

            # Cancella tutti i commenti associati alle recensioni del paper
            Comment.objects.filter(review__in=reviews).delete()
            return JsonResponse({'success': 'All comments for the paper deleted successfully'}, status=204)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'detail': f'Method "{request.method}" not allowed.'}, status=405)


## delete di tutti i commenti di un utente
@swagger_auto_schema(
    method='delete',
    operation_description="Delete all comments made by a specific user.",
    responses={
        204: openapi.Response(description="All comments by the user deleted successfully"),
        404: openapi.Response(description="User not found"),
    }
)
@api_view(['DELETE'])
def delete_comments_by_user(request, user_id):
    """
    Delete all comments made by a specific user.
    """
    if request.method == 'DELETE':
        try:
            user = User.objects.get(id=user_id)
            # Cancella tutti i commenti fatti dall'utente
            Comment.objects.filter(user=user).delete()
            return JsonResponse({'success': 'All comments by the user deleted successfully'}, status=204)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

    return JsonResponse({'detail': f'Method "{request.method}" not allowed.'}, status=405)

## delete di tutti i commenti per una review

@swagger_auto_schema(
    method='delete',
    operation_description="Delete all comments for a specific review.",
    responses={
        204: openapi.Response(description="All comments for the review deleted successfully"),
        404: openapi.Response(description="Review not found"),
    }
)
@api_view(['DELETE'])
def delete_comments_by_review(request, review_id):
    """
    Delete all comments for a specific review.
    """
    if request.method == 'DELETE':
        try:
            review = Review.objects.get(id=review_id)
            # Cancella tutti i commenti associati alla review
            Comment.objects.filter(review=review).delete()
            return JsonResponse({'success': 'All comments for the review deleted successfully'}, status=204)
        except Review.DoesNotExist:
            return JsonResponse({'error': 'Review not found'}, status=404)

    return JsonResponse({'detail': f'Method "{request.method}" not allowed.'}, status=405)




