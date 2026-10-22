import pytest
from django.core import mail
from rest_framework.test import APIClient

from historico.models import Historico
from notificacao.models import Notificacao
from perfil.models import Gestor, Tecnico
from utils.apoio_testes import atribuir, criar_localizacao, criar_os, criar_usuario


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


def _atribuir(usuario, ordem_servico, corpo):
    return _cliente(usuario).patch(f"/ordem-servico/{ordem_servico.pk}/atribuir-tecnico/", corpo, format="json")


@pytest.fixture
def cenario(db):
    gestor = criar_usuario("Gestor", "gestor.atr@fho.edu.br", "GESTOR")
    ana = criar_usuario("Ana", "ana.atr@fho.edu.br", "TECNICO")
    bia = criar_usuario("Bia", "bia.atr@fho.edu.br", "TECNICO")
    Tecnico.objects.filter(usuario__in=[ana, bia]).update(gestor=Gestor.objects.get(usuario=gestor))
    return {"localizacao": criar_localizacao(), "gestor": gestor, "ana": ana, "bia": bia}


def test_atribuicao_notifica_tecnico_e_aprova_a_os(cenario, django_capture_on_commit_callbacks):
    ordem_servico = criar_os(cenario["localizacao"])

    with django_capture_on_commit_callbacks(execute=True):
        resposta = _atribuir(cenario["gestor"], ordem_servico, {"tecnico": cenario["ana"].pk})

    assert resposta.status_code == 200
    ordem_servico.refresh_from_db()
    assert ordem_servico.status_ordem_servico == "APROVADA"
    notificacao = Notificacao.objects.get(usuario=cenario["ana"])
    assert notificacao.tipo == "OS_ATRIBUIDA" and notificacao.ordem_servico_id == ordem_servico.pk
    assert [m.to for m in mail.outbox] == [["ana.atr@fho.edu.br"]]


def test_gestor_atribui_os_aprovada_na_triagem_sem_tecnico(cenario):
    ordem_servico = criar_os(cenario["localizacao"], status_ordem_servico="APROVADA")

    resposta = _atribuir(cenario["gestor"], ordem_servico, {"tecnico": cenario["ana"].pk})

    assert resposta.status_code == 200
    assert Historico.objects.filter(ordem_servico=ordem_servico, tipo_evento="ATRIBUICAO", tecnico_id=cenario["ana"].pk).exists()


def test_reatribuicao_exige_justificativa_preserva_anterior_e_notifica_os_dois(cenario, django_capture_on_commit_callbacks):
    ordem_servico = criar_os(cenario["localizacao"], status_ordem_servico="EM_EXECUCAO")
    atribuir(ordem_servico, cenario["ana"], cenario["gestor"])

    sem_justificativa = _atribuir(cenario["gestor"], ordem_servico, {"tecnico": cenario["bia"].pk})
    assert sem_justificativa.status_code == 400
    assert "justificativa" in sem_justificativa.data["erros"]

    with django_capture_on_commit_callbacks(execute=True):
        resposta = _atribuir(cenario["gestor"], ordem_servico, {"tecnico": cenario["bia"].pk, "justificativa": "Ana foi deslocada para outro prédio."})

    assert resposta.status_code == 200
    atribuicoes = list(Historico.objects.filter(ordem_servico=ordem_servico, tipo_evento="ATRIBUICAO").order_by("id_historico_ordem_servico"))
    assert [a.tecnico_id for a in atribuicoes] == [cenario["ana"].pk, cenario["bia"].pk]
    assert atribuicoes[-1].desc_historico == "Técnico reatribuído: Ana -> Bia. Justificativa: Ana foi deslocada para outro prédio."
    ordem_servico.refresh_from_db()
    assert ordem_servico.status_ordem_servico == "EM_EXECUCAO"
    assert set(Notificacao.objects.values_list("usuario_id", "tipo")) == {(cenario["bia"].pk, "OS_ATRIBUIDA"), (cenario["ana"].pk, "OS_REATRIBUIDA")}
    assert sorted(m.to[0] for m in mail.outbox) == ["ana.atr@fho.edu.br", "bia.atr@fho.edu.br"]


