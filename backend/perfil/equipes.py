from django.db.models import Q

from perfil.models import Gestor, Tecnico

AREA_TODAS = 'TODAS'


def area_generalista(area):
    return not area or str(area).strip().upper() == AREA_TODAS


def areas_compativeis(area, categoria):
    if area_generalista(area) or not categoria:
        return True
    return str(area).strip().upper() == str(categoria).strip().upper()


def area_do_gestor(usuario):
    return Gestor.objects.filter(usuario_id=usuario.pk).values_list('area_atuacao', flat=True).first()


def filtro_categoria_da_area(area, campo='categoria_manutencao'):
    if area_generalista(area):
        return Q()
    return Q(**{f'{campo}__isnull': True}) | Q(**{campo: str(area).strip().upper()})


def tecnicos_da_equipe(usuario_gestor):
    area = area_do_gestor(usuario_gestor)
    sem_gestor = Q(gestor__isnull=True)
    if not area_generalista(area):
        sem_gestor &= Q(area_atuacao__iexact=str(area).strip()) | Q(area_atuacao__iexact=AREA_TODAS)
    return Tecnico.objects.filter(Q(gestor_id=usuario_gestor.pk) | sem_gestor)


def ids_tecnicos_da_equipe(usuario_gestor):
    return list(tecnicos_da_equipe(usuario_gestor).values_list('usuario_id', flat=True))


def tecnico_atende(usuario_tecnico, categoria):
    area = Tecnico.objects.filter(usuario_id=usuario_tecnico.pk).values_list('area_atuacao', flat=True).first()
    return areas_compativeis(area, categoria)
