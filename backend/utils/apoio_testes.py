from django.utils import timezone

from localizacao.models import Localizacao
from ordem_servico.constantes import EM_TRIAGEM, PRIORIDADE_NORMAL, TIPO_CORRETIVA
from ordem_servico.models import OrdemServico
from perfil.services import definir_perfil
from predio.models import Predio
from usuario.models import STATUS_CONTA_ATIVA, Usuario
from utils.historico import registrar_atribuicao


def criar_usuario(nome, email, perfil=None, **extra):
    campos = {"senha_hash": "x", "email_confirmado": True, "status_conta": STATUS_CONTA_ATIVA}
    campos.update(extra)
    usuario = Usuario.objects.create(nome=nome, email=email, **campos)
    if perfil:
        definir_perfil(usuario, perfil)
    return usuario


def criar_localizacao(nome_predio="Bloco A", nome_sala="Sala 101"):
    predio = Predio.objects.create(nome_predio=nome_predio)
    return Localizacao.objects.create(predio=predio, desc_localizacao=nome_sala)


def atribuir(ordem_servico, tecnico, gestor=None):
    if gestor is None:
        gestor = tecnico
    registrar_atribuicao(ordem_servico, gestor, tecnico)
    for atributo in ("tecnico_atual_id", "tecnico_atual_nome", "gestor_atual_id", "gestor_atual_nome"):
        ordem_servico.__dict__.pop(atributo, None)
    return ordem_servico


def criar_os(localizacao, tecnico=None, gestor=None, **campos):
    valores = {
        "tipo_manutencao": TIPO_CORRETIVA,
        "prioridade_urgencia": PRIORIDADE_NORMAL,
        "status_ordem_servico": EM_TRIAGEM,
        "dt_abertura": timezone.now(),
        "descricao_servico": "OS de teste.",
    }
    valores.update(campos)
    ordem_servico = OrdemServico.objects.create(localizacao=localizacao, **valores)
    if tecnico is not None:
        atribuir(ordem_servico, tecnico, gestor)
    return ordem_servico
