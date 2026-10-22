from collections import OrderedDict

from django.utils import timezone
from fpdf import FPDF

from preventiva_grupo.catalogo import catalogo_do_tipo
from preventiva_grupo.models import OrdemServicoAtivo, PlanoAcaoRecurso

ROTULO_TIPO = {'AR_CONDICIONADO': 'Ar-condicionado', 'BEBEDOURO': 'Bebedouro'}


def _texto(valor):
    return str(valor if valor is not None else '').encode('latin-1', 'replace').decode('latin-1')


def _formatar_quantidade(valor):
    return f"{valor:g}".replace('.', ',')


def recursos_do_plano(id_predio, tipo_ativo):
    recursos = list(
        PlanoAcaoRecurso.objects.filter(
            plano_acao__plano_manutencao__predio_id=id_predio,
            plano_acao__plano_manutencao__tipo_ativo=tipo_ativo,
            plano_acao__plano_manutencao__ativo_no_sistema=True,
        ).select_related('recurso')
    )
    if not recursos:
        return None
    return {
        'materiais': [(r.recurso.nome, float(r.quantidade), r.recurso.unidade_medida) for r in recursos if r.recurso.tipo == 'MATERIAL'],
        'ferramentas': [r.recurso.nome for r in recursos if r.recurso.tipo == 'FERRAMENTA'],
        'epis': [r.recurso.nome for r in recursos if r.recurso.tipo == 'EPI'],
    }


def consolidar_recursos(itens):
    materiais = OrderedDict()
    ferramentas = OrderedDict()
    epis = OrderedDict()
    planos = {}
    for item in itens:
        chave_plano = (item.ativo.localizacao.predio_id, item.ativo.tipo_ativo)
        if chave_plano not in planos:
            planos[chave_plano] = recursos_do_plano(*chave_plano)
        catalogo = planos[chave_plano] or catalogo_do_tipo(item.ativo.tipo_ativo)
        for descricao, quantidade, unidade in catalogo['materiais']:
            chave = (descricao, unidade)
            materiais[chave] = materiais.get(chave, 0) + quantidade
        for ferramenta in catalogo['ferramentas']:
            ferramentas[ferramenta] = True
        for epi in catalogo['epis']:
            epis[epi] = True
    return (
        [{'descricao': descricao, 'quantidade': quantidade, 'unidade': unidade} for (descricao, unidade), quantidade in materiais.items()],
        list(ferramentas),
        list(epis),
    )


def gerar_guia_pdf(ordem_servico):
    itens = list(
        OrdemServicoAtivo.objects.filter(ordem_servico=ordem_servico)
        .select_related('ativo__localizacao__predio')
        .order_by('id_ordem_servico_ativo')
    )
    materiais, ferramentas, epis = consolidar_recursos(itens)
    predio = itens[0].ativo.localizacao.predio.nome_predio if itens else '-'

    pdf = FPDF(format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    largura = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(largura, 10, _texto(f'Guia de preventiva - OS #{ordem_servico.pk}'), new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(largura, 6, _texto(f'Prédio: {predio}'), new_x='LMARGIN', new_y='NEXT')
    pdf.cell(largura, 6, _texto(f'Técnico responsável: {ordem_servico.tecnico_nome or "-"}'), new_x='LMARGIN', new_y='NEXT')
    pdf.cell(largura, 6, _texto(f'Emitido em: {timezone.localtime().strftime("%d/%m/%Y %H:%M")}'), new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    def titulo(texto):
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(largura, 8, _texto(texto), new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 10)

    def linha(texto):
        pdf.multi_cell(largura, 6, _texto(texto), new_x='LMARGIN', new_y='NEXT')

    titulo(f'Ativos ({len(itens)})')
    for item in itens:
        ativo = item.ativo
        linha(
            f'- {ativo.codigo_patrimonial} | {ROTULO_TIPO.get(ativo.tipo_ativo, ativo.tipo_ativo)} | '
            f'{(ativo.marca or "")} {(ativo.modelo or "")} | Local: {ativo.localizacao.desc_localizacao}'
        )
    pdf.ln(2)

    titulo('Materiais consolidados')
    if materiais:
        for material in materiais:
            linha(f'- {material["descricao"]}: {_formatar_quantidade(material["quantidade"])} {material["unidade"]}')
    else:
        linha('- Nenhum material previsto.')
    pdf.ln(2)

    titulo('Ferramentas')
    for ferramenta in ferramentas or ['Nenhuma ferramenta específica.']:
        linha(f'- {ferramenta}')
    pdf.ln(2)

    titulo('EPIs obrigatórios')
    for epi in epis or ['Nenhum EPI específico.']:
        linha(f'- {epi}')
    pdf.ln(2)

    titulo('Checklists por tipo de ativo')
    for tipo in OrderedDict((item.ativo.tipo_ativo, True) for item in itens):
        pdf.set_font('Helvetica', 'B', 10)
        linha(ROTULO_TIPO.get(tipo, tipo))
        pdf.set_font('Helvetica', '', 10)
        for codigo, descricao in catalogo_do_tipo(tipo)['itens']:
            linha(f'[  ] {codigo}. {descricao}')
        pdf.ln(1)

    return bytes(pdf.output())
