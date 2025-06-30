import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import os
import tempfile
import json
import time

# Importar módulos customizados
from parser_3d import parser_3d
from orcamento import sistema_orcamento
from visualizador_3d import visualizador_3d
from atualizador_precos import atualizador_precos
from auth_system import sistema_auth

# Configuração da página
st.set_page_config(
    page_title="🏠 Orça Interiores",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para design Apple-level
st.markdown("""
<style>
    /* Importar fonte Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Reset e configurações globais */
    .main {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 400;
    }
    
    /* Cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    
    /* Upload area */
    .upload-section {
        background: #f8fafc;
        border: 2px dashed #cbd5e0;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    /* Botões */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* Métricas */
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    /* Alertas */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Tabelas */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    /* File uploader */
    .stFileUploader {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        border: 2px dashed #cbd5e0;
    }
    
    /* Esconder elementos do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Funções auxiliares
def format_currency(value):
    """Formatar valor em moeda brasileira"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_size(bytes_size):
    """Formatar tamanho de arquivo"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def analyze_3d_file(file_content, filename):
    """Analisar arquivo 3D usando o parser avançado"""
    return parser_3d.analisar_arquivo(file_content, filename)

def calcular_orcamento(analise, 
                      tipo_material='mdf_15mm',
                      qualidade_acessorios='comum', 
                      complexidade_mao_obra='media',
                      margem_lucro=0.3):
    """Calcular orçamento usando o sistema avançado com preços da Léo Madeiras"""
    if not analise['sucesso']:
        return None
    
    # Configurações para o novo sistema
    configuracoes = {
        'tipo_material': tipo_material.lower().replace(' ', '_'),
        'qualidade_acessorios': qualidade_acessorios.lower(),
        'complexidade': complexidade_mao_obra.lower(),
        'margem_lucro': margem_lucro
    }
    
    return sistema_orcamento.gerar_orcamento_completo(
        analise['componentes'], 
        configuracoes
    )

# Interface principal
def main():
    # Verificar autenticação
    usuario = sistema_auth.criar_interface_login()
    
    if not usuario:
        # Mostrar página de marketing para usuários não logados
        mostrar_pagina_marketing()
        return
    
    # Usuário logado - mostrar aplicação completa
    mostrar_aplicacao_principal(usuario)

def mostrar_pagina_marketing():
    """Página de marketing para usuários não logados"""
    # Header principal
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #667eea; font-size: 3rem; margin-bottom: 0.5rem;'>
            🏠 Orça Interiores
        </h1>
        <h3 style='color: #764ba2; margin-bottom: 2rem;'>
            Análise automática de projetos 3D para orçamento de marcenaria
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Benefícios principais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🎯 Análise Automática
        Upload de arquivos 3D e análise instantânea de componentes de marcenaria
        """)
    
    with col2:
        st.markdown("""
        ### 💰 Preços Atualizados
        Integração com fornecedores para preços sempre atualizados
        """)
    
    with col3:
        st.markdown("""
        ### 📊 Visualização 3D
        Veja cada móvel individualmente com seus custos detalhados
        """)
    
    # Planos de assinatura
    sistema_auth.criar_interface_planos()

def mostrar_aplicacao_principal(usuario: Dict):
    """Aplicação principal para usuários logados"""
    
    # Dashboard do usuário na sidebar
    with st.sidebar:
        sistema_auth.criar_dashboard_usuario(usuario)
    
    # Verificar limite de projetos
    if not sistema_auth.verificar_limite_projetos(usuario['id']):
        st.error("🚫 Limite de projetos mensais atingido. Faça upgrade do seu plano!")
        sistema_auth.criar_interface_planos()
        return
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🏠 Orça Interiores</h1>
        <p>Análise automática de projetos 3D para orçamento de marcenaria</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Configurações")
        
        # Configurações de orçamento
        st.markdown("#### 💰 Orçamento")
        margem_lucro = st.slider(
            "Margem de Lucro (%)",
            min_value=10,
            max_value=50,
            value=30,
            step=5
        ) / 100
        
        # Configurações de material
        st.markdown("#### 🪵 Material")
        tipo_material = st.selectbox(
            "Tipo de Material",
            ["mdf_15mm", "mdf_18mm", "compensado_15mm", "compensado_18mm", "melamina_15mm", "melamina_18mm"],
            format_func=lambda x: x.replace('_', ' ').upper()
        )
        
        # Configurações de acessórios
        st.markdown("#### 🔧 Acessórios")
        qualidade_acessorios = st.selectbox(
            "Qualidade dos Acessórios",
            ["comum", "premium"],
            format_func=lambda x: x.title()
        )
        
        # Configurações de mão de obra
        st.markdown("#### 👷 Mão de Obra")
        complexidade_mao_obra = st.selectbox(
            "Complexidade do Projeto",
            ["simples", "media", "complexa", "premium"],
            index=1,
            format_func=lambda x: x.replace('media', 'média').title()
        )
        
        # Informações do projeto
        st.markdown("#### 📋 Projeto")
        cliente_nome = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
        ambiente = st.selectbox(
            "Ambiente",
            ["Cozinha", "Quarto", "Sala", "Banheiro", "Escritório", "Closet", "Lavanderia", "Outro"]
        )
        
        # Estatísticas
        st.markdown("#### 📊 Estatísticas")
        if 'projetos_analisados' not in st.session_state:
            st.session_state.projetos_analisados = 0
        
        st.metric("Projetos Analisados", st.session_state.projetos_analisados)
        
        # Informações
        st.markdown("#### ℹ️ Formatos Suportados")
        st.info("""
        **Formatos aceitos:**
        - OBJ (recomendado)
        - DAE (COLLADA)
        - STL
        - PLY
        
        **Tamanho máximo:** 500MB
        """)
        
        # Preços atuais da Léo Madeiras
        st.markdown("#### 💵 Preços Léo Madeiras")
        with st.expander("Ver preços atuais"):
            st.write("**Materiais (por m²):**")
            st.write("• MDF 15mm: R$ 69,15")
            st.write("• MDF 18mm: R$ 77,85")
            st.write("• Compensado 15mm: R$ 64,00")
            st.write("• Compensado 10mm: R$ 52,50")
            st.write("• Melamina 15mm: R$ 89,50")
            
            st.write("**Acessórios:**")
            st.write("• Dobradiça comum: R$ 12,50")
            st.write("• Puxador simples: R$ 15,80")
            st.write("• Corrediça comum: R$ 45,00")
            
            st.write("**Mão de obra: R$ 120,00/m² base**")
            st.write("**Corte: R$ 2,50/metro linear**")
            
            st.caption("🔗 Fonte: [Léo Madeiras](https://www.leomadeiras.com.br/) - Atualizado em 30/06/2025")
        
        # Sistema de atualização de preços
        st.markdown("#### 🔄 Atualização de Preços")
        with st.expander("Gerenciar preços"):
            atualizador_precos.criar_interface_atualizacao()
    
    # Área principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📁 Upload de Arquivo 3D")
        
        # Upload de arquivo
        uploaded_file = st.file_uploader(
            "Selecione seu arquivo 3D",
            type=['obj', 'dae', 'stl', 'ply'],
            help="Arraste e solte ou clique para selecionar"
        )
        
        if uploaded_file is not None:
            # Informações do arquivo
            file_size = len(uploaded_file.getvalue())
            
            st.success(f"✅ Arquivo carregado: **{uploaded_file.name}**")
            
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.metric("📄 Nome", uploaded_file.name)
            with col_info2:
                st.metric("📏 Tamanho", format_size(file_size))
            with col_info3:
                st.metric("🔧 Formato", uploaded_file.name.split('.')[-1].upper())
            
            # Botão de análise
            if st.button("🚀 Analisar Projeto", type="primary"):
                with st.spinner("🔍 Analisando arquivo 3D..."):
                    # Simular tempo de processamento
                    import time
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.02)
                        progress_bar.progress(i + 1)
                    
                    # Analisar arquivo
                    file_content = uploaded_file.getvalue()
                    analise = analyze_3d_file(file_content, uploaded_file.name)
                    
                    if analise['sucesso']:
                        # Calcular orçamento com configurações avançadas
                        orcamento = calcular_orcamento(
                            analise, 
                            tipo_material=tipo_material,
                            qualidade_acessorios=qualidade_acessorios,
                            complexidade_mao_obra=complexidade_mao_obra,
                            margem_lucro=margem_lucro
                        )
                        
                        if orcamento:
                            # Incrementar contador de projetos
                            sistema_auth.incrementar_contador_projetos(usuario['id'])
                            
                            # Salvar no session state
                            st.session_state.ultima_analise = analise
                            st.session_state.ultimo_orcamento = orcamento
                            st.session_state.projetos_analisados += 1
                            
                            st.success(f"✅ Análise concluída em {analise['tempo_processamento']:.1f}s!")
                            st.rerun()
                        else:
                            st.error("❌ Erro no cálculo do orçamento")
                    else:
                        st.error(f"❌ Erro na análise: {analise['erro']}")
    
    with col2:
        st.markdown("### 📊 Resumo Rápido")
        
        if 'ultima_analise' in st.session_state and 'ultimo_orcamento' in st.session_state:
            analise = st.session_state.ultima_analise
            orcamento = st.session_state.ultimo_orcamento
            
            # Métricas principais
            st.metric(
                "🔧 Componentes",
                analise['componentes_detectados'],
                help="Número de componentes detectados"
            )
            
            st.metric(
                "📐 Área Total",
                f"{analise['area_total_m2']} m²",
                help="Área total do projeto"
            )
            
            st.metric(
                "💰 Valor Final",
                format_currency(orcamento['resumo']['valor_final']),
                help="Valor total do orçamento"
            )
            
            st.metric(
                "💵 Valor/m²",
                format_currency(orcamento['resumo']['valor_por_m2']),
                help="Valor por metro quadrado"
            )
        else:
            st.info("📤 Faça upload de um arquivo 3D para ver o resumo")
    
    # Resultados detalhados
    if 'ultima_analise' in st.session_state and 'ultimo_orcamento' in st.session_state:
        st.markdown("---")
        st.markdown("## 📋 Resultados Detalhados")
        
        analise = st.session_state.ultima_analise
        orcamento = st.session_state.ultimo_orcamento
                # Tabs para diferentes visualizações
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Resumo", "💰 Orçamento", "🎯 Visualização 3D", "📈 Gráficos", "📄 Relatório"])        
        with tab1:
            st.markdown("### 🔍 Análise dos Componentes")
            
            # Criar DataFrame dos componentes
            df_componentes = pd.DataFrame(analise['componentes'])
            
            # Formatação das colunas
            df_display = df_componentes.copy()
            df_display['Confiança'] = df_display['confianca'].apply(lambda x: f"{x:.1%}")
            df_display = df_display[['tipo', 'largura_m', 'altura_m', 'profundidade_m', 'area_m2', 'Confiança']]
            df_display.columns = ['Tipo', 'Largura (m)', 'Altura (m)', 'Profundidade (m)', 'Área (m²)', 'Confiança']
            
            st.dataframe(df_display, use_container_width=True)
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📦 Total de Componentes", len(analise['componentes']))
            with col2:
                st.metric("📐 Área Total", f"{analise['area_total_m2']} m²")
            with col3:
                st.metric("📊 Volume Total", f"{analise['volume_total_m3']} m³")
        
        with tab2:
            st.markdown("### 💰 Orçamento Detalhado")
            
            # Resumo financeiro
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "🪵 Materiais",
                    format_currency(orcamento['resumo']['subtotal_materiais'])
                )
            
            with col2:
                st.metric(
                    "🔧 Acessórios",
                    format_currency(orcamento['resumo']['subtotal_acessorios'])
                )
            
            with col3:
                st.metric(
                    "👷 Mão de Obra",
                    format_currency(orcamento['resumo']['subtotal_mao_obra'])
                )
            
            with col4:
                st.metric(
                    "💰 Total",
                    format_currency(orcamento['resumo']['valor_final']),
                    delta=f"+{orcamento['configuracoes']['margem_lucro']:.0%} margem"
                )
            
            # Detalhamento
            st.markdown("#### 📋 Detalhamento")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🪵 Materiais:**")
                mat = orcamento['materiais']
                st.write(f"• {mat['tipo_material'].replace('_', ' ').upper()}: {mat['area_com_desperdicio_m2']} m² × {format_currency(mat['preco_m2'])}/m²")
                st.write(f"• Desperdício: {mat['desperdicio_percentual']:.0%}")
                st.write(f"• **Total:** {format_currency(mat['custo_total'])}")
                
                st.markdown("**👷 Mão de Obra:**")
                mao = orcamento['mao_obra']
                st.write(f"• Área: {mao['area_m2']} m² × {format_currency(mao['custo_base']/mao['area_m2'] if mao['area_m2'] > 0 else 0)}/m²")
                st.write(f"• Complexidade: {mao['complexidade'].title()}")
                st.write(f"• **Total:** {format_currency(mao['custo_total'])}")
            
            with col2:
                st.markdown("**🔧 Acessórios:**")
                acess = orcamento['acessorios']
                st.write(f"• Qualidade: {acess['qualidade'].title()}")
                
                if acess['itens']:
                    for item, dados in acess['itens'].items():
                        nome_item = item.replace('_', ' ').title()
                        st.write(f"• {nome_item}: {dados['quantidade']} un × {format_currency(dados['preco_unitario'])}")
                else:
                    st.write("• Nenhum acessório detectado")
                    
                st.write(f"• **Total:** {format_currency(acess['custo_total'])}")
                
                st.markdown("**✂️ Corte e Usinagem:**")
                corte = orcamento['corte']
                st.write(f"• {corte['descricao']}")
                st.write(f"• Peças: {corte['componentes_processados']}")
                st.write(f"• **Total:** {format_currency(corte['custo_total'])}")
        
        with tab3:
            # Verificar acesso à visualização 3D
            if not sistema_auth.verificar_funcionalidade(usuario['plano'], 'visualizacao_3d'):
                st.warning("🔒 Visualização 3D disponível apenas nos planos Básico, Profissional e Empresarial")
                sistema_auth.criar_interface_planos()
                return
            
            st.markdown("### 🎯 Visualização 3D dos Móveis")
            
            # Criar visualização 3D usando os custos individuais
            if 'custos_individuais' in orcamento:
                visualizador_3d.criar_dashboard_moveis(
                    analise['componentes'], 
                    orcamento['custos_individuais']
                )
            else:
                st.warning("⚠️ Custos individuais não disponíveis. Atualize a análise.")
        
        with tab4:
            st.markdown("### 📊 Visualizações")
            
            # Gráfico de distribuição de custos
            custos = [
                orcamento['resumo']['subtotal_materiais'],
                orcamento['resumo']['subtotal_acessorios'],
                orcamento['resumo']['subtotal_mao_obra']
            ]
            labels = ['Materiais', 'Acessórios', 'Mão de Obra']
            
            fig_pie = px.pie(
                values=custos,
                names=labels,
                title="Distribuição de Custos",
                color_discrete_sequence=['#667eea', '#764ba2', '#f093fb']
            )
            fig_pie.update_layout(
                font_family="Inter",
                title_font_size=20,
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Gráfico de componentes por tipo
            tipos_count = pd.DataFrame(analise['componentes'])['tipo'].value_counts()
            
            fig_bar = px.bar(
                x=tipos_count.index,
                y=tipos_count.values,
                title="Componentes por Tipo",
                labels={'x': 'Tipo de Componente', 'y': 'Quantidade'},
                color=tipos_count.values,
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(
                font_family="Inter",
                title_font_size=20,
                showlegend=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with tab5:
            st.markdown("### 📄 Relatório do Projeto")
            
            # Informações do projeto
            st.markdown(f"""
            **📋 Informações do Projeto**
            - **Cliente:** {cliente_nome or 'Não informado'}
            - **Ambiente:** {ambiente}
            - **Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
            - **Arquivo:** {uploaded_file.name if 'uploaded_file' in locals() and uploaded_file else 'N/A'}
            
            **🔍 Resumo da Análise**
            - **Componentes detectados:** {analise['componentes_detectados']}
            - **Área total:** {analise['area_total_m2']} m²
            - **Volume total:** {analise['volume_total_m3']} m³
            - **Tempo de processamento:** {analise['tempo_processamento']:.1f}s
            
            **💰 Resumo Financeiro**
            - **Materiais:** {format_currency(orcamento['resumo']['subtotal_materiais'])}
            - **Acessórios:** {format_currency(orcamento['resumo']['subtotal_acessorios'])}
            - **Mão de obra:** {format_currency(orcamento['resumo']['subtotal_mao_obra'])}
            - **Margem de lucro:** {orcamento['configuracoes']['margem_lucro']:.0%}
            - **Valor final:** {format_currency(orcamento['resumo']['valor_final'])}
            - **Valor por m²:** {format_currency(orcamento['resumo']['valor_por_m2'])}
            """)
            
            # Botão para download do relatório
            relatorio_json = {
                'projeto': {
                    'cliente': cliente_nome,
                    'ambiente': ambiente,
                    'data': datetime.now().isoformat(),
                    'arquivo': uploaded_file.name if 'uploaded_file' in locals() and uploaded_file else None
                },
                'analise': analise,
                'orcamento': orcamento
            }
            
            st.download_button(
                label="📥 Baixar Relatório (JSON)",
                data=json.dumps(relatorio_json, indent=2, ensure_ascii=False),
                file_name=f"orcamento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()

