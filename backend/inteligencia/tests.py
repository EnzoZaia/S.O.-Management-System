import base64
import json

import pytest
from rest_framework.test import APIClient

from ativo.models import Ativo
from inteligencia.cliente import ClienteIA, FalhaTransporte, IAIndisponivelError
from os_participante.models import OsParticipante
from utils.apoio_testes import criar_localizacao, criar_os, criar_usuario


class TransporteFalso:
    def __init__(self, texto="1. Desligue o disjuntor.\n2. Limpe o filtro.", erro=None, finish="STOP"):
        self.chamadas = []
        self.erro = erro
        self.texto = texto
        self.finish = finish

    def __call__(self, url, cabecalhos, corpo, timeout):
        self.chamadas.append({"url": url, "cabecalhos": cabecalhos, "corpo": corpo, "timeout": timeout})
        if self.erro is not None:
            raise self.erro
        return {"candidates": [{"finishReason": self.finish, "content": {"parts": [{"text": self.texto}]}}]}


def _partes(chamada):
    return chamada["corpo"]["contents"][0]["parts"]


def _texto(chamada):
    return "\n".join(parte.get("text", "") for parte in _partes(chamada))


def _sistema(chamada):
    return chamada["corpo"]["system_instruction"]["parts"][0]["text"]


@pytest.fixture
def ia(settings, monkeypatch):
    settings.IA_PROVEDOR = "gemini"
    settings.GEMINI_API_KEY = "chave-de-teste"
    settings.GEMINI_MODEL = "gemini-flash-latest"
    settings.IA_MAX_RETRIES = 2
    falso = TransporteFalso()
    cliente = ClienteIA(transporte=falso)
    monkeypatch.setattr(ClienteIA, "instancia", classmethod(lambda cls: cliente))
    return falso


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


@pytest.fixture
def os_corretiva(db):
    localizacao = criar_localizacao()
    ativo = Ativo.objects.create(localizacao=localizacao, codigo_patrimonial="PAT-IA", tipo_ativo="AR_CONDICIONADO", marca="Springer", modelo="Xtreme", periodicidade_preventiva_dias=30)
    tecnico = criar_usuario("Tec", "tec.ia@fho.edu.br", "TECNICO")
    solicitante = criar_usuario("Maria Sigilosa", "maria.sigilosa@fho.edu.br", "SOLICITANTE")
    ordem_servico = criar_os(localizacao, ativo=ativo, tecnico=tecnico, solicitante=solicitante, status_ordem_servico="EM_EXECUCAO", descricao_servico="Ar pingando água na sala.")
    return {"os": ordem_servico, "tecnico": tecnico, "solicitante": solicitante}


def _url(os_corretiva):
    return f"/ordem-servico/{os_corretiva['os'].pk}/assistente/"


def test_tecnico_atribuido_consulta_com_contexto_do_ativo_e_aviso_de_falta_de_manual(ia, os_corretiva):
    resposta = _cliente(os_corretiva["tecnico"]).post(_url(os_corretiva), {"pergunta": "Como limpar o dreno entupido?"}, format="json")

    assert resposta.status_code == 200
    dados = resposta.data["dados"]
    assert dados["resposta"].startswith("1. Desligue")
    assert dados["base_conhecimento"]["possui_manual"] is False
    assert "Não há manual" in dados["aviso"]
    chamada = ia.chamadas[0]
    assert "models/gemini-flash-latest:generateContent" in chamada["url"]
    assert chamada["cabecalhos"]["x-goog-api-key"] == "chave-de-teste"
    conteudo = _texto(chamada)
    assert "Springer" in conteudo and "Xtreme" in conteudo and "Como limpar o dreno" in conteudo
    assert "não há base de conhecimento" in _sistema(chamada).lower()


@pytest.mark.parametrize("ator", ["solicitante", "outro_tecnico"])
def test_somente_o_tecnico_atribuido_pode_consultar(ia, os_corretiva, ator):
    usuario = os_corretiva.get(ator) or criar_usuario("Outro", "outro.ia@fho.edu.br", "TECNICO")

    resposta = _cliente(usuario).post(_url(os_corretiva), {"pergunta": "Como limpar o dreno entupido?"}, format="json")

    assert resposta.status_code == 403
    assert ia.chamadas == []


def test_preventiva_e_pergunta_invalida(ia, os_corretiva):
    os_corretiva["os"].tipo_manutencao = "PREVENTIVA"
    os_corretiva["os"].save()
    assert _cliente(os_corretiva["tecnico"]).post(_url(os_corretiva), {"pergunta": "Pergunta válida aqui?"}, format="json").status_code == 400

    os_corretiva["os"].tipo_manutencao = "CORRETIVA"
    os_corretiva["os"].save()
    curta = _cliente(os_corretiva["tecnico"]).post(_url(os_corretiva), {"pergunta": "oi"}, format="json")
    assert curta.status_code == 400 and "pergunta" in curta.data["erros"]


