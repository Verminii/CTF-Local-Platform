from django.http import JsonResponse
from django.shortcuts import render, HttpResponse
from .models import ToDoItem
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

def home(request):
    return render(request, 'homePage.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return JsonResponse({"redirect": "/mainhub", "message": "Login successful!"})
        else:
            return JsonResponse({"message": "Invalid credentials."})
    return JsonResponse({"message": "Please fill in the form."})

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            return JsonResponse({"message": "User already exists"})

        user = User.objects.create_user(
            username=username,
            password=password
        )

        return JsonResponse({"message": "User created successfully"})

@login_required
def mainhub(request):
    return render(request, 'mainhub.html')

def todos(request):
    items = ToDoItem.objects.all()
    return render(request, 'todos.html', {'todo_items': items})