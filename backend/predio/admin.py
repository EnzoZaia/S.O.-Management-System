from django.contrib import admin
from predio.models import Predio
# Register your models here.

class PredioAdmin(admin.ModelAdmin):
    list_display = ('id_predio', 'nome_predio')
    search_fields = ('nome_predio',)

admin.site.register(Predio, PredioAdmin)