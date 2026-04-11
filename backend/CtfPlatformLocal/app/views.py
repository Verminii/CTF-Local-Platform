from django.http import JsonResponse, Http404, FileResponse
from django.shortcuts import render, redirect
from .models import ToDoItem, Challenge
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from pathlib import Path
from django.contrib.auth import logout

CHALLENGE_STORAGE = Path(settings.MEDIA_ROOT)


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

        User.objects.create_user(username=username, password=password)
        return JsonResponse({"message": "User created successfully"})

    return JsonResponse({"message": "Please fill in the form."})


def read_text_file(path):
    try:
        return path.read_text(encoding='utf-8').strip()
    except FileNotFoundError:
        return ""


def scan_storage_and_sync_challenges():
    if not CHALLENGE_STORAGE.exists():
        return

    existing_folders = set(Challenge.objects.values_list('folder_name', flat=True))

    for folder_path in CHALLENGE_STORAGE.iterdir():
        if not folder_path.is_dir():
            continue

        folder_name = folder_path.name

        if folder_name not in existing_folders:
            title = folder_name.replace('_', ' ').title()
            description_path = folder_path / 'description.txt'
            description = read_text_file(description_path) or f"Challenge: {title}"

            Challenge.objects.create(
                title=title,
                description=description,
                folder_name=folder_name
            )


@login_required
def mainhub(request):
    scan_storage_and_sync_challenges()
    challenges = Challenge.objects.all().order_by('id')

    for challenge in challenges:
        challenge_path = CHALLENGE_STORAGE / challenge.folder_name
        short_description_path = challenge_path / 'short_description.txt'
        challenge.short_description = read_text_file(short_description_path) or challenge.description

    return render(request, 'mainhub.html', {'challenges': challenges})

@login_required
def challenge_detail(request, folder_name):
    try:
        challenge = Challenge.objects.get(folder_name=folder_name)
    except Challenge.DoesNotExist:
        raise Http404("Challenge not found")

    challenge_path = CHALLENGE_STORAGE / folder_name
    if not challenge_path.exists():
        raise Http404("Challenge folder not found")

    description_path = challenge_path / 'description.txt'
    flag_path = challenge_path / 'flag' / 'flag.txt'
    short_description_path = challenge_path / 'short_description.txt'
    short_description = read_text_file(short_description_path)
    resources_dir = challenge_path / 'resources'
    hints_dir = challenge_path / 'hints'

    description = read_text_file(description_path)
    files = []
    if resources_dir.exists() and resources_dir.is_dir():
        for file_path in sorted(resources_dir.rglob('*')):
            if file_path.is_file():
                rel_path = file_path.relative_to(challenge_path)
                files.append({
                    'name': file_path.name,
                    'path': str(rel_path).replace('\\', '/'),
                    'size': file_path.stat().st_size,
                })

    hints = []
    if hints_dir.exists() and hints_dir.is_dir():
        for hint_path in sorted(hints_dir.iterdir()):
            if hint_path.is_file() and hint_path.suffix.lower() == '.txt':
                hints.append({
                    'id': hint_path.stem,
                    'title': f'Hint {hint_path.stem}',
                    'content': read_text_file(hint_path),
                })

    return render(request, 'challenge_detail.html', {
        'challenge': challenge,
        'description_text': description,
        'short_description': short_description,
        'files': files,
        'hints': hints,
    })


@login_required
def submit_flag(request, folder_name):
    if request.method != 'POST':
        return JsonResponse({"message": "Invalid method."}, status=405)

    try:
        challenge = Challenge.objects.get(folder_name=folder_name)
    except Challenge.DoesNotExist:
        raise Http404("Challenge not found")

    challenge_path = CHALLENGE_STORAGE / folder_name
    flag_path = challenge_path / 'flag' / 'flag.txt'

    submitted_flag = request.POST.get('flag', '').strip()
    real_flag = read_text_file(flag_path)

    if not real_flag:
        return JsonResponse({"message": "Flag file not found."}, status=404)

    if submitted_flag == real_flag:
        return JsonResponse({"message": "Correct flag!"})
    return JsonResponse({"message": "Wrong flag."})


@login_required
def download_file(request, folder_name, file_path):
    try:
        challenge = Challenge.objects.get(folder_name=folder_name)
    except Challenge.DoesNotExist:
        raise Http404("Challenge not found")

    challenge_path = CHALLENGE_STORAGE / folder_name
    full_path = (challenge_path / file_path).resolve()

    try:
        full_path.relative_to(challenge_path.resolve())
    except ValueError:
        raise Http404("Access denied")

    if not full_path.exists() or not full_path.is_file():
        raise Http404("File not found")

    return FileResponse(open(full_path, 'rb'), as_attachment=True, filename=full_path.name)


@login_required
def user_logout(request):
    logout(request)
    return redirect('home')



def custom_404(request, exception):
    return render(request, '404.html', status=404)

def todos(request):
    items = ToDoItem.objects.all()
    return render(request, 'todos.html', {'todo_items': items})
