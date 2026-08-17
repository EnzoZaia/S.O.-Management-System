from django.contrib import admin
from localizacao.models import Localizacao
# Register your models here.

class LocalizacaoAdmin(admin.ModelAdmin):
    list_display = ('id_localizacao', 'desc_localizacao', 'predio')
    search_fields = ('desc_localizacao', 'predio_nome_predio')
    list_filter = ('predio',)

admin.site.register(Localizacao, LocalizacaoAdmin)