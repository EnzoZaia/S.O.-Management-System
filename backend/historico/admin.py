from django.contrib import admin
from historico.models import Historico
# Register your models here.

class HistoricoAdmin(admin.ModelAdmin):
    list_display = ('id_historico_ordem_servico', 'usuario', 'ordem_servico', 'data_registro')
    search_fields = ('desc_historico', 'usuario__nome', 'usuario__email', 'ordem_servico__descricao_servico')
    list_filter = ('data_registro',)

admin.site.register(Historico, HistoricoAdmin)