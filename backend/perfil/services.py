import secrets

from django.db import transaction

from perfil.models import TIPO_VINCULO_FUNCIONARIO, Gerente, Gestor, Solicitante, Tecnico

GERENTE = 'GERENTE'
GESTOR = 'GESTOR'
TECNICO = 'TECNICO'
SOLICITANTE = 'SOLICITANTE'

PERFIS = (GERENTE, GESTOR, TECNICO, SOLICITANTE)

ID_POR_PERFIL = {GERENTE: 1, GESTOR: 2, TECNICO: 3, SOLICITANTE: 4}
PERFIL_POR_ID = {id_perfil: nome for nome, id_perfil in ID_POR_PERFIL.items()}

MODELO_POR_PERFIL = {GERENTE: Gerente, GESTOR: Gestor, TECNICO: Tecnico, SOLICITANTE: Solicitante}
RELACAO_POR_PERFIL = {GERENTE: 'perfil_gerente', GESTOR: 'perfil_gestor', TECNICO: 'perfil_tecnico', SOLICITANTE: 'perfil_solicitante'}

AREA_ATUACAO_PADRAO = 'GERAIS'

_TENTATIVAS_GERAR_IDENTIFICADOR = 20


class PerfilError(Exception):
    def __init__(self, mensagem, status_code=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status_code = status_code


def lista_perfis():
    return [{'id_grupo': ID_POR_PERFIL[nome], 'desc_grupo': nome} for nome in PERFIS]


def usuario_tem_perfil(usuario, nome_perfil):
    if not usuario or not getattr(usuario, 'is_authenticated', False) or not usuario.pk:
        return False
    modelo = MODELO_POR_PERFIL.get(nome_perfil)
    if modelo is None:
        return False
    relacao = RELACAO_POR_PERFIL[nome_perfil]
    if relacao in usuario._state.fields_cache:
        return usuario._state.fields_cache[relacao] is not None
    return modelo.objects.filter(usuario_id=usuario.pk).exists()


def perfis_do_usuario(usuario):
    if not usuario or not usuario.pk:
        return []
    return [nome for nome in PERFIS if usuario_tem_perfil(usuario, nome)]


def perfil_principal(usuario):
    perfis = perfis_do_usuario(usuario)
    return perfis[0] if perfis else None


def _identificador_em_uso(identificador):
    return Solicitante.objects.filter(identificador_vinculo=identificador).exists()


def gerar_identificador_unico():
    for _ in range(_TENTATIVAS_GERAR_IDENTIFICADOR):
        candidato = gerar_identificador_candidato()
        if not _identificador_em_uso(candidato):
            return candidato
    raise PerfilError("Não foi possível gerar o RA agora. Tente novamente.", 503)


def gerar_identificador_candidato():
    return str(secrets.randbelow(900000) + 100000)


def _referencias_que_impedem_remocao(usuario, nome_perfil):
    from historico.models import Historico
    from ordem_servico.models import OrdemServico

    if nome_perfil == TECNICO and Historico.objects.filter(tecnico_id=usuario.pk).exists():
        return "o técnico já tem atribuições no histórico de ordens de serviço"
    if nome_perfil == SOLICITANTE and OrdemServico.objects.filter(solicitante_id=usuario.pk).exists():
        return "o solicitante já tem ordens de serviço abertas"
    return None


def _remover_perfil(usuario, nome_perfil):
    if nome_perfil == GESTOR:
        Tecnico.objects.filter(gestor_id=usuario.pk).update(gestor=None)
    MODELO_POR_PERFIL[nome_perfil].objects.filter(usuario_id=usuario.pk).delete()


def criar_perfil(usuario, nome_perfil, tipo_vinculo=TIPO_VINCULO_FUNCIONARIO, identificador=None):
    if nome_perfil == GERENTE:
        return Gerente.objects.get_or_create(usuario=usuario)[0]
    if nome_perfil == GESTOR:
        return Gestor.objects.get_or_create(usuario=usuario, defaults={'area_atuacao': AREA_ATUACAO_PADRAO})[0]
    if nome_perfil == TECNICO:
        return Tecnico.objects.get_or_create(usuario=usuario, defaults={'area_atuacao': AREA_ATUACAO_PADRAO})[0]
    if nome_perfil == SOLICITANTE:
        existente = Solicitante.objects.filter(usuario=usuario).first()
        if existente:
            return existente
        return Solicitante.objects.create(
            usuario=usuario,
            tipo_vinculo=tipo_vinculo,
            identificador_vinculo=identificador or gerar_identificador_unico(),
        )
    raise PerfilError("Perfil inválido.")


@transaction.atomic
def definir_perfil(usuario, nome_perfil):
    if nome_perfil not in PERFIS:
        raise PerfilError("Perfil inválido.")

    posicao_alvo = PERFIS.index(nome_perfil)

    for outro in PERFIS:
        if outro == nome_perfil or not usuario_tem_perfil(usuario, outro):
            continue
        impedimento = _referencias_que_impedem_remocao(usuario, outro)
        if impedimento is None:
            _remover_perfil(usuario, outro)
        elif PERFIS.index(outro) < posicao_alvo:
            raise PerfilError(f"Não é possível remover o perfil {outro}: {impedimento}.")

    criar_perfil(usuario, nome_perfil)
    for relacao in RELACAO_POR_PERFIL.values():
        usuario._state.fields_cache.pop(relacao, None)
