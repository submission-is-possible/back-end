from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import User
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
import json

'''
TEST DI PROVA PER VEDERE SE IL LO SCHEMA DEL DATABASE FUNZIONA
def create_user(request):
    user = User.objects.create(
        first_name='Mario',
        last_name='Rossi',
        email='mario.rossi@example.com',
        password='password123'
    )
    return HttpResponse(f"User {user.first_name} created!")
def list_users(request):
    users = User.objects.all()
    response = ', '.join([f"{user.first_name} {user.last_name} {user.email} " for user in users])
    return HttpResponse(f"Users: {response}")
'''

@csrf_exempt  # Disabilita temporaneamente il controllo CSRF (per sviluppo locale)
def create_user(request):
    if request.method == 'POST':
        try:
            # Estrai i dati dal body della richiesta
            data = json.loads(request.body)
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            password = data.get('password')

            # Verifica che tutti i campi siano presenti
            if not (first_name and last_name and email and password):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            # Controlla se esiste già un utente con quell'email
            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Email already in use'}, status=400)

            # Crea il nuovo utente
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password
            )
            return JsonResponse({'message': f"User {user.first_name} created!"}, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        except IntegrityError:
            return JsonResponse({'error': 'Database integrity error'}, status=400)
    
    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

def list_users(request):
    pass
