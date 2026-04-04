from django.http import JsonResponse
from django.shortcuts import render, HttpResponse
from .models import ToDoItem, Challenge
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import os
from django.conf import settings
from django.http import Http404, FileResponse
from pathlib import Path

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
    # Auto-scan storage/ for new challenges and add to DB
    from pathlib import Path
    from django.conf import settings

    storage_path = Path(settings.MEDIA_ROOT)
    existing_folders = set(Challenge.objects.values_list('folder_name', flat=True))

    for folder_path in storage_path.iterdir():
        if folder_path.is_dir():
            folder_name = folder_path.name
            if folder_name not in existing_folders:
                # Create challenge automatically
                title = folder_name.replace('_', ' ').title()
                Challenge.objects.create(
                    title=title,
                    description=f"Auto-detected challenge: {folder_name}",
                    folder_name=folder_name
                )

    challenges = Challenge.objects.all()
    return render(request, 'mainhub.html', {'challenges': challenges})

@login_required
def challenge_detail(request, folder_name):
    try:
        challenge = Challenge.objects.get(folder_name=folder_name)
    except Challenge.DoesNotExist:
        raise Http404("Challenge not found")

    challenge_path = Path(settings.MEDIA_ROOT) / folder_name

    if not challenge_path.exists():
        raise Http404("Challenge folder not found")

    # Get all files in the challenge folder
    files = []
    text_files = []

    for file_path in challenge_path.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(challenge_path)
            files.append({
                'name': file_path.name,
                'path': str(relative_path),
                'size': file_path.stat().st_size,
                'is_text': file_path.suffix.lower() in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json']
            })

            # Read text files
            if file_path.suffix.lower() in ['.txt', '.md']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    text_files.append({
                        'name': file_path.name,
                        'path': str(relative_path),
                        'content': content
                    })
                except UnicodeDecodeError:
                    # If file can't be decoded as text, treat as binary
                    pass

    return render(request, 'challenge_detail.html', {
        'challenge': challenge,
        'files': files,
        'text_files': text_files
    })

@login_required
def download_file(request, folder_name, file_path):
    try:
        challenge = Challenge.objects.get(folder_name=folder_name)
    except Challenge.DoesNotExist:
        raise Http404("Challenge not found")

    full_path = Path(settings.MEDIA_ROOT) / folder_name / file_path

    if not full_path.exists() or not full_path.is_file():
        raise Http404("File not found")

    # Security check: ensure the file is within the challenge folder
    try:
        full_path.relative_to(Path(settings.MEDIA_ROOT) / folder_name)
    except ValueError:
        raise Http404("Access denied")

    try:
        return FileResponse(open(full_path, 'rb'), as_attachment=True, filename=full_path.name)
    except FileNotFoundError:
        raise Http404("File not found")

def todos(request):
    items = ToDoItem.objects.all()
    return render(request, 'todos.html', {'todo_items': items})