from django.db import transaction
from django.utils import timezone

from ativo.models import Ativo
from ativo.services import registrar_preventiva_concluida
from ordem_servico.constantes import APROVADA, ATRIBUIDA, EM_EXECUCAO, ENCERRADA, STATUS_FINAIS, TIPO_PREVENTIVA, status_para_api
from ordem_servico.fachada import OrdemServicoFacade
from ordem_servico.models import OrdemServico
from predio.models import Predio
from preventiva_grupo.catalogo import catalogo_do_tipo, categoria_para_tipos
from preventiva_grupo.models import (
    ITEM_EXECUTADO,
    ITEM_NAO_EXECUTADO,
    ITEM_PENDENTE,
    RESULTADO_CONCLUIDO,
    RESULTADO_NAO_CONCLUIDO,
    RESULTADO_PENDENTE,
    ChecklistItemAtivo,
    OrdemServicoAtivo,
)
from usuario.models import Usuario
from utils.historico import registrar_historico
from utils.permissions import usuario_tem_grupo

MOTIVO_MIN = 10
MOTIVO_MAX = 200
MENSAGEM_MESMO_PREDIO = "Só é possível agrupar ativos do mesmo prédio. Gere uma ordem por prédio."


class PreventivaGrupoError(Exception):
    def __init__(self, mensagem, erros=None, status_code=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.erros = erros
        self.status_code = status_code


def _validar_motivo(texto, campo, erros):
    valor = (texto or '').strip()
    if not valor:
        erros[campo] = ["Informe o motivo."]
    elif len(valor) < MOTIVO_MIN:
        erros[campo] = [f"Descreva o motivo com pelo menos {MOTIVO_MIN} caracteres."]
    elif len(valor) > MOTIVO_MAX:
        erros[campo] = [f"Use no máximo {MOTIVO_MAX} caracteres no motivo."]
    return valor


def ordens_agrupadas():
    return OrdemServico.objects.filter(tipo_manutencao=TIPO_PREVENTIVA, itens_preventiva__isnull=False).distinct()


def nome_ativo(ativo):
    nome = f"{ativo.marca or ''} {ativo.modelo or ''}".strip()
    return nome or 'Equipamento'


def montar_grupo(ordem_servico):
    itens = list(
        OrdemServicoAtivo.objects.filter(ordem_servico=ordem_servico)
        .select_related('ativo__localizacao__predio')
        .order_by('id_ordem_servico_ativo')
    )
    predio = itens[0].ativo.localizacao.predio if itens else None
    return {
        'id_ordem_servico': ordem_servico.id_ordem_servico,
        'predio': predio.id_predio if predio else None,
        'predio_nome': predio.nome_predio if predio else None,
        'tecnico': ordem_servico.tecnico_id,
        'tecnico_nome': ordem_servico.tecnico_nome,
        'status_ordem_servico': status_para_api(ordem_servico.status_ordem_servico),
        'dt_abertura': ordem_servico.dt_abertura,
        'dt_conclusao': ordem_servico.dt_conclusao,
        'itens': [
            {
                'ativo': item.ativo_id,
                'codigo_patrimonial': item.ativo.codigo_patrimonial,
                'nome': nome_ativo(item.ativo),
                'resultado': item.resultado,
                'motivo': item.motivo,
                'dt_resultado': item.dt_resultado,
            }
            for item in itens
        ],
    }


def montar_checklist(ordem_servico):
    itens = (
        OrdemServicoAtivo.objects.filter(ordem_servico=ordem_servico)
        .select_related('ativo')
        .prefetch_related('checklist')
        .order_by('id_ordem_servico_ativo')
    )
    return {
        'id_ordem_servico': ordem_servico.id_ordem_servico,
        'status_ordem_servico': status_para_api(ordem_servico.status_ordem_servico),
        'ativos': [montar_checklist_ativo(item) for item in itens],
    }


def montar_checklist_ativo(item):
    return {
        'ativo': item.ativo_id,
        'codigo_patrimonial': item.ativo.codigo_patrimonial,
        'nome': nome_ativo(item.ativo),
        'tipo_ativo': item.ativo.tipo_ativo,
        'resultado': item.resultado,
        'motivo': item.motivo,
        'itens': [
            {'id_item': linha.codigo_item, 'descricao': linha.descricao, 'resultado': linha.resultado, 'motivo': linha.motivo}
            for linha in sorted(item.checklist.all(), key=lambda linha: linha.codigo_item)
        ],
    }


class PreventivaAgrupadaService:
    def __init__(self, fachada=None):
        self._fachada = fachada or OrdemServicoFacade()

    @transaction.atomic
    def gerar(self, responsavel, id_predio, id_tecnico, ids_ativos):
        erros = {}
        predio = Predio.objects.filter(pk=id_predio).first() if id_predio else None
        if predio is None:
            erros['predio'] = ["Informe um prédio válido."]
        tecnico = Usuario.objects.filter(pk=id_tecnico).first() if id_tecnico else None
        if tecnico is None:
            erros['tecnico'] = ["Selecione o técnico responsável."]

        ids = []
        for valor in ids_ativos or []:
            try:
                ids.append(int(valor))
            except (TypeError, ValueError):
                erros['ativos'] = ["Informe os ids dos ativos."]
                break
        ids = list(dict.fromkeys(ids))
        if not ids and 'ativos' not in erros:
            erros['ativos'] = ["Selecione ao menos um ativo."]

        ativos = list(Ativo.objects.select_for_update().filter(pk__in=ids).select_related('localizacao__predio')) if ids else []
        if ids and len(ativos) != len(ids):
            erros['ativos'] = ["Há ativos inexistentes na seleção."]
        if erros:
            raise PreventivaGrupoError("Revise os dados da ordem agrupada.", erros)

        if any(ativo.localizacao.predio_id != predio.id_predio for ativo in ativos):
            raise PreventivaGrupoError(MENSAGEM_MESMO_PREDIO, {'ativos': [MENSAGEM_MESMO_PREDIO]})

        em_execucao = OrdemServicoAtivo.objects.filter(
            ativo_id__in=ids, resultado=RESULTADO_PENDENTE,
        ).exclude(ordem_servico__status_ordem_servico__in=STATUS_FINAIS).select_related('ativo')
        if em_execucao.exists():
            codigos = ', '.join(item.ativo.codigo_patrimonial for item in em_execucao)
            raise PreventivaGrupoError(f"Há ativo já vinculado a uma ordem em execução ({codigos}).", None, 409)

        ativos.sort(key=lambda ativo: ativo.codigo_patrimonial)
        descricao = (
            f"Manutenção preventiva agrupada - {predio.nome_predio}: {len(ativos)} ativo(s) "
            f"({', '.join(ativo.codigo_patrimonial for ativo in ativos)})."
        )
        ordem_servico = self._fachada.abrir_preventiva_agrupada(
            responsavel, ativos[0].localizacao, categoria_para_tipos(ativo.tipo_ativo for ativo in ativos), descricao,
        )

        for ativo in ativos:
            item = OrdemServicoAtivo.objects.create(ordem_servico=ordem_servico, ativo=ativo)
            ChecklistItemAtivo.objects.bulk_create([
                ChecklistItemAtivo(item_ordem=item, codigo_item=codigo, descricao=texto)
                for codigo, texto in catalogo_do_tipo(ativo.tipo_ativo)['itens']
            ])

        self._fachada.atribuir_tecnico(ordem_servico, tecnico, responsavel)
        return ordem_servico

    def _garantir_em_andamento(self, ordem_servico):
        if ordem_servico.status_ordem_servico in STATUS_FINAIS:
            raise PreventivaGrupoError(
                f"Esta ordem já foi finalizada (status atual: {status_para_api(ordem_servico.status_ordem_servico)}).", None, 409,
            )

    def _iniciar_se_preciso(self, ordem_servico, usuario):
        if ordem_servico.status_ordem_servico in (APROVADA, ATRIBUIDA):
            self._fachada.mover_status_por_regra(ordem_servico, usuario, EM_EXECUCAO, "Execução da preventiva agrupada iniciada.")

    @staticmethod
    def _item_do_ativo(ordem_servico, id_ativo):
        return (
            OrdemServicoAtivo.objects.select_for_update()
            .filter(ordem_servico=ordem_servico, ativo_id=id_ativo)
            .select_related('ativo')
            .first()
        )

    @transaction.atomic
    def salvar_checklist(self, ordem_servico, id_ativo, itens, usuario):
        ordem_servico = OrdemServico.objects.select_for_update().get(pk=ordem_servico.pk)
        self._garantir_em_andamento(ordem_servico)
        item = self._item_do_ativo(ordem_servico, id_ativo)
        if item is None:
            raise PreventivaGrupoError("Este ativo não faz parte da ordem agrupada.", None, 404)
        if item.resultado != RESULTADO_PENDENTE:
            raise PreventivaGrupoError("O resultado deste ativo já foi registrado; o checklist não pode mais ser alterado.", None, 409)
        if not isinstance(itens, list) or not itens:
            raise PreventivaGrupoError("Informe ao menos um item do checklist.", {'itens': ["Informe ao menos um item do checklist."]})

        linhas = {linha.codigo_item: linha for linha in ChecklistItemAtivo.objects.select_for_update().filter(item_ordem=item)}
        erros = {}
        respostas = []
        for posicao, resposta in enumerate(itens):
            codigo = resposta.get('item') if isinstance(resposta, dict) else None
            resultado = resposta.get('resultado') if isinstance(resposta, dict) else None
            if codigo not in linhas:
                erros[f'itens[{posicao}]'] = ["Item de checklist inexistente para este ativo."]
                continue
            if resultado not in (ITEM_EXECUTADO, ITEM_NAO_EXECUTADO):
                erros[f'itens[{posicao}]'] = ["Use EXECUTADO ou NAO_EXECUTADO."]
                continue
            motivo = None
            if resultado == ITEM_NAO_EXECUTADO:
                motivo = _validar_motivo(resposta.get('motivo'), f'itens[{posicao}]', erros)
            respostas.append((linhas[codigo], resultado, motivo))
        if erros:
            raise PreventivaGrupoError("Revise os itens do checklist.", erros)

        agora = timezone.now()
        for linha, resultado, motivo in respostas:
            linha.resultado = resultado
            linha.motivo = motivo
            linha.dt_resposta = agora
            linha.usuario = usuario
            linha.save(update_fields=['resultado', 'motivo', 'dt_resposta', 'usuario'])

        self._iniciar_se_preciso(ordem_servico, usuario)
        item.refresh_from_db()
        return montar_checklist_ativo(item)

    @transaction.atomic
    def registrar_resultados(self, ordem_servico, itens, usuario):
        ordem_servico = OrdemServico.objects.select_for_update().get(pk=ordem_servico.pk)
        self._garantir_em_andamento(ordem_servico)
        if not isinstance(itens, list) or not itens:
            raise PreventivaGrupoError("Informe ao menos um resultado.", {'itens': ["Informe ao menos um resultado."]})

        exige_checklist = not (usuario_tem_grupo(usuario, 'GERENTE') or usuario_tem_grupo(usuario, 'GESTOR'))
        erros = {}
        registros = []
        for posicao, envio in enumerate(itens):
            campo = f'itens[{posicao}]'
            id_ativo = envio.get('ativo') if isinstance(envio, dict) else None
            resultado = envio.get('resultado') if isinstance(envio, dict) else None
            item = self._item_do_ativo(ordem_servico, id_ativo) if id_ativo is not None else None
            if item is None:
                erros[campo] = ["Este ativo não faz parte da ordem agrupada."]
                continue
            if item.resultado != RESULTADO_PENDENTE:
                raise PreventivaGrupoError(f"O resultado do ativo {item.ativo.codigo_patrimonial} já foi registrado.", None, 409)
            if resultado not in (RESULTADO_CONCLUIDO, RESULTADO_NAO_CONCLUIDO):
                erros[campo] = ["Use CONCLUIDO ou NAO_CONCLUIDO."]
                continue
            motivo = None
            if resultado == RESULTADO_NAO_CONCLUIDO:
                motivo = _validar_motivo(envio.get('motivo'), campo, erros)
            elif exige_checklist:
                self._garantir_checklist_completo(item)
            registros.append((item, resultado, motivo))
        if erros:
            raise PreventivaGrupoError("Revise os resultados informados.", erros)

        self._iniciar_se_preciso(ordem_servico, usuario)
        agora = timezone.now()
        for item, resultado, motivo in registros:
            item.resultado = resultado
            item.motivo = motivo
            item.dt_resultado = agora
            item.usuario_resultado = usuario
            item.save(update_fields=['resultado', 'motivo', 'dt_resultado', 'usuario_resultado'])
            if resultado == RESULTADO_CONCLUIDO:
                registrar_preventiva_concluida(item.ativo, timezone.localdate())
                registrar_historico(ordem_servico, usuario, f"Ativo {item.ativo.codigo_patrimonial}: preventiva concluída.")
            else:
                registrar_historico(ordem_servico, usuario, f"Ativo {item.ativo.codigo_patrimonial}: não concluído. Motivo: {motivo}")

        if not OrdemServicoAtivo.objects.filter(ordem_servico=ordem_servico, resultado=RESULTADO_PENDENTE).exists():
            concluidos = OrdemServicoAtivo.objects.filter(ordem_servico=ordem_servico, resultado=RESULTADO_CONCLUIDO).count()
            total = OrdemServicoAtivo.objects.filter(ordem_servico=ordem_servico).count()
            self._fachada.mover_status_por_regra(
                ordem_servico, usuario, ENCERRADA,
                f"Todos os ativos têm resultado ({concluidos} de {total} concluídos).",
            )
        return ordem_servico

    @staticmethod
    def _garantir_checklist_completo(item):
        linhas = list(item.checklist.all())
        pendentes = sum(1 for linha in linhas if linha.resultado == ITEM_PENDENTE)
        if pendentes:
            raise PreventivaGrupoError(
                f"Checklist incompleto do ativo {item.ativo.codigo_patrimonial}: faltam {pendentes} item(ns). "
                "Responda todos antes de concluir o ativo."
            )
        if any(linha.resultado == ITEM_NAO_EXECUTADO for linha in linhas):
            raise PreventivaGrupoError(
                f"Checklist incompleto do ativo {item.ativo.codigo_patrimonial}: há itens não executados. "
                "Registre o ativo como não concluído."
            )
