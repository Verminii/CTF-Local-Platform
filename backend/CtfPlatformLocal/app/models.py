from django.db import models

# Create your models here.

class ToDoItem(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)

class Challenge(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    folder_name = models.CharField(max_length=100, unique=True)  # Name of the folder in storage/
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


    