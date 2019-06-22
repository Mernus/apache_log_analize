from django.contrib import admin
from .models import Logfile, Logdata

admin.site.register(Logdata)
admin.site.register(Logfile)
# Register your models here.
