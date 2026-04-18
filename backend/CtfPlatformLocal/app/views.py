from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import JsonResponse, Http404, FileResponse
from django.shortcuts import render, redirect

from .models import (
    ToDoItem,
    Challenge,
    ChallengeHint,
    ChallengeHintUse,
    ChallengeCompletion,
)

CHALLENGE_STORAGE = Path(settings.MEDIA_ROOT)


def read_text_file(path):
    try:
        return path.read_text(encoding='utf-8').strip()
    except FileNotFoundError:
        return ""


def parse_hint_file(path):
    content = read_text_file(path).strip()
    if not content:
        return 0, ""
    lines = content.splitlines()
    try:
        cost = int(lines[0].strip())
        hint_text = "\n".join(lines[1:]).strip()
    except ValueError:
        cost = 0
        hint_text = content
    return cost, hint_text


def sync_storage_to_db():
    if not CHALLENGE_STORAGE.exists():
        return

    for folder_path in CHALLENGE_STORAGE.iterdir():
        if not folder_path.is_dir():
            continue

        folder_name = folder_path.name
        title = folder_name.replace('_', ' ').title()

        description_path = folder_path / 'description.txt'
        short_description_path = folder_path / 'short_description.txt'
        points_path = folder_path / 'points.txt'
        flag_path = folder_path / 'flag' / 'flag.txt'

        description = read_text_file(description_path) or f"Challenge: {title}"
        short_description = read_text_file(short_description_path) or description
        points_text = read_text_file(points_path)
        points = int(points_text) if points_text.isdigit() else 100
        flag = read_text_file(flag_path)

        challenge, _ = Challenge.objects.update_or_create(
            folder_name=folder_name,
            defaults={
                'title': title,
                'description': description,
                'short_description': short_description,
                'points': points,
                'flag': flag,
            }
        )

        hints_dir = folder_path / 'hints'
        if hints_dir.exists() and hints_dir.is_dir():
            for hint_file in sorted(hints_dir.glob('*.txt')):
                cost, hint_text = parse_hint_file(hint_file)
                if not hint_text:
                    continue

                ChallengeHint.objects.update_or_create(
                    challenge=challenge,
                    filename=hint_file.name,
                    defaults={
                        'hint': hint_text,
                        'cost': cost,
                    }
                )


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


@login_required
def mainhub(request):
    sync_storage_to_db()
    challenges = Challenge.objects.all().order_by('id')

    completions = ChallengeCompletion.objects.filter(
        user=request.user
    ).select_related('challenge')

    completed_map = {c.challenge_id: c.points_awarded for c in completions}

    challenge_cards = []
    for challenge in challenges:
        challenge_cards.append({
            'challenge': challenge,
            'completed': challenge.id in completed_map,
            'display_points': completed_map.get(challenge.id, challenge.points),
        })

    return render(request, 'mainhub.html', {
        'challenge_cards': challenge_cards,
    })


@login_required
def challenge_detail(request, folder_name):
    try:
        challenge = Challenge.objects.get(folder_name=folder_name)
    except Challenge.DoesNotExist:
        raise Http404("Challenge not found")

    files = []
    challenge_path = CHALLENGE_STORAGE / folder_name
    resources_dir = challenge_path / 'resources'

    if resources_dir.exists() and resources_dir.is_dir():
        for file_path in sorted(resources_dir.rglob('*')):
            if file_path.is_file():
                rel_path = file_path.relative_to(challenge_path)
                files.append({
                    'name': file_path.name,
                    'path': str(rel_path).replace('\\', '/'),
                    'size': file_path.stat().st_size,
                })

    used_hint_ids = set(
        ChallengeHintUse.objects.filter(
            user=request.user,
            challenge_hint__challenge=challenge,
            used=True
        ).values_list('challenge_hint_id', flat=True)
    )

    completed = ChallengeCompletion.objects.filter(
        user=request.user,
        challenge=challenge
    ).first()

    return render(request, 'challenge_detail.html', {
        'challenge': challenge,
        'description_text': challenge.description,
        'files': files,
        'hints': challenge.hints.all().order_by('id'),
        'used_hint_ids': used_hint_ids,
        'completed': completed,
    })


@login_required
def use_hint(request, hint_id):
    if request.method != 'POST':
        return JsonResponse({"message": "Invalid method."}, status=405)

    try:
        hint = ChallengeHint.objects.select_related('challenge').get(id=hint_id)
    except ChallengeHint.DoesNotExist:
        raise Http404("Hint not found")

    obj, created = ChallengeHintUse.objects.get_or_create(
        user=request.user,
        challenge_hint=hint,
        defaults={'used': True}
    )

    if not created and not obj.used:
        obj.used = True
        obj.save(update_fields=['used'])

    return JsonResponse({
        "success": True,
        "message": "Hint unlocked.",
        "hint": hint.hint,
        "cost": hint.cost,
        "hint_id": hint.id,
    })


@login_required
def submit_flag(request, folder_name):
    if request.method != 'POST':
        return JsonResponse({"message": "Invalid method."}, status=405)

    try:
        challenge = Challenge.objects.get(folder_name=folder_name)
    except Challenge.DoesNotExist:
        raise Http404("Challenge not found")

    submitted_flag = request.POST.get('flag', '').strip()
    real_flag = (challenge.flag or '').strip()

    if not real_flag:
        return JsonResponse({"message": "Flag not set for this challenge."}, status=404)

    if submitted_flag != real_flag:
        return JsonResponse({"message": "Wrong flag.", "success": False})

    used_cost = ChallengeHintUse.objects.filter(
        user=request.user,
        challenge_hint__challenge=challenge,
        used=True
    ).aggregate(total=Sum('challenge_hint__cost'))['total'] or 0

    final_points = max(challenge.points - used_cost, 0)

    completion, created = ChallengeCompletion.objects.get_or_create(
        user=request.user,
        challenge=challenge,
        defaults={'points_awarded': final_points}
    )

    if not created and completion.points_awarded != final_points:
        completion.points_awarded = final_points
        completion.save(update_fields=['points_awarded'])

    return JsonResponse({
        "message": "Correct flag!",
        "success": True,
        "completed": True,
        "points_awarded": final_points,
        "already_completed": not created,
    })


@login_required
def download_file(request, folder_name, file_path):
    try:
        Challenge.objects.get(folder_name=folder_name)
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
