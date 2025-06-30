"""
Módulo de Visualização 3D Individual de Móveis
Sistema profissional para aplicação SaaS de orçamento de marcenaria
"""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import streamlit as st

class VisualizadorMoveis3D:
    """Visualizador 3D profissional para móveis individuais"""
    
    def __init__(self):
        self.cores_materiais = {
            'mdf_15mm': '#D2B48C',      # Bege claro
            'mdf_18mm': '#CD853F',      # Peru
            'compensado_15mm': '#DEB887', # Burlywood
            'compensado_10mm': '#F5DEB3', # Wheat
            'melamina_15mm': '#FFFFFF',   # Branco
            'mdp_15mm': '#F0E68C'       # Khaki
        }
        
        self.cores_tipos = {
            'Lateral': '#8B4513',       # Saddle Brown
            'Porta': '#A0522D',         # Sienna
            'Prateleira': '#CD853F',    # Peru
            'Gaveta': '#D2691E',        # Chocolate
            'Fundo': '#DEB887',         # Burlywood
            'Topo': '#F4A460',          # Sandy Brown
            'Base': '#BC8F8F'           # Rosy Brown
        }
    
    def criar_mesh_componente(self, componente: Dict) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Criar mesh 3D para um componente individual"""
        
        largura = componente['largura_m']
        altura = componente['altura_m'] 
        profundidade = componente['profundidade_m']
        
        # Definir vértices do paralelepípedo
        vertices = np.array([
            [0, 0, 0],                    # 0
            [largura, 0, 0],              # 1
            [largura, altura, 0],         # 2
            [0, altura, 0],               # 3
            [0, 0, profundidade],         # 4
            [largura, 0, profundidade],   # 5
            [largura, altura, profundidade], # 6
            [0, altura, profundidade]     # 7
        ])
        
        # Definir faces (triângulos)
        faces = np.array([
            # Face frontal
            [0, 1, 2], [0, 2, 3],
            # Face traseira
            [4, 7, 6], [4, 6, 5],
            # Face esquerda
            [0, 3, 7], [0, 7, 4],
            # Face direita
            [1, 5, 6], [1, 6, 2],
            # Face inferior
            [0, 4, 5], [0, 5, 1],
            # Face superior
            [3, 2, 6], [3, 6, 7]
        ])
        
        return vertices, faces, self._calcular_normais(vertices, faces)
    
    def _calcular_normais(self, vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
        """Calcular normais das faces para iluminação"""
        normais = []
        
        for face in faces:
            v1 = vertices[face[1]] - vertices[face[0]]
            v2 = vertices[face[2]] - vertices[face[0]]
            normal = np.cross(v1, v2)
            normal = normal / np.linalg.norm(normal)
            normais.append(normal)
        
        return np.array(normais)
    
    def criar_visualizacao_individual(self, componente: Dict, orcamento_componente: Dict) -> go.Figure:
        """Criar visualização 3D de um componente individual com informações de custo"""
        
        vertices, faces, normais = self.criar_mesh_componente(componente)
        
        # Obter cor baseada no tipo
        cor = self.cores_tipos.get(componente['tipo'], '#8B4513')
        
        # Criar mesh 3D
        fig = go.Figure(data=[
            go.Mesh3d(
                x=vertices[:, 0],
                y=vertices[:, 1], 
                z=vertices[:, 2],
                i=faces[:, 0],
                j=faces[:, 1],
                k=faces[:, 2],
                color=cor,
                opacity=0.8,
                name=f"{componente['tipo']} - {componente.get('id', 'N/A')}",
                hovertemplate=(
                    f"<b>{componente['tipo']}</b><br>"
                    f"Dimensões: {componente['largura_m']:.2f} × {componente['altura_m']:.2f} × {componente['profundidade_m']:.2f}m<br>"
                    f"Área: {componente['area_m2']:.2f} m²<br>"
                    f"Custo: R$ {orcamento_componente.get('custo_total', 0):.2f}<br>"
                    "<extra></extra>"
                )
            )
        ])
        
        # Configurar layout
        fig.update_layout(
            title={
                'text': f"<b>{componente['tipo']}</b> - R$ {orcamento_componente.get('custo_total', 0):.2f}",
                'x': 0.5,
                'font': {'size': 16, 'family': 'Inter'}
            },
            scene=dict(
                xaxis_title="Largura (m)",
                yaxis_title="Altura (m)", 
                zaxis_title="Profundidade (m)",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                ),
                aspectmode='data'
            ),
            width=400,
            height=350,
            margin=dict(l=0, r=0, t=40, b=0),
            font=dict(family="Inter", size=12)
        )
        
        return fig
    
    def criar_visualizacao_conjunto(self, componentes: List[Dict], orcamentos: List[Dict]) -> go.Figure:
        """Criar visualização 3D do conjunto completo de móveis"""
        
        fig = go.Figure()
        
        # Posicionamento automático dos componentes
        posicao_x = 0
        espacamento = 0.1  # 10cm entre componentes
        
        for i, (comp, orc) in enumerate(zip(componentes, orcamentos)):
            vertices, faces, _ = self.criar_mesh_componente(comp)
            
            # Deslocar componente na posição X
            vertices[:, 0] += posicao_x
            
            # Cor baseada no custo (heatmap)
            custo = orc.get('custo_total', 0)
            cor = self._obter_cor_custo(custo, [o.get('custo_total', 0) for o in orcamentos])
            
            fig.add_trace(go.Mesh3d(
                x=vertices[:, 0],
                y=vertices[:, 1],
                z=vertices[:, 2],
                i=faces[:, 0],
                j=faces[:, 1],
                k=faces[:, 2],
                color=cor,
                opacity=0.8,
                name=f"{comp['tipo']} - R$ {custo:.2f}",
                hovertemplate=(
                    f"<b>{comp['tipo']}</b><br>"
                    f"Dimensões: {comp['largura_m']:.2f} × {comp['altura_m']:.2f} × {comp['profundidade_m']:.2f}m<br>"
                    f"Área: {comp['area_m2']:.2f} m²<br>"
                    f"Custo: R$ {custo:.2f}<br>"
                    "<extra></extra>"
                )
            ))
            
            # Atualizar posição para próximo componente
            posicao_x += comp['largura_m'] + espacamento
        
        # Configurar layout
        fig.update_layout(
            title={
                'text': "<b>Visualização Completa do Projeto</b>",
                'x': 0.5,
                'font': {'size': 18, 'family': 'Inter'}
            },
            scene=dict(
                xaxis_title="Posição (m)",
                yaxis_title="Altura (m)",
                zaxis_title="Profundidade (m)",
                camera=dict(
                    eye=dict(x=2, y=2, z=1.5)
                ),
                aspectmode='data'
            ),
            width=800,
            height=500,
            margin=dict(l=0, r=0, t=50, b=0),
            font=dict(family="Inter", size=12)
        )
        
        return fig
    
    def _obter_cor_custo(self, custo: float, todos_custos: List[float]) -> str:
        """Obter cor baseada no custo relativo (heatmap)"""
        if not todos_custos or max(todos_custos) == min(todos_custos):
            return '#8B4513'
        
        # Normalizar custo (0-1)
        custo_norm = (custo - min(todos_custos)) / (max(todos_custos) - min(todos_custos))
        
        # Escala de cores: verde (baixo) -> amarelo (médio) -> vermelho (alto)
        if custo_norm < 0.5:
            # Verde para amarelo
            r = int(255 * (custo_norm * 2))
            g = 255
            b = 0
        else:
            # Amarelo para vermelho
            r = 255
            g = int(255 * (2 - custo_norm * 2))
            b = 0
        
        return f'rgb({r},{g},{b})'
    
    def criar_dashboard_moveis(self, componentes: List[Dict], orcamentos: List[Dict]) -> None:
        """Criar dashboard completo com visualizações individuais e conjunto"""
        
        st.markdown("### 🎯 Visualização 3D dos Móveis")
        
        # Tabs para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "🔍 Móveis Individuais", "📈 Análise de Custos"])
        
        with tab1:
            st.markdown("#### 🏠 Projeto Completo")
            fig_conjunto = self.criar_visualizacao_conjunto(componentes, orcamentos)
            st.plotly_chart(fig_conjunto, use_container_width=True)
            
            # Resumo rápido
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🔧 Total de Móveis", len(componentes))
            with col2:
                custo_total = sum(orc.get('custo_total', 0) for orc in orcamentos)
                st.metric("💰 Custo Total", f"R$ {custo_total:.2f}")
            with col3:
                area_total = sum(comp['area_m2'] for comp in componentes)
                st.metric("📐 Área Total", f"{area_total:.2f} m²")
        
        with tab2:
            st.markdown("#### 🔍 Análise Individual dos Móveis")
            
            # Grid de visualizações individuais
            cols_per_row = 2
            for i in range(0, len(componentes), cols_per_row):
                cols = st.columns(cols_per_row)
                
                for j in range(cols_per_row):
                    idx = i + j
                    if idx < len(componentes):
                        with cols[j]:
                            comp = componentes[idx]
                            orc = orcamentos[idx]
                            
                            # Visualização 3D
                            fig_individual = self.criar_visualizacao_individual(comp, orc)
                            st.plotly_chart(fig_individual, use_container_width=True)
                            
                            # Detalhes do componente
                            with st.expander(f"📋 Detalhes - {comp['tipo']}"):
                                st.write(f"**Dimensões:** {comp['largura_m']:.2f} × {comp['altura_m']:.2f} × {comp['profundidade_m']:.2f}m")
                                st.write(f"**Área:** {comp['area_m2']:.2f} m²")
                                st.write(f"**Volume:** {comp.get('volume_m3', 0):.3f} m³")
                                st.write(f"**Custo:** R$ {orc.get('custo_total', 0):.2f}")
                                st.write(f"**Custo/m²:** R$ {orc.get('custo_total', 0) / comp['area_m2']:.2f}")
        
        with tab3:
            st.markdown("#### 📈 Análise de Custos por Móvel")
            
            # Criar DataFrame para análise
            df_analise = pd.DataFrame([
                {
                    'Móvel': comp['tipo'],
                    'ID': comp.get('id', f'Item {i+1}'),
                    'Área (m²)': comp['area_m2'],
                    'Custo Total (R$)': orc.get('custo_total', 0),
                    'Custo/m² (R$)': orc.get('custo_total', 0) / comp['area_m2'] if comp['area_m2'] > 0 else 0,
                    'Percentual do Total (%)': (orc.get('custo_total', 0) / sum(o.get('custo_total', 0) for o in orcamentos)) * 100 if sum(o.get('custo_total', 0) for o in orcamentos) > 0 else 0
                }
                for i, (comp, orc) in enumerate(zip(componentes, orcamentos))
            ])
            
            # Gráfico de barras - Custo por móvel
            fig_barras = px.bar(
                df_analise,
                x='Móvel',
                y='Custo Total (R$)',
                color='Custo Total (R$)',
                title="💰 Custo por Móvel",
                color_continuous_scale='RdYlGn_r'
            )
            fig_barras.update_layout(
                font_family="Inter",
                title_font_size=16
            )
            st.plotly_chart(fig_barras, use_container_width=True)
            
            # Gráfico de pizza - Distribuição de custos
            fig_pizza = px.pie(
                df_analise,
                values='Custo Total (R$)',
                names='Móvel',
                title="📊 Distribuição de Custos"
            )
            fig_pizza.update_layout(
                font_family="Inter",
                title_font_size=16
            )
            st.plotly_chart(fig_pizza, use_container_width=True)
            
            # Tabela detalhada
            st.markdown("#### 📋 Tabela Detalhada")
            st.dataframe(
                df_analise.round(2),
                use_container_width=True,
                hide_index=True
            )

# Instância global do visualizador
visualizador_3d = VisualizadorMoveis3D()

