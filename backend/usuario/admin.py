from django.contrib import admin
from usuario.models import Usuario

class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'nome', 'email')
    search_fields = ('nome', 'email')

admin.site.register(Usuario, UsuarioAdmin)
