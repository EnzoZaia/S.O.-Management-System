from django.contrib import admin
from grupo.models import Grupo
# Register your models here.

class GrupoAdmin(admin.ModelAdmin):
    list_display = ('id_grupo', 'desc_grupo', 'desc_permissao')
    search_fields = ('desc_grupo', 'desc_permissao')

admin.site.register(Grupo, GrupoAdmin)