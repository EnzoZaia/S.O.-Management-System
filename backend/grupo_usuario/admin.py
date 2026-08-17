from django.contrib import admin
from .models import GrupoUsuario

class GrupoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'grupo')
    search_fields = ('usuario__nome', 'usuario__email', 'grupo__desc_grupo')
    list_filter = ('grupo',)

admin.site.register(GrupoUsuario, GrupoUsuarioAdmin)