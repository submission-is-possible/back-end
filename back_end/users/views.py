from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password, check_password
from .models import User
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
import json
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view


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
@swagger_auto_schema(
    method='post',
operation_description="Create a new user with first name, last name, email, and password.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name of the user'),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name of the user'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the user'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password for the user'),
        },
        required=['first_name', 'last_name', 'email', 'password']
    ),
    responses={
        201: openapi.Response(description="User created successfully"),
        400: openapi.Response(description="Missing fields or email already in use"),
        405: openapi.Response(description="Only POST requests are allowed"),
    }
)
@api_view(['POST'])
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
                password=make_password(password)
            )
            return JsonResponse({'message': f"User {user.first_name} created!"}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except IntegrityError:
            return JsonResponse({'error': 'Database integrity error'}, status=400)
    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)



@csrf_exempt
@swagger_auto_schema(
    method='post',
    operation_description="Login user with email and password.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the user'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password of the user'),
        },
        required=['email', 'password']
    ),
    responses={
        200: openapi.Response(description="Login successful"),
        400: openapi.Response(description="Email and password are required or Invalid JSON"),
        401: openapi.Response(description="Invalid email or password"),
        405: openapi.Response(description="Only POST requests are allowed"),
    }
)
@api_view(['POST'])
def login_user(request):
    if request.method == 'POST':
        try:
            # Estrai i dati dal body della richiesta
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            print(email, password)

            # Verifica che i campi siano presenti
            if not (email and password):
                return JsonResponse({'error': 'Email and password are required.'}, status=400)

             # Cerca l'utente tramite email
            try:
                user = User.objects.get(email=email)
                # Confronta la password fornita con quella salvata nel database
                if check_password(password, user.password):
                    # Registra l'utente nella sessione
                    login(request, user)  
                    return JsonResponse({'message': 'Login successful', 'user_id': user.id}, status=200)
                else:
                    return JsonResponse({'error': 'Invalid email or password'}, status=401)
            except User.DoesNotExist:
                return JsonResponse({'error': 'Invalid email or password'}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

def list_users(request):
    pass
