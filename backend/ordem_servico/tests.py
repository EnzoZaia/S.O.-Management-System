from django.utils import timezone
import pytest
from rest_framework.test import APIClient

from ativo.models import Ativo
from grupo.models import Grupo
from grupo_usuario.models import GrupoUsuario
from localizacao.models import Localizacao
from ordem_servico.models import OrdemServico
from predio.models import Predio
from usuario.models import Usuario


@pytest.mark.django_db
def test_concluir_os_com_tag_patrimonio_nao_estoura_nameerror():
    """
    Regressão: ordem_servico/views.py usava Ativo.objects.filter(...) sem
    importar o model Ativo, gerando NameError sempre que a observação de
    conclusão trazia a tag [PAT: <codigo>].
    """
    predio = Predio.objects.create(nome_predio="Bloco A")
    localizacao = Localizacao.objects.create(predio=predio, desc_localizacao="Sala 101")
    ativo = Ativo.objects.create(
        localizacao=localizacao,
        codigo_patrimonial="PAT-001",
        tipo_ativo="AR_CONDICIONADO",
        periodicidade_preventiva_dias=90,
    )

    grupo_tecnico = Grupo.objects.create(desc_grupo="TECNICO")
    tecnico = Usuario.objects.create(
        nome="Tecnico", email="tecnico@fho.edu.br", senha_hash="x", email_confirmado=True
    )
    GrupoUsuario.objects.create(usuario=tecnico, grupo=grupo_tecnico)

    ordem_servico = OrdemServico.objects.create(
        localizacao=localizacao,
        tecnico=tecnico,
        tipo_manutencao="CORRETIVA",
        prioridade_urgencia="NAO",
        status_ordem_servico="APROVADA",
        dt_abertura=timezone.now(),
        descricao_servico="Ar-condicionado não liga.",
    )

    client = APIClient()
    client.force_authenticate(user=tecnico)

    resposta = client.patch(f"/ordem-servico/{ordem_servico.pk}/", {
        "status_ordem_servico": "CONCLUIDA",
        "observacao": f"Trocado o filtro. [PAT: {ativo.codigo_patrimonial}]",
    })

    assert resposta.status_code == 200

    ativo.refresh_from_db()
    assert ativo.dt_ultima_preventiva is not None

    ordem_servico.refresh_from_db()
    assert ordem_servico.status_ordem_servico == "CONCLUIDA"
    assert ordem_servico.dt_conclusao is not None, (
        "Regressão: dt_conclusao de OS corretiva não era persistido antes da Etapa 3 "
        "(só o Ativo era salvo), o que excluía essas OS do indicador de tempo médio do dashboard."
    )
    assert ordem_servico.ativo_id == ativo.pk


@pytest.mark.django_db
def test_abrir_os_corretiva_pelo_totem_anonimo_usa_diretor():
    """Ponta-a-ponta: POST /ordem-servico/ sem autenticação (fluxo do totem) passa pelo serializer -> Diretor -> Builder."""
    predio = Predio.objects.create(nome_predio="Bloco B")
    localizacao = Localizacao.objects.create(predio=predio, desc_localizacao="Recepção")
    # O fluxo do totem registra o histórico com Usuario.objects.first() quando
    # não há autenticação, então precisa existir ao menos um usuário no banco.
    Usuario.objects.create(nome="Admin", email="admin@fho.edu.br", senha_hash="x")

    client = APIClient()

    resposta = client.post("/ordem-servico/", {
        "localizacao": localizacao.pk,
        "descricao_servico": "Torneira da recepção pingando.",
        "categoria_manutencao": "GERAIS",
        "prioridade_urgencia": "NAO",
    })

    assert resposta.status_code == 201

    ordem_servico = OrdemServico.objects.get(pk=resposta.data["dados"]["id_ordem_servico"])
    assert ordem_servico.tipo_manutencao == "CORRETIVA"
    assert ordem_servico.status_ordem_servico == "ABERTA"
    assert ordem_servico.solicitante is None
    assert ordem_servico.dt_abertura is not None
