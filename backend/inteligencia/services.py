import base64
import json
from decimal import Decimal
from pathlib import Path

from django.db import transaction

from django.conf import settings

from django.utils import timezone

from historico.models import Historico
from ativo.models import ManualAtivo
from inteligencia.cliente import ClienteIA, IAIndisponivelError
from inteligencia.models import (
    STATUS_CONCLUIDO,
    STATUS_INDISPONIVEL,
    STATUS_PROCESSANDO,
    STATUS_RESPOSTA_INVALIDA,
    AssistenteTecnicoIA,
    ConsultaAssistenteIA,
    IndicadorGerencial,
    InsightGerencial,
    InsightIndicador,
)
from ordem_servico.constantes import status_para_api

SISTEMA_ASSISTENTE = (
    "Você é o assistente técnico do TechOrder, um sistema de manutenção predial de uma instituição de ensino. "
    "Responda em português do Brasil, de forma objetiva, em passos numerados quando for um procedimento. "
    "Baseie-se no contexto do equipamento enviado. Quando o contexto informar que não há manual cadastrado, "
    "comece a resposta dizendo claramente que não há base de conhecimento do fabricante para este equipamento "
    "e que a orientação é genérica. Não invente códigos de peça, valores de torque, pressões ou especificações "
    "que não estejam no contexto. Sempre lembre de desligar e bloquear a energia antes de intervir e de usar os EPIs "
    "adequados. Se a pergunta não tiver relação com manutenção, diga que só pode ajudar com o atendimento técnico."
)

SISTEMA_INTELLIGENCE = (
    "Você é um analista de gestão de manutenção predial. Você recebe apenas indicadores agregados e anonimizados "
    "de um período. Escreva em português do Brasil uma análise curta com três seções: 'Resumo do período', "
    "'Pontos de atenção' e 'Recomendações'. Cite os números usados. Não invente dados que não estejam nos indicadores; "
    "quando um indicador vier nulo, diga que não há dados suficientes para ele."
)

CHAVES_INDICADORES_IA = (
    'volume_total', 'volume_corretivas', 'volume_preventivas', 'backlog_ativo', 'fila_triagem', 'total_solucionadas',
    'tempo_medio_horas', 'mttr_horas',
    'taxa_resolucao_primeira_intervencao', 'satisfacao_media', 'total_avaliacoes', 'reincidencias', 'taxa_reincidencia',
    'usuarios_afetados', 'saude_ativos',
)


TAMANHO_MAX_MANUAL_BYTES = 10 * 1024 * 1024
TAMANHO_MAX_TEXTO_MANUAL = 20000


def _arquivo_local_do_manual(caminho):
    if not caminho or '://' in caminho:
        return None
    raiz = Path(settings.MEDIA_ROOT).resolve()
    arquivo = Path(caminho)
    arquivo = (arquivo if arquivo.is_absolute() else raiz / arquivo).resolve()
    if not arquivo.is_relative_to(raiz) or not arquivo.is_file() or arquivo.stat().st_size > TAMANHO_MAX_MANUAL_BYTES:
        return None
    return arquivo


def carregar_manuais(ativo):
    manuais = []
    for manual in ManualAtivo.objects.filter(ativo=ativo, ativo_para_consulta=True).order_by('id_manual'):
        arquivo = _arquivo_local_do_manual(manual.caminho_arquivo)
        bloco = None
        if arquivo is not None and arquivo.suffix.lower() == '.pdf':
            bloco = {
                'type': 'document',
                'source': {'type': 'base64', 'media_type': 'application/pdf', 'data': base64.b64encode(arquivo.read_bytes()).decode('ascii')},
                'title': manual.titulo[:150],
            }
        elif arquivo is not None and arquivo.suffix.lower() in ('.txt', '.md'):
            bloco = {
                'type': 'document',
                'source': {'type': 'text', 'media_type': 'text/plain', 'data': arquivo.read_text(encoding='utf-8', errors='replace')[:TAMANHO_MAX_TEXTO_MANUAL]},
                'title': manual.titulo[:150],
            }
        manuais.append({'manual': manual, 'bloco': bloco})
    return manuais


def manuais_do_ativo(ativo):
    return [
        {'id_manual': item['manual'].id_manual, 'titulo': item['manual'].titulo, 'versao': item['manual'].versao, 'conteudo_lido': item['bloco'] is not None}
        for item in carregar_manuais(ativo)
    ]


