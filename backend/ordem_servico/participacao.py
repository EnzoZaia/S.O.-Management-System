from ordem_servico.constantes import STATUS_ATIVOS, TIPO_CORRETIVA, status_para_api
from ordem_servico.models import OrdemServico

TAMANHO_DESCRICAO_RESUMIDA = 120


def corretiva_ativa_do_ativo(ativo):
    if ativo is None:
        return None
    return (
        OrdemServico.objects.com_total_afetados()
        .select_related('localizacao__predio', 'ativo')
        .filter(ativo=ativo, tipo_manutencao=TIPO_CORRETIVA, status_ordem_servico__in=STATUS_ATIVOS)
        .order_by('dt_abertura', 'id_ordem_servico')
        .first()
    )


def os_esta_ativa(ordem_servico):
    return ordem_servico.status_ordem_servico in STATUS_ATIVOS


def usuario_ja_vinculado(ordem_servico, usuario):
    if usuario is None or not getattr(usuario, 'is_authenticated', False):
        return False
    from utils.permissions import usuario_participa_da_os

    return usuario_participa_da_os(usuario, ordem_servico)


def resumo_publico(ordem_servico):
    descricao = ordem_servico.descricao_servico or ''
    if len(descricao) > TAMANHO_DESCRICAO_RESUMIDA:
        descricao = descricao[:TAMANHO_DESCRICAO_RESUMIDA - 3].rstrip() + '...'
    localizacao = ordem_servico.localizacao
    return {
        'id_ordem_servico': ordem_servico.id_ordem_servico,
        'status_ordem_servico': status_para_api(ordem_servico.status_ordem_servico),
        'dt_abertura': ordem_servico.dt_abertura,
        'predio_nome': localizacao.predio.nome_predio if localizacao and localizacao.predio_id else None,
        'localizacao_nome': localizacao.desc_localizacao if localizacao else None,
        'ativo_patrimonio': ordem_servico.ativo.codigo_patrimonial if ordem_servico.ativo_id else None,
        'descricao_resumida': descricao,
        'total_afetados': ordem_servico.total_afetados,
    }


def situacao_participacao(ordem_servico, usuario):
    ja_vinculado = usuario_ja_vinculado(ordem_servico, usuario)
    autenticado = usuario is not None and getattr(usuario, 'is_authenticated', False)
    return {
        'ordem_existente': resumo_publico(ordem_servico),
        'pode_presenciar': bool(autenticado and not ja_vinculado and os_esta_ativa(ordem_servico)),
        'ja_vinculado': ja_vinculado,
    }
