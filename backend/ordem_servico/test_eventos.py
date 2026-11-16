import pytest
from django.core import mail

from notificacao.canais import CanalComposto, CanalEmail, CanalNotificacao, CanalSistema, Mensagem
from notificacao.models import Notificacao
from ordem_servico.eventos import Observador, PublicadorEventos, ServicoReprovado, TecnicoAtribuido, TecnicoReatribuido
from ordem_servico.fachada import OrdemServicoFacade
from ordem_servico.observadores import (
    AlertarGestorReprovacaoObserver,
    NotificarNovoTecnicoObserver,
    NotificarTecnicoAnteriorObserver,
    criar_publicador_padrao,
)
from utils.apoio_testes import criar_localizacao, criar_os, criar_usuario


class ObservadorEspiao(Observador):
    def __init__(self):
        self.recebidos = []

    def atualizar(self, evento):
        self.recebidos.append(evento)


class ObservadorQuebrado(Observador):
    def atualizar(self, evento):
        raise RuntimeError("falha simulada")


class CanalEspiao(CanalNotificacao):
    def __init__(self, retorno=None):
        self.mensagens = []
        self.retorno = retorno

    def enviar(self, mensagem):
        self.mensagens.append(mensagem)
        return self.retorno


def _evento():
    return TecnicoAtribuido(ordem_servico=None, responsavel=None, tecnico=None)


@pytest.mark.django_db
def test_publicador_entrega_so_aos_inscritos_no_tipo_do_evento():
    atribuicao, reprovacao = ObservadorEspiao(), ObservadorEspiao()
    publicador = PublicadorEventos().inscrever(TecnicoAtribuido, atribuicao).inscrever(ServicoReprovado, reprovacao)

    publicador.publicar(_evento())

    assert len(atribuicao.recebidos) == 1 and reprovacao.recebidos == []


def test_inscricao_duplicada_e_cancelamento():
    espiao = ObservadorEspiao()
    publicador = PublicadorEventos().inscrever(TecnicoAtribuido, espiao).inscrever(TecnicoAtribuido, espiao)
    assert publicador.observadores_de(TecnicoAtribuido) == (espiao,)

    publicador.cancelar_inscricao(TecnicoAtribuido, espiao)
    publicador.publicar(_evento())

    assert espiao.recebidos == []


@pytest.mark.django_db
def test_falha_de_um_observador_nao_impede_os_demais():
    espiao = ObservadorEspiao()
    publicador = PublicadorEventos().inscrever(TecnicoAtribuido, ObservadorQuebrado()).inscrever(TecnicoAtribuido, espiao)

    publicador.publicar(_evento())

    assert len(espiao.recebidos) == 1


def test_publicador_padrao_registra_os_observadores_de_cada_evento():
    publicador = criar_publicador_padrao()

    assert [type(o) for o in publicador.observadores_de(TecnicoAtribuido)] == [NotificarNovoTecnicoObserver]
    assert [type(o) for o in publicador.observadores_de(TecnicoReatribuido)] == [NotificarNovoTecnicoObserver, NotificarTecnicoAnteriorObserver]
    assert [type(o) for o in publicador.observadores_de(ServicoReprovado)] == [AlertarGestorReprovacaoObserver]


@pytest.mark.django_db
def test_fachada_publica_evento_de_atribuicao_no_publicador_injetado():
    localizacao = criar_localizacao()
    gerente = criar_usuario("Gerente Obs", "gerente.obs@fho.edu.br", "GERENTE")
    tecnico = criar_usuario("Tec Obs", "tec.obs@fho.edu.br", "TECNICO")
    ordem_servico = criar_os(localizacao, status_ordem_servico="APROVADA", descricao_servico="Lâmpada queimada no corredor.")
    espiao = ObservadorEspiao()

    OrdemServicoFacade(publicador=PublicadorEventos().inscrever(TecnicoAtribuido, espiao)).atribuir_tecnico(ordem_servico, tecnico, gerente)

    evento = espiao.recebidos[0]
    assert (evento.ordem_servico.pk, evento.tecnico, evento.responsavel) == (ordem_servico.pk, tecnico, gerente)
    assert not Notificacao.objects.exists()


def test_canal_composto_envia_por_todos_e_devolve_o_primeiro_resultado():
    primeiro, segundo = CanalEspiao(retorno="registro"), CanalEspiao(retorno="ignorado")
    mensagem = Mensagem(destinatario=None, tipo="T", titulo="Título", texto="Texto")

    assert CanalComposto([primeiro]).adicionar(segundo).enviar(mensagem) == "registro"
    assert primeiro.mensagens == [mensagem] and segundo.mensagens == [mensagem]


def test_canal_email_adapta_o_envio_do_django(settings):
    settings.FRONTEND_URL = "http://techorder.local"
    enviados = []
    canal = CanalEmail(enviar_email=lambda *args, **kwargs: enviados.append(args), agendar=lambda funcao: funcao())
    destinatario = type("Usuario", (), {"email": "ana@fho.edu.br"})()

    canal.enviar(Mensagem(destinatario=destinatario, tipo="T", titulo="OS #1", texto="Corpo"))
    canal.enviar(Mensagem(destinatario=type("SemEmail", (), {"email": ""})(), tipo="T", titulo="x", texto="y"))

    assert enviados == [("OS #1 - TechOrder", "Corpo\n\nAcompanhe pelo sistema: http://techorder.local", None, ["ana@fho.edu.br"])]


@pytest.mark.django_db
def test_canal_sistema_mais_email_grava_notificacao_e_envia_email(django_capture_on_commit_callbacks):
    usuario = criar_usuario("Ana Canal", "ana.canal@fho.edu.br", "TECNICO")

    with django_capture_on_commit_callbacks(execute=True):
        registro = CanalComposto([CanalSistema(), CanalEmail()]).enviar(Mensagem(destinatario=usuario, tipo="OS_ATRIBUIDA", titulo="OS #9", texto="Olá"))

    assert isinstance(registro, Notificacao) and registro.usuario_id == usuario.pk
    assert [m.to for m in mail.outbox] == [["ana.canal@fho.edu.br"]]
