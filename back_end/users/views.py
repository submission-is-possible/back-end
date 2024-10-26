from django.shortcuts import render
from django.http import HttpResponse
from .models import User

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

def create_user(request):
    pass

def list_users(request):
    pass