def test_mesmo_tecnico_inativo_ou_fora_da_equipe_sao_recusados(cenario):
    ordem_servico = criar_os(cenario["localizacao"])
    atribuir(ordem_servico, cenario["ana"], cenario["gestor"])
    assert _atribuir(cenario["gestor"], ordem_servico, {"tecnico": cenario["ana"].pk}).status_code == 400

    inativo = criar_usuario("Caio", "caio.atr@fho.edu.br", "TECNICO", status_conta="DESATIVADA")
    resposta_inativo = _atribuir(cenario["gestor"], ordem_servico, {"tecnico": inativo.pk, "justificativa": "Tentativa com técnico inativo."})
    assert resposta_inativo.status_code == 400
    assert "ativo" in resposta_inativo.data["mensagem"]

    outro_gestor = criar_usuario("Outro Gestor", "outro.gestor@fho.edu.br", "GESTOR")
    de_outra_equipe = criar_usuario("Davi", "davi.atr@fho.edu.br", "TECNICO")
    Tecnico.objects.filter(usuario=de_outra_equipe).update(gestor=Gestor.objects.get(usuario=outro_gestor))
    resposta_equipe = _atribuir(cenario["gestor"], ordem_servico, {"tecnico": de_outra_equipe.pk, "justificativa": "Tentativa com técnico de outra equipe."})
    assert resposta_equipe.status_code == 400
    assert "equipe" in resposta_equipe.data["mensagem"]


def test_area_do_tecnico_precisa_atender_a_categoria(cenario):
    Tecnico.objects.filter(usuario=cenario["ana"]).update(area_atuacao="ELETRICA")
    ordem_servico = criar_os(cenario["localizacao"], categoria_manutencao="REFRIGERACAO")

    resposta = _atribuir(cenario["gestor"], ordem_servico, {"tecnico": cenario["ana"].pk})

    assert resposta.status_code == 400
    assert "área" in resposta.data["mensagem"]


def test_gerente_atribui_qualquer_tecnico_ativo_e_os_finalizada_recusa(cenario):
    gerente = criar_usuario("Gerente", "gerente.atr@fho.edu.br", "GERENTE")
    avulso = criar_usuario("Edu", "edu.atr@fho.edu.br", "TECNICO")
    Tecnico.objects.filter(usuario=avulso).update(gestor=Gestor.objects.create(usuario=criar_usuario("G2", "g2.atr@fho.edu.br"), area_atuacao="TODAS"))

    assert _atribuir(gerente, criar_os(cenario["localizacao"]), {"tecnico": avulso.pk}).status_code == 200

    encerrada = criar_os(cenario["localizacao"], status_ordem_servico="ENCERRADA")
    resposta = _atribuir(gerente, encerrada, {"tecnico": avulso.pk})
    assert resposta.status_code == 400
    assert "status" in resposta.data["mensagem"]


def test_gestor_lista_apenas_tecnicos_da_equipe_em_usuario(cenario):
    outro_gestor = criar_usuario("Outro", "outro2.gestor@fho.edu.br", "GESTOR")
    fora = criar_usuario("Fora", "fora.atr@fho.edu.br", "TECNICO")
    Tecnico.objects.filter(usuario=fora).update(gestor=Gestor.objects.get(usuario=outro_gestor))

    nomes = {u["nome"] for u in _cliente(cenario["gestor"]).get("/usuario/").data}

    assert nomes == {"Ana", "Bia"}


def test_endpoint_de_notificacoes_do_usuario(cenario):
    ordem_servico = criar_os(cenario["localizacao"])
    _atribuir(cenario["gestor"], ordem_servico, {"tecnico": cenario["ana"].pk})
    client = _cliente(cenario["ana"])

    lista = client.get("/notificacao/").data["dados"]
    assert lista["nao_lidas"] == 1
    id_notificacao = lista["notificacoes"][0]["id_notificacao"]

    assert _cliente(cenario["bia"]).patch(f"/notificacao/{id_notificacao}/lida/").status_code == 404
    assert client.patch(f"/notificacao/{id_notificacao}/lida/").data["dados"]["lida"] is True
    assert client.get("/notificacao/?nao_lidas=true").data["dados"]["notificacoes"] == []