@pytest.mark.parametrize("erro", [
    FalhaTransporte(),
    FalhaTransporte(429),
    FalhaTransporte(500),
    FalhaTransporte(403),
])
def test_falha_do_provedor_responde_503_amigavel_sem_bloquear(ia, os_corretiva, erro):
    ia.erro = erro

    resposta = _cliente(os_corretiva["tecnico"]).post(_url(os_corretiva), {"pergunta": "Como limpar o dreno entupido?"}, format="json")

    assert resposta.status_code == 503
    assert "indisponível" in resposta.data["mensagem"]
    os_corretiva["os"].refresh_from_db()
    assert os_corretiva["os"].status_ordem_servico == "EM_EXECUCAO"


def test_sem_chave_configurada_responde_indisponivel(settings, os_corretiva):
    settings.IA_PROVEDOR = "gemini"
    settings.GEMINI_API_KEY = ""
    ClienteIA.resetar_instancia()

    resposta = _cliente(os_corretiva["tecnico"]).post(_url(os_corretiva), {"pergunta": "Como limpar o dreno entupido?"}, format="json")

    assert resposta.status_code == 503
    assert "não está configurado" in resposta.data["mensagem"]


def test_recusa_ou_resposta_vazia_vira_indisponivel(settings):
    settings.IA_PROVEDOR = "gemini"
    settings.GEMINI_API_KEY = "chave"
    for falso in (TransporteFalso(finish="SAFETY"), TransporteFalso(texto="  ")):
        with pytest.raises(IAIndisponivelError) as erro:
            ClienteIA(transporte=falso).gerar("sistema", "conteudo")
        assert erro.value.invalida is True


def test_falha_temporaria_e_repetida_e_erro_de_cliente_nao(settings):
    settings.IA_PROVEDOR = "gemini"
    settings.GEMINI_API_KEY = "chave"
    settings.IA_MAX_RETRIES = 2

    temporaria = TransporteFalso(erro=FalhaTransporte(503))
    with pytest.raises(IAIndisponivelError):
        ClienteIA(transporte=temporaria).gerar("sistema", "conteudo")
    assert len(temporaria.chamadas) == 3

    definitiva = TransporteFalso(erro=FalhaTransporte(400))
    with pytest.raises(IAIndisponivelError):
        ClienteIA(transporte=definitiva).gerar("sistema", "conteudo")
    assert len(definitiva.chamadas) == 1


def test_pdf_do_manual_vai_como_inline_data_no_gemini(settings):
    settings.IA_PROVEDOR = "gemini"
    settings.GEMINI_API_KEY = "chave"
    falso = TransporteFalso()
    pdf = base64.b64encode(b"%PDF-1.4 manual").decode("ascii")
    blocos = [
        {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf}, "title": "Manual"},
        {"type": "text", "text": "Pergunta"},
    ]

    ClienteIA(transporte=falso).gerar("sistema", blocos)

    partes = _partes(falso.chamadas[0])
    assert partes[0] == {"inline_data": {"mime_type": "application/pdf", "data": pdf}}
    assert partes[1] == {"text": "Pergunta"}


def test_provedor_grok_usa_formato_de_chat_completions(settings):
    settings.IA_PROVEDOR = "grok"
    settings.GROK_API_KEY = "chave-grok"
    settings.GROK_MODEL = "grok-4.3"
    chamadas = []

    def transporte(url, cabecalhos, corpo, timeout):
        chamadas.append({"url": url, "cabecalhos": cabecalhos, "corpo": corpo})
        return {"choices": [{"finish_reason": "stop", "message": {"content": "Resposta do Grok"}}]}

    cliente = ClienteIA(transporte=transporte)
    assert cliente.gerar("sistema", [{"type": "text", "text": "Pergunta"}]) == "Resposta do Grok"
    assert cliente.provedor == "grok" and cliente.modelo == "grok-4.3"
    chamada = chamadas[0]
    assert chamada["url"] == "https://api.x.ai/v1/chat/completions"
    assert chamada["cabecalhos"]["Authorization"] == "Bearer chave-grok"
    assert chamada["corpo"]["model"] == "grok-4.3"
    assert chamada["corpo"]["messages"] == [{"role": "system", "content": "sistema"}, {"role": "user", "content": "Pergunta"}]


