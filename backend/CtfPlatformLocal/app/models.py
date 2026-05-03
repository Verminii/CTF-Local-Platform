from django.db import models
from django.conf import settings


class ToDoItem(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Challenge(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    short_description = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=100)
    folder_name = models.CharField(max_length=100, unique=True)
    flag = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class ChallengeHint(models.Model):
    challenge = models.ForeignKey('Challenge', on_delete=models.CASCADE, related_name='hints')
    filename = models.CharField(max_length=100)
    hint = models.TextField()
    cost = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.challenge.title} - {self.filename}"


class ChallengeHintUse(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hint_uses')
    challenge_hint = models.ForeignKey(ChallengeHint, on_delete=models.CASCADE, related_name='uses')
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'challenge_hint')

    def __str__(self):
        return f"{self.user.username} - {self.challenge_hint.filename}"


class ChallengeCompletion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='challenge_completions')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)
    points_awarded = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'challenge')

    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"
