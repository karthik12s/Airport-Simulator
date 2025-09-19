from django.contrib import admin
from . import models

# Register your models here

for  i in models.models_list:
    admin.site.register(i)