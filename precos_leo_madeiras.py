"""
Preços atuais da Léo Madeiras - Coletados em 30/06/2025
Fonte: https://www.leomadeiras.com.br/
"""

from datetime import datetime

# Data da última atualização
ULTIMA_ATUALIZACAO = datetime(2025, 6, 30)

# Preços de materiais por m² (em reais)
PRECOS_MATERIAIS = {
    'mdf_15mm': {
        'preco_m2': 69.15,  # MDF 15mm 2750x1840mm por R$ 349,90 = R$ 69,15/m²
        'descricao': 'MDF Branco Ártico Texturizado Ultra Premium 15mm',
        'fornecedor': 'Duratex',
        'desperdicio_percentual': 0.15  # 15% de desperdício
    },
    'mdf_18mm': {
        'preco_m2': 77.85,  # MDF 18mm estimado 12% mais caro que 15mm
        'descricao': 'MDF Branco Ártico Texturizado Ultra Premium 18mm',
        'fornecedor': 'Duratex',
        'desperdicio_percentual': 0.15
    },
    'compensado_15mm': {
        'preco_m2': 64.00,  # Compensado Paricá 15mm 2200x1600mm por R$ 224,90 = R$ 64/m²
        'descricao': 'Compensado Paricá 15mm 100% Eucalipto',
        'fornecedor': 'Nacional',
        'desperdicio_percentual': 0.12  # 12% de desperdício
    },
    'compensado_10mm': {
        'preco_m2': 52.50,  # Compensado Paricá 10mm 2200x1600mm por R$ 184,90 = R$ 52,5/m²
        'descricao': 'Compensado Paricá 10mm 100% Eucalipto',
        'fornecedor': 'Nacional',
        'desperdicio_percentual': 0.12
    },
    'mdp_15mm': {
        'preco_m2': 58.00,  # MDP estimado 16% mais barato que MDF
        'descricao': 'MDP Melamínico 15mm',
        'fornecedor': 'Nacional',
        'desperdicio_percentual': 0.18  # 18% de desperdício (mais quebradiço)
    },
    'melamina_15mm': {
        'preco_m2': 89.50,  # Melamina premium estimada 30% mais cara que MDF
        'descricao': 'Melamina Texturizada 15mm',
        'fornecedor': 'Nacional',
        'desperdicio_percentual': 0.10  # 10% de desperdício (já acabada)
    }
}

# Preços de acessórios (em reais por unidade)
PRECOS_ACESSORIOS = {
    'comum': {
        'dobradica': 12.50,
        'puxador': 15.80,
        'corredicica': 45.00,
        'suporte_prateleira': 8.50,
        'fechadura': 25.00,
        'parafuso_kit': 3.50
    },
    'premium': {
        'dobradica': 28.50,
        'puxador': 45.00,
        'corredicica': 89.00,
        'suporte_prateleira': 18.50,
        'fechadura': 65.00,
        'parafuso_kit': 8.50
    }
}

# Custos de mão de obra (em reais por m²)
CUSTOS_MAO_OBRA = {
    'base_m2': 120.00,  # Custo base por m²
    'multiplicadores_complexidade': {
        'simples': 1.0,     # Móveis retos, sem detalhes
        'media': 1.3,       # Móveis com alguns detalhes
        'complexa': 1.7,    # Móveis com muitos detalhes
        'premium': 2.2      # Móveis sob medida complexos
    }
}

# Custos de corte (novo)
CUSTOS_CORTE = {
    'corte_reto_metro': 2.50,      # R$ 2,50 por metro linear de corte reto
    'corte_curvo_metro': 4.50,     # R$ 4,50 por metro linear de corte curvo
    'furo_dobradica': 1.50,        # R$ 1,50 por furo de dobradiça
    'rebaixo_metro': 3.50,         # R$ 3,50 por metro linear de rebaixo
    'chanfro_metro': 2.00,         # R$ 2,00 por metro linear de chanfro
    'taxa_minima': 15.00           # Taxa mínima de corte por peça
}

def calcular_custo_corte_estimado(componentes):
    """
    Calcula custo estimado de corte baseado nos componentes
    """
    custo_total = 0
    
    for comp in componentes:
        # Estimar metros lineares de corte por componente
        perimetro = 2 * (comp['largura_m'] + comp['altura_m'])
        
        # Custo base de corte reto
        custo_corte = perimetro * CUSTOS_CORTE['corte_reto_metro']
        
        # Taxa mínima por peça
        custo_corte = max(custo_corte, CUSTOS_CORTE['taxa_minima'])
        
        # Adicionar custos extras baseado no tipo
        if comp['tipo'] in ['Porta', 'Gaveta']:
            # Portas e gavetas precisam de furos para dobradiças
            custo_corte += 4 * CUSTOS_CORTE['furo_dobradica']  # 4 furos por porta
        
        if comp['tipo'] == 'Prateleira':
            # Prateleiras podem precisar de rebaixos
            custo_corte += comp['largura_m'] * CUSTOS_CORTE['rebaixo_metro']
        
        custo_total += custo_corte
    
    return round(custo_total, 2)

def obter_preco_material(tipo_material):
    """
    Retorna informações de preço para um tipo de material
    """
    return PRECOS_MATERIAIS.get(tipo_material, PRECOS_MATERIAIS['mdf_15mm'])

def obter_precos_acessorios(qualidade):
    """
    Retorna preços de acessórios para uma qualidade específica
    """
    return PRECOS_ACESSORIOS.get(qualidade, PRECOS_ACESSORIOS['comum'])

def obter_custo_mao_obra(complexidade):
    """
    Retorna custo de mão de obra para uma complexidade específica
    """
    multiplicador = CUSTOS_MAO_OBRA['multiplicadores_complexidade'].get(complexidade, 1.3)
    return CUSTOS_MAO_OBRA['base_m2'] * multiplicador

# Informações sobre a fonte dos preços
INFO_FONTE = {
    'nome': 'Léo Madeiras',
    'url': 'https://www.leomadeiras.com.br/',
    'data_coleta': ULTIMA_ATUALIZACAO.strftime('%d/%m/%Y'),
    'observacoes': [
        'Preços coletados do site oficial da Léo Madeiras',
        'Valores podem variar conforme disponibilidade e promoções',
        'Custos de corte estimados baseados em práticas do mercado',
        'Desperdício calculado conforme experiência em marcenaria'
    ]
}