def test_provedor_desconhecido_fica_nao_configurado(settings):
    settings.IA_PROVEDOR = "outro"
    settings.GEMINI_API_KEY = "chave"
    with pytest.raises(IAIndisponivelError) as erro:
        ClienteIA(transporte=TransporteFalso()).gerar("sistema", "conteudo")
    assert "não está configurado" in erro.value.mensagem


def test_intelligence_envia_so_agregados_sem_dados_pessoais(ia, os_corretiva):
    gerente = criar_usuario("Gerente Secreto", "gerente.secreto@fho.edu.br", "GERENTE")
    participante = criar_usuario("Joao Particular", "joao.particular@fho.edu.br", "SOLICITANTE")
    OsParticipante.objects.create(ordem_servico=os_corretiva["os"], usuario=participante)
    ia.texto = "Resumo do período: 1 ordem aberta. Pontos de atenção: nenhum. Recomendações: manter."

    resposta = _cliente(gerente).post("/indicadores/intelligence/", {"periodo": "30d"}, format="json")

    assert resposta.status_code == 200
    dados = resposta.data["dados"]
    assert dados["periodo"]["rotulo"] == "Últimos 30 dias"
    assert dados["indicadores_usados"]["indicadores"]["volume_total"] == 1
    assert dados["analise"].startswith("Resumo do período")

    enviado = _texto(ia.chamadas[0]) + _sistema(ia.chamadas[0])
    for proibido in ("Maria Sigilosa", "maria.sigilosa@fho.edu.br", "Joao Particular", "joao.particular", "Gerente Secreto", "Tec", "tec.ia@fho.edu.br"):
        assert proibido not in enviado
    payload = json.loads(_texto(ia.chamadas[0]).split("\n", 1)[1])
    assert set(payload) == {"periodo", "indicadores", "ocorrencias_por_tipo_de_ativo", "predios_mais_ocorrencias", "locais_mais_ocorrencias", "ativos_mais_ocorrencias"}


def test_intelligence_falha_nao_afeta_indicadores_nativos(ia, os_corretiva):
    gerente = criar_usuario("Gerente", "gerente.ia@fho.edu.br", "GERENTE")
    ia.erro = FalhaTransporte()

    falha = _cliente(gerente).post("/indicadores/intelligence/", {"periodo": "30d"}, format="json")
    nativos = _cliente(gerente).get("/ordem-servico/indicadores-gerenciais/?periodo=30d")

    assert falha.status_code == 503
    assert nativos.status_code == 200 and nativos.data["dados"]["volume_total"] == 1


def test_intelligence_resposta_invalida_e_permissao(ia, os_corretiva):
    gerente = criar_usuario("Gerente", "gerente2.ia@fho.edu.br", "GERENTE")
    ia.texto = "ok"

    assert _cliente(gerente).post("/indicadores/intelligence/", {}, format="json").status_code == 503
    assert _cliente(os_corretiva["tecnico"]).post("/indicadores/intelligence/", {}, format="json").status_code == 403


def test_consulta_e_persistida_com_status_concluido_e_manual_lido(ia, os_corretiva, settings, tmp_path):
    from ativo.models import ManualAtivo
    from inteligencia.models import ConsultaAssistenteIA

    settings.MEDIA_ROOT = tmp_path
    (tmp_path / "manuais").mkdir()
    (tmp_path / "manuais" / "xtreme.txt").write_text("Dreno: remova a mangueira e sopre com ar comprimido.", encoding="utf-8")
    ativo = os_corretiva["os"].ativo
    manual = ManualAtivo.objects.create(ativo=ativo, titulo="Manual Xtreme", versao="2.1", caminho_arquivo="manuais/xtreme.txt")
    ManualAtivo.objects.create(ativo=ativo, titulo="Manual antigo", caminho_arquivo="manuais/antigo.pdf", ativo_para_consulta=False)

    resposta = _cliente(os_corretiva["tecnico"]).post(_url(os_corretiva), {"pergunta": "Como limpar o dreno entupido?"}, format="json")

    assert resposta.status_code == 200
    dados = resposta.data["dados"]
    assert dados["aviso"] is None and dados["consulta_registrada"] is True
    assert [m["titulo"] for m in dados["base_conhecimento"]["manuais"]] == ["Manual Xtreme"]
    partes = _partes(ia.chamadas[0])
    assert len(partes) == 2 and "Manual Xtreme" in partes[0]["text"] and "ar comprimido" in partes[0]["text"]
    consulta = ConsultaAssistenteIA.objects.get()
    assert (consulta.status, consulta.manual_id, consulta.provedor_ia, consulta.modelo_ia) == ("CONCLUIDO", manual.pk, "gemini", "gemini-flash-latest")
    assert consulta.resposta.startswith("1. Desligue") and consulta.tecnico_id == os_corretiva["tecnico"].pk