def montar_contexto_assistente(ordem_servico, manuais_carregados=None):
    ativo = ordem_servico.ativo
    manuais_carregados = manuais_carregados if manuais_carregados is not None else (carregar_manuais(ativo) if ativo is not None else [])
    manuais = [
        {'id_manual': item['manual'].id_manual, 'titulo': item['manual'].titulo, 'versao': item['manual'].versao, 'conteudo_lido': item['bloco'] is not None}
        for item in manuais_carregados
    ]
    eventos = list(
        Historico.objects.filter(ordem_servico=ordem_servico, status_novo__isnull=False)
        .order_by('-data_registro', '-id_historico_ordem_servico')
        .values_list('status_novo', flat=True)[:5]
    )
    return {
        'ordem_servico': {
            'id': ordem_servico.pk,
            'categoria': ordem_servico.categoria_manutencao,
            'status': status_para_api(ordem_servico.status_ordem_servico),
            'descricao_problema': ordem_servico.descricao_servico,
            'ultimos_status': [status_para_api(status) for status in eventos],
        },
        'equipamento': {
            'tipo': ativo.tipo_ativo,
            'marca': ativo.marca,
            'modelo': ativo.modelo,
            'codigo_patrimonial': ativo.codigo_patrimonial,
            'periodicidade_preventiva_dias': ativo.periodicidade_preventiva_dias,
            'ultima_preventiva': ativo.dt_ultima_preventiva.isoformat() if ativo.dt_ultima_preventiva else None,
        } if ativo is not None else None,
        'manuais': manuais,
        'possui_manual': bool(manuais),
    }


def _aviso_base_conhecimento(contexto):
    if contexto['equipamento'] is None:
        return "Esta ordem não tem ativo vinculado; a resposta usa apenas a descrição do problema."
    if not contexto['possui_manual']:
        return "Não há manual cadastrado para este ativo; a resposta é uma orientação genérica."
    if not any(manual['conteudo_lido'] for manual in contexto['manuais']):
        return "Há manual cadastrado, mas o arquivo não está acessível ao servidor; só o título e a versão foram usados."
    return None


def _registrar_consulta(ordem_servico, usuario, manuais_carregados, pergunta, cliente):
    if not ordem_servico.ativo_id:
        return None
    return ConsultaAssistenteIA.objects.create(
        tecnico=usuario,
        ordem_servico=ordem_servico,
        ativo_id=ordem_servico.ativo_id,
        manual=next((item['manual'] for item in manuais_carregados if item['bloco'] is not None), None),
        provedor_ia=ClienteIA.PROVEDOR,
        modelo_ia=cliente.modelo[:60],
        pergunta=pergunta,
        status=STATUS_PROCESSANDO,
    )


def _finalizar_consulta(consulta, status, resposta=None):
    if consulta is None:
        return
    consulta.status = status
    consulta.resposta = resposta
    consulta.save(update_fields=['status', 'resposta'])


def consultar_assistente(ordem_servico, pergunta, usuario, cliente=None):
    manuais_carregados = carregar_manuais(ordem_servico.ativo) if ordem_servico.ativo_id else []
    contexto = montar_contexto_assistente(ordem_servico, manuais_carregados)
    cliente = cliente or ClienteIA.instancia()
    consulta = _registrar_consulta(ordem_servico, usuario, manuais_carregados, pergunta, cliente)

    blocos = [item['bloco'] for item in manuais_carregados if item['bloco'] is not None]
    texto = (
        "Contexto do atendimento (JSON):\n"
        f"{json.dumps(contexto, ensure_ascii=False, default=str)}\n\n"
        f"Pergunta do técnico: {pergunta}"
    )
    conteudo = [*blocos, {'type': 'text', 'text': texto}] if blocos else texto

    try:
        if not assistente_habilitado():
            raise IAIndisponivelError("O assistente técnico está desabilitado pela administração.")
        resposta = cliente.gerar(SISTEMA_ASSISTENTE, conteudo)
    except IAIndisponivelError as erro:
        _finalizar_consulta(consulta, STATUS_RESPOSTA_INVALIDA if erro.invalida else STATUS_INDISPONIVEL)
        raise

    _finalizar_consulta(consulta, STATUS_CONCLUIDO, resposta)
    return {
        'id_consulta': consulta.id_consulta if consulta else None,
        'consulta_registrada': consulta is not None,
        'resposta': resposta,
        'modelo': cliente.modelo,
        'aviso': _aviso_base_conhecimento(contexto),
        'base_conhecimento': {
            'possui_manual': contexto['possui_manual'],
            'manuais': contexto['manuais'],
            'equipamento': contexto['equipamento'],
        },
        'dt_consulta': timezone.now(),
    }


def assistente_habilitado():
    configuracao = AssistenteTecnicoIA.objects.filter(pk=1).values_list('disponivel', flat=True).first()
    return configuracao is None or configuracao


