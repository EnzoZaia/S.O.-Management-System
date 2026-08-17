from django.contrib import admin
from ordem_servico.models import OrdemServico
# Register your models here.

class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ('id_ordem_servico', 'localizacao', 'prioridade_urgencia', 'status_ordem_servico', 'dt_abertura', 'dt_conclusao')
    search_fields = ('descricao_servico', 'localizacao__desc_localizacao')
    list_filter = ('prioridade_urgencia', 'status_ordem_servico', 'dt_abertura')

admin.site.register(OrdemServico, OrdemServicoAdmin)