def test_manual_inacessivel_usa_so_metadados_e_avisa(ia, os_corretiva):
    from ativo.models import ManualAtivo

    ManualAtivo.objects.create(ativo=os_corretiva["os"].ativo, titulo="Manual na nuvem", caminho_arquivo="https://storage.exemplo/manual.pdf")
    ManualAtivo.objects.create(ativo=os_corretiva["os"].ativo, titulo="Fora da pasta", caminho_arquivo="../../segredo.txt")

    dados = _cliente(os_corretiva["tecnico"]).post(_url(os_corretiva), {"pergunta": "Como limpar o dreno entupido?"}, format="json").data["dados"]

    assert "não está acessível" in dados["aviso"]
    assert len(_partes(ia.chamadas[0])) == 1


@pytest.mark.parametrize("erro, status_esperado", [
    (FalhaTransporte(), "INDISPONIVEL"),
    (None, "RESPOSTA_INVALIDA"),
])
def test_falha_da_consulta_e_persistida_com_status(ia, os_corretiva, erro, status_esperado):
    from inteligencia.models import ConsultaAssistenteIA

    ia.erro = erro
    if erro is None:
        ia.finish = "SAFETY"

    resposta = _cliente(os_corretiva["tecnico"]).post(_url(os_corretiva), {"pergunta": "Como limpar o dreno entupido?"}, format="json")

    assert resposta.status_code == 503
    assert ConsultaAssistenteIA.objects.get().status == status_esperado


def test_assistente_desabilitado_na_tabela_de_configuracao(ia, os_corretiva):
    from inteligencia.models import AssistenteTecnicoIA

    AssistenteTecnicoIA.objects.create(provedor="gemini", modelo="gemini-flash-latest", disponivel=False)

    resposta = _cliente(os_corretiva["tecnico"]).post(_url(os_corretiva), {"pergunta": "Como limpar o dreno entupido?"}, format="json")

    assert resposta.status_code == 503
    assert ia.chamadas == []


def test_os_sem_ativo_responde_mas_nao_registra_consulta(ia, os_corretiva):
    from inteligencia.models import ConsultaAssistenteIA

    os_corretiva["os"].ativo = None
    os_corretiva["os"].save()

    dados = _cliente(os_corretiva["tecnico"]).post(_url(os_corretiva), {"pergunta": "Como limpar o dreno entupido?"}, format="json").data["dados"]

    assert dados["consulta_registrada"] is False
    assert not ConsultaAssistenteIA.objects.exists()


def test_insight_e_indicadores_sao_persistidos(ia, os_corretiva):
    from inteligencia.models import IndicadorGerencial, InsightGerencial

    gerente = criar_usuario("Gerente", "gerente.persist@fho.edu.br", "GERENTE")
    ia.texto = "Resumo do período: 1 ordem aberta. Pontos de atenção: nenhum. Recomendações: manter."

    dados = _cliente(gerente).post("/indicadores/intelligence/", {"periodo": "30d"}, format="json").data["dados"]

    insight = InsightGerencial.objects.get(pk=dados["id_insight"])
    assert (insight.status, insight.gerente_id, insight.provedor_ia) == ("CONCLUIDO", gerente.pk, "gemini")
    assert insight.conteudo.startswith("Resumo do período")
    tipos = set(insight.indicadores.values_list("tipo", flat=True))
    assert {"VOLUME_TOTAL", "BACKLOG_ATIVO", "FILA_TRIAGEM", "USUARIOS_AFETADOS", "DISTRIBUICAO_POR_ATIVO", "DISTRIBUICAO_POR_LOCALIZACAO"} <= tipos
    assert IndicadorGerencial.objects.get(tipo="VOLUME_TOTAL").valor == 1
    assert IndicadorGerencial.objects.get(tipo="DISTRIBUICAO_POR_ATIVO").tipo_ativo == "AR_CONDICIONADO"


def test_insight_com_falha_fica_registrado_como_indisponivel(ia, os_corretiva):
    from inteligencia.models import InsightGerencial

    gerente = criar_usuario("Gerente", "gerente.falha@fho.edu.br", "GERENTE")
    ia.erro = FalhaTransporte()

    assert _cliente(gerente).post("/indicadores/intelligence/", {}, format="json").status_code == 503
    insight = InsightGerencial.objects.get()
    assert insight.status == "INDISPONIVEL" and insight.conteudo is None
    assert insight.indicadores.exists()