def montar_payload_intelligence(indicadores):
    periodo = indicadores['periodo']
    payload = {
        'periodo': {
            'rotulo': periodo['rotulo'],
            'inicio': periodo['inicio'].isoformat(),
            'fim': periodo['fim'].isoformat(),
        },
        'indicadores': {chave: indicadores.get(chave) for chave in CHAVES_INDICADORES_IA},
        'ocorrencias_por_tipo_de_ativo': {},
        'predios_mais_ocorrencias': [
            {'predio': item['predio_nome'], 'total': item['total']} for item in indicadores.get('predios_mais_ocorrencias', [])
        ],
        'locais_mais_ocorrencias': [
            {'predio': item['predio_nome'], 'local': item['localizacao_nome'], 'total': item['total']}
            for item in indicadores.get('distribuicao_por_localizacao', [])
        ],
        'ativos_mais_ocorrencias': [
            {'patrimonio': item['codigo_patrimonial'], 'tipo': item['tipo_ativo'], 'total': item['total']}
            for item in indicadores.get('distribuicao_por_ativo', [])
        ],
    }
    for item in indicadores.get('distribuicao_por_ativo', []):
        tipo = item['tipo_ativo'] or 'NAO_INFORMADO'
        payload['ocorrencias_por_tipo_de_ativo'][tipo] = payload['ocorrencias_por_tipo_de_ativo'].get(tipo, 0) + item['total']
    return payload


INDICADORES_ESCALARES = (
    ('VOLUME_TOTAL', 'volume_total'),
    ('FILA_TRIAGEM', 'fila_triagem'),
    ('TOTAL_SOLUCIONADO', 'total_solucionadas'),
    ('TEMPO_MEDIO', 'tempo_medio_horas'),
    ('BACKLOG_ATIVO', 'backlog_ativo'),
    ('MTTR', 'mttr_horas'),
    ('TAXA_PRIMEIRA_INTERVENCAO', 'taxa_resolucao_primeira_intervencao'),
    ('SATISFACAO', 'satisfacao_media'),
    ('REINCIDENCIA', 'taxa_reincidencia'),
    ('USUARIOS_AFETADOS', 'usuarios_afetados'),
)


def registrar_indicadores(gerente, indicadores):
    periodo = indicadores['periodo']
    base = {
        'gerente': gerente,
        'dt_inicio_periodo': timezone.localtime(periodo['inicio']).date(),
        'dt_fim_periodo': max(timezone.localtime(periodo['fim']).date(), timezone.localtime(periodo['inicio']).date()),
    }
    registros = [
        IndicadorGerencial(tipo=tipo, valor=Decimal(str(indicadores[chave])), **base)
        for tipo, chave in INDICADORES_ESCALARES
        if indicadores.get(chave) is not None
    ]
    registros += [
        IndicadorGerencial(tipo='DISTRIBUICAO_POR_ATIVO', tipo_ativo=item['tipo_ativo'], valor=Decimal(item['total']), **base)
        for item in indicadores.get('distribuicao_por_tipo_ativo', []) if item['tipo_ativo']
    ]
    registros += [
        IndicadorGerencial(tipo='DISTRIBUICAO_POR_LOCALIZACAO', predio_id=item['id_predio'], valor=Decimal(item['total']), **base)
        for item in indicadores.get('predios_mais_ocorrencias', []) if item['id_predio']
    ]
    for registro in registros:
        registro.save()
    return registros


def gerar_insight(indicadores, gerente, cliente=None):
    payload = montar_payload_intelligence(indicadores)
    cliente = cliente or ClienteIA.instancia()

    with transaction.atomic():
        registros = registrar_indicadores(gerente, indicadores)
        insight = InsightGerencial.objects.create(
            gerente=gerente,
            dt_inicio_periodo=registros[0].dt_inicio_periodo if registros else timezone.localdate(),
            dt_fim_periodo=registros[0].dt_fim_periodo if registros else timezone.localdate(),
            provedor_ia=ClienteIA.PROVEDOR,
            modelo_ia=cliente.modelo[:60],
            status=STATUS_PROCESSANDO,
        )
        InsightIndicador.objects.bulk_create([InsightIndicador(insight=insight, indicador=registro) for registro in registros])

    try:
        analise = cliente.gerar(
            SISTEMA_INTELLIGENCE,
            "Indicadores agregados do período (JSON):\n" + json.dumps(payload, ensure_ascii=False, default=str),
        )
        if len(analise.strip()) < 20:
            raise IAIndisponivelError("O serviço de inteligência artificial retornou uma resposta vazia ou inválida.", invalida=True)
    except IAIndisponivelError as erro:
        insight.status = STATUS_RESPOSTA_INVALIDA if erro.invalida else STATUS_INDISPONIVEL
        insight.save(update_fields=['status'])
        erro.id_insight = insight.id_insight
        raise

    insight.status = STATUS_CONCLUIDO
    insight.conteudo = analise
    insight.save(update_fields=['status', 'conteudo'])
    return {
        'id_insight': insight.id_insight,
        'periodo': payload['periodo'],
        'indicadores_usados': payload,
        'analise': analise,
        'modelo': cliente.modelo,
        'gerado_em': insight.dt_geracao,
    }
