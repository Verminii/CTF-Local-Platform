from django.contrib import admin
from .models import Challenge
from .models import ToDoItem

# Register your models here.

admin.site.register(Challenge)
admin.site.register(ToDoItem)
