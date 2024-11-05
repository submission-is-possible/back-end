import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from users.models import User  # Importa il modello User dall'app users
from .models import Conference  # Importa il modello Conference creato in precedenza

@csrf_exempt
def create_conference(request):
    if request.method == 'POST':
        try:
            # Estrai i dati dal body della richiesta
            data = json.loads(request.body)
            title = data.get('title')
            admin_id = data.get('admin_id')
            deadline = data.get('deadline')
            description = data.get('description')

            # Verifica che i campi richiesti siano presenti
            if not (title and admin_id and deadline and description):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            # Verifica se l'utente (admin) esiste
            try:
                admin_user = User.objects.get(id=admin_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'Admin user not found'}, status=404)

            # Crea la nuova conferenza
            conference = Conference.objects.create(
                title=title,
                admin_id=admin_user,
                created_at=timezone.now(),
                deadline=deadline,
                description=description
            )
            return JsonResponse({
                'message': 'Conference created successfully',
                'conference_id': conference.id
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    

@csrf_exempt
def delete_conference(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            conference_id = data.get('conference_id')

            # Verifica che l'ID della conferenza sia fornito
            if not conference_id:
                return JsonResponse({'error': 'Missing conference_id'}, status=400)

            # Cerca la conferenza e eliminala
            try:
                conference = Conference.objects.get(id=conference_id)
                conference.delete()  # Elimina la conferenza
                return JsonResponse({'message': 'Conference deleted successfully'}, status=200)
            except Conference.DoesNotExist:
                return JsonResponse({'error': 'Conference not found'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
