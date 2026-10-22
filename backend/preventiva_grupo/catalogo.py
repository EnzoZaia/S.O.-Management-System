CATALOGO_POR_TIPO = {
    'AR_CONDICIONADO': {
        'categoria': 'REFRIGERACAO',
        'itens': [
            (1, 'Desligar o equipamento e bloquear a alimentação elétrica'),
            (2, 'Limpar ou substituir os filtros de ar'),
            (3, 'Higienizar a serpentina da evaporadora'),
            (4, 'Limpar a bandeja e desobstruir o dreno'),
            (5, 'Verificar ruídos e vibrações anormais'),
            (6, 'Inspecionar a condensadora e a fixação das tubulações'),
            (7, 'Medir a corrente de operação e conferir conexões elétricas'),
            (8, 'Testar o funcionamento e a temperatura de insuflamento'),
        ],
        'materiais': [('Filtro de ar', 1, 'un'), ('Bactericida para serpentina', 0.5, 'L'), ('Pano de limpeza', 2, 'un')],
        'ferramentas': ['Jogo de chaves de fenda e Phillips', 'Alicate amperímetro', 'Termômetro digital', 'Lavadora de baixa pressão'],
        'epis': ['Luvas de proteção', 'Óculos de segurança', 'Calçado de segurança'],
    },
    'BEBEDOURO': {
        'categoria': 'GERAIS',
        'itens': [
            (1, 'Desligar o equipamento e fechar o registro de água'),
            (2, 'Substituir o elemento filtrante'),
            (3, 'Higienizar reservatório, torneiras e bicas'),
            (4, 'Verificar vazamentos nas conexões'),
            (5, 'Conferir a temperatura da água gelada'),
            (6, 'Registrar a data da troca do filtro na etiqueta do equipamento'),
        ],
        'materiais': [('Elemento filtrante', 1, 'un'), ('Solução sanitizante', 0.2, 'L')],
        'ferramentas': ['Chave para carcaça do filtro', 'Termômetro digital'],
        'epis': ['Luvas de proteção', 'Óculos de segurança'],
    },
}

CATALOGO_PADRAO = {
    'categoria': 'GERAIS',
    'itens': [
        (1, 'Inspeção visual geral do equipamento'),
        (2, 'Limpeza externa'),
        (3, 'Teste de funcionamento'),
    ],
    'materiais': [],
    'ferramentas': ['Jogo de chaves básico'],
    'epis': ['Luvas de proteção'],
}


def catalogo_do_tipo(tipo_ativo):
    return CATALOGO_POR_TIPO.get(tipo_ativo, CATALOGO_PADRAO)


def categoria_para_tipos(tipos):
    categorias = {catalogo_do_tipo(tipo)['categoria'] for tipo in tipos}
    return categorias.pop() if len(categorias) == 1 else 'GERAIS'
