import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import json

# Importar preços atuais da Léo Madeiras
from precos_leo_madeiras import (
    obter_preco_material, 
    obter_precos_acessorios, 
    obter_custo_mao_obra,
    calcular_custo_corte_estimado,
    INFO_FONTE
)

class SistemaOrcamento:
    """Sistema avançado de orçamento para marcenaria com preços da Léo Madeiras"""
    
    def __init__(self):
        # Usar preços atuais da Léo Madeiras
        self.fonte_precos = INFO_FONTE
    
    def calcular_materiais(self, componentes: List[Dict], tipo_material: str = 'mdf_15mm') -> Dict:
        """Calcular custos de materiais usando preços da Léo Madeiras"""
        
        # Obter informações do material
        info_material = obter_preco_material(tipo_material)
        
        # Calcular área total
        area_total = sum(comp['area_m2'] for comp in componentes)
        
        # Aplicar desperdício
        area_com_desperdicio = area_total * (1 + info_material['desperdicio_percentual'])
        
        # Calcular custo
        custo_total = area_com_desperdicio * info_material['preco_m2']
        
        return {
            'tipo_material': tipo_material,
            'descricao': info_material['descricao'],
            'fornecedor': info_material['fornecedor'],
            'area_liquida_m2': round(area_total, 2),
            'desperdicio_percentual': info_material['desperdicio_percentual'],
            'area_com_desperdicio_m2': round(area_com_desperdicio, 2),
            'preco_m2': info_material['preco_m2'],
            'custo_total': round(custo_total, 2)
        }
    
    def calcular_acessorios(self, componentes: List[Dict], qualidade: str = 'comum') -> Dict:
        """Calcular custos de acessórios usando preços da Léo Madeiras"""
        
        # Obter preços dos acessórios
        precos = obter_precos_acessorios(qualidade)
        
        # Contar acessórios necessários
        itens = {}
        
        for comp in componentes:
            tipo = comp['tipo'].lower()
            
            if 'porta' in tipo or 'gaveta' in tipo:
                # Dobradiças (2 por porta/gaveta)
                if 'dobradica' not in itens:
                    itens['dobradica'] = {'quantidade': 0, 'preco_unitario': precos['dobradica']}
                itens['dobradica']['quantidade'] += 2
                
                # Puxadores (1 por porta/gaveta)
                if 'puxador' not in itens:
                    itens['puxador'] = {'quantidade': 0, 'preco_unitario': precos['puxador']}
                itens['puxador']['quantidade'] += 1
            
            if 'gaveta' in tipo:
                # Corrediças (1 par por gaveta)
                if 'corredicica' not in itens:
                    itens['corredicica'] = {'quantidade': 0, 'preco_unitario': precos['corredicica']}
                itens['corredicica']['quantidade'] += 1
            
            if 'prateleira' in tipo:
                # Suportes (4 por prateleira)
                if 'suporte_prateleira' not in itens:
                    itens['suporte_prateleira'] = {'quantidade': 0, 'preco_unitario': precos['suporte_prateleira']}
                itens['suporte_prateleira']['quantidade'] += 4
        
        # Calcular custo total
        custo_total = 0
        for item, dados in itens.items():
            dados['custo_total'] = dados['quantidade'] * dados['preco_unitario']
            custo_total += dados['custo_total']
        
        return {
            'qualidade': qualidade,
            'itens': itens,
            'custo_total': round(custo_total, 2)
        }
    
    def calcular_mao_obra(self, componentes: List[Dict], complexidade: str = 'media') -> Dict:
        """Calcular custos de mão de obra usando preços da Léo Madeiras"""
        
        # Calcular área total
        area_total = sum(comp['area_m2'] for comp in componentes)
        
        # Obter custo por m² baseado na complexidade
        custo_m2 = obter_custo_mao_obra(complexidade)
        
        # Calcular custo base
        custo_base = area_total * custo_m2
        
        # Calcular custo total
        custo_total = custo_base
        
        return {
            'complexidade': complexidade,
            'area_m2': round(area_total, 2),
            'custo_m2': custo_m2,
            'custo_base': round(custo_base, 2),
            'custo_total': round(custo_total, 2)
        }
    
    def calcular_corte(self, componentes: List[Dict]) -> Dict:
        """Calcular custos de corte usando estimativas baseadas nos componentes"""
        
        custo_corte = calcular_custo_corte_estimado(componentes)
        
        return {
            'descricao': 'Corte e usinagem de peças',
            'componentes_processados': len(componentes),
            'custo_total': custo_corte
        }
    
    def calcular_custos_individuais(self, componentes: List[Dict], configuracoes: Dict) -> List[Dict]:
        """Calcular custos individuais para cada componente"""
        
        # Obter informações dos materiais e preços
        info_material = obter_preco_material(configuracoes['tipo_material'])
        precos_acessorios = obter_precos_acessorios(configuracoes['qualidade_acessorios'])
        custo_mao_obra_m2 = obter_custo_mao_obra(configuracoes['complexidade'])
        
        custos_individuais = []
        
        for comp in componentes:
            # Custo do material
            area_com_desperdicio = comp['area_m2'] * (1 + info_material['desperdicio_percentual'])
            custo_material = area_com_desperdicio * info_material['preco_m2']
            
            # Custo de acessórios
            custo_acessorios = 0
            acessorios_usados = []
            
            tipo = comp['tipo'].lower()
            if 'porta' in tipo or 'gaveta' in tipo:
                # Dobradiças (2 por porta/gaveta)
                custo_acessorios += 2 * precos_acessorios['dobradica']
                acessorios_usados.append(f"2x Dobradiça")
                
                # Puxadores (1 por porta/gaveta)
                custo_acessorios += precos_acessorios['puxador']
                acessorios_usados.append(f"1x Puxador")
            
            if 'gaveta' in tipo:
                # Corrediças (1 par por gaveta)
                custo_acessorios += precos_acessorios['corredicica']
                acessorios_usados.append(f"1x Corrediça")
            
            if 'prateleira' in tipo:
                # Suportes (4 por prateleira)
                custo_acessorios += 4 * precos_acessorios['suporte_prateleira']
                acessorios_usados.append(f"4x Suporte")
            
            # Custo de mão de obra
            custo_mao_obra = comp['area_m2'] * custo_mao_obra_m2
            
            # Custo de corte
            custo_corte = calcular_custo_corte_estimado([comp])
            
            # Subtotal antes da margem
            subtotal = custo_material + custo_acessorios + custo_mao_obra + custo_corte
            
            # Aplicar margem de lucro
            valor_margem = subtotal * configuracoes['margem_lucro']
            custo_total = subtotal + valor_margem
            
            custos_individuais.append({
                'componente_id': comp.get('id', f"comp_{len(custos_individuais)}"),
                'tipo': comp['tipo'],
                'area_m2': comp['area_m2'],
                'custo_material': round(custo_material, 2),
                'custo_acessorios': round(custo_acessorios, 2),
                'custo_mao_obra': round(custo_mao_obra, 2),
                'custo_corte': round(custo_corte, 2),
                'subtotal': round(subtotal, 2),
                'valor_margem': round(valor_margem, 2),
                'custo_total': round(custo_total, 2),
                'custo_por_m2': round(custo_total / comp['area_m2'] if comp['area_m2'] > 0 else 0, 2),
                'acessorios_usados': acessorios_usados,
                'detalhamento': {
                    'material': {
                        'tipo': configuracoes['tipo_material'],
                        'area_liquida': comp['area_m2'],
                        'area_com_desperdicio': round(area_com_desperdicio, 2),
                        'preco_m2': info_material['preco_m2'],
                        'desperdicio_percentual': info_material['desperdicio_percentual']
                    },
                    'mao_obra': {
                        'complexidade': configuracoes['complexidade'],
                        'custo_m2': custo_mao_obra_m2
                    }
                }
            })
        
        return custos_individuais
    
    def gerar_orcamento_completo(self, componentes: List[Dict], configuracoes: Dict = None) -> Dict:
        """Gerar orçamento completo com preços da Léo Madeiras"""
        
        if not configuracoes:
            configuracoes = {
                'tipo_material': 'mdf_15mm',
                'qualidade_acessorios': 'comum',
                'complexidade': 'media',
                'margem_lucro': 0.30
            }
        
        # Calcular cada categoria
        materiais = self.calcular_materiais(componentes, configuracoes['tipo_material'])
        acessorios = self.calcular_acessorios(componentes, configuracoes['qualidade_acessorios'])
        mao_obra = self.calcular_mao_obra(componentes, configuracoes['complexidade'])
        corte = self.calcular_corte(componentes)
        
        # Calcular subtotais
        subtotal_materiais = materiais['custo_total']
        subtotal_acessorios = acessorios['custo_total']
        subtotal_mao_obra = mao_obra['custo_total']
        subtotal_corte = corte['custo_total']
        
        # Subtotal antes da margem
        subtotal_antes_margem = subtotal_materiais + subtotal_acessorios + subtotal_mao_obra + subtotal_corte
        
        # Aplicar margem de lucro
        valor_margem = subtotal_antes_margem * configuracoes['margem_lucro']
        valor_final = subtotal_antes_margem + valor_margem
        
        # Calcular área total
        area_total = sum(comp['area_m2'] for comp in componentes)
        valor_por_m2 = valor_final / area_total if area_total > 0 else 0
        
        # Resumo
        resumo = {
            'subtotal_materiais': round(subtotal_materiais, 2),
            'subtotal_acessorios': round(subtotal_acessorios, 2),
            'subtotal_mao_obra': round(subtotal_mao_obra, 2),
            'subtotal_corte': round(subtotal_corte, 2),
            'subtotal_antes_margem': round(subtotal_antes_margem, 2),
            'valor_margem': round(valor_margem, 2),
            'valor_final': round(valor_final, 2),
            'area_total_m2': round(area_total, 2),
            'valor_por_m2': round(valor_por_m2, 2)
        }
        
        # Calcular custos individuais por componente
        custos_individuais = self.calcular_custos_individuais(componentes, configuracoes)
        
        return {
            'configuracoes': configuracoes,
            'materiais': materiais,
            'acessorios': acessorios,
            'mao_obra': mao_obra,
            'corte': corte,
            'custos_individuais': custos_individuais,
            'resumo': resumo,
            'fonte_precos': self.fonte_precos,
            'data_orcamento': datetime.now().isoformat()
        }

# Instância global do sistema
sistema_orcamento = SistemaOrcamento()

