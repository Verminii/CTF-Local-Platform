from django.http import JsonResponse
from django.shortcuts import render, HttpResponse
from .models import ToDoItem

# Create your views here.
def home(request):
    return render(request, 'homePage.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username == 'admin' and password == 'admin':
            return JsonResponse({"message": "Login successful!"})
        else:
            return JsonResponse({"message": "Invalid credentials."})
    return JsonResponse({"message": "Only POST allowed."})

def todos(request):
    items = ToDoItem.objects.all()
    return render(request, 'todos.html', {'todo_items': items})