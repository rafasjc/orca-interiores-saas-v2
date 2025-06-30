"""
Sistema de Atualização Automática de Preços da Léo Madeiras
Módulo profissional para aplicação SaaS de orçamento de marcenaria
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import time
import streamlit as st
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AtualizadorPrecos:
    """Sistema profissional de atualização automática de preços"""
    
    def __init__(self):
        self.base_url = "https://www.leomadeiras.com.br"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Cache de preços
        self.cache_file = Path("cache_precos_leo.json")
        self.cache_duration = timedelta(hours=6)  # Cache válido por 6 horas
        
        # URLs específicas para coleta
        self.urls_coleta = {
            'mdf': '/categoria/madeiras/mdf/',
            'compensados': '/categoria/madeiras/compensados/',
            'mdp': '/categoria/madeiras/mdp/'
        }
    
    def verificar_cache_valido(self) -> bool:
        """Verificar se o cache de preços ainda é válido"""
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            ultima_atualizacao = datetime.fromisoformat(cache_data.get('ultima_atualizacao', ''))
            return datetime.now() - ultima_atualizacao < self.cache_duration
        except:
            return False
    
    def carregar_cache(self) -> Optional[Dict]:
        """Carregar preços do cache"""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def salvar_cache(self, dados: Dict) -> None:
        """Salvar preços no cache"""
        dados['ultima_atualizacao'] = datetime.now().isoformat()
        
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
    
    def extrair_preco_produto(self, produto_html: BeautifulSoup) -> Optional[Tuple[str, float, str]]:
        """Extrair preço de um produto específico"""
        try:
            # Buscar nome do produto
            nome_elem = produto_html.find(['h2', 'h3', 'div'], class_=re.compile(r'.*nome.*|.*title.*|.*produto.*', re.I))
            if not nome_elem:
                nome_elem = produto_html.find('a', href=re.compile(r'/p/'))
            
            nome = nome_elem.get_text(strip=True) if nome_elem else "Produto"
            
            # Buscar preço
            preco_elem = produto_html.find(['span', 'div'], string=re.compile(r'R\$\s*[\d,\.]+'))
            if not preco_elem:
                preco_elem = produto_html.find(['span', 'div'], class_=re.compile(r'.*preco.*|.*price.*', re.I))
            
            if preco_elem:
                preco_text = preco_elem.get_text(strip=True)
                # Extrair valor numérico
                preco_match = re.search(r'R\$\s*([\d,\.]+)', preco_text)
                if preco_match:
                    preco_str = preco_match.group(1).replace('.', '').replace(',', '.')
                    preco = float(preco_str)
                    
                    # Extrair dimensões se disponível
                    dimensoes = self._extrair_dimensoes(nome)
                    
                    return nome, preco, dimensoes
        except Exception as e:
            logger.warning(f"Erro ao extrair preço: {e}")
        
        return None
    
    def _extrair_dimensoes(self, nome: str) -> str:
        """Extrair dimensões do nome do produto"""
        # Padrões comuns: 15mm, 2750x1840mm, etc.
        dimensoes_match = re.search(r'(\d+mm|\d+x\d+mm|\d+\.\d+x\d+\.\d+)', nome, re.I)
        return dimensoes_match.group(1) if dimensoes_match else ""
    
    def coletar_precos_categoria(self, categoria: str, url_path: str) -> List[Dict]:
        """Coletar preços de uma categoria específica"""
        precos = []
        
        try:
            url = f"{self.base_url}{url_path}"
            logger.info(f"Coletando preços de {categoria}: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar produtos na página
            produtos = soup.find_all(['div', 'article'], class_=re.compile(r'.*produto.*|.*item.*|.*card.*', re.I))
            
            if not produtos:
                # Fallback: buscar por links de produtos
                produtos = soup.find_all('a', href=re.compile(r'/p/\d+/'))
                produtos = [link.parent for link in produtos if link.parent]
            
            logger.info(f"Encontrados {len(produtos)} produtos em {categoria}")
            
            for produto in produtos[:10]:  # Limitar a 10 produtos por categoria
                resultado = self.extrair_preco_produto(produto)
                if resultado:
                    nome, preco, dimensoes = resultado
                    
                    # Calcular preço por m² se possível
                    preco_m2 = self._calcular_preco_m2(preco, dimensoes, nome)
                    
                    precos.append({
                        'categoria': categoria,
                        'nome': nome,
                        'preco': preco,
                        'dimensoes': dimensoes,
                        'preco_m2': preco_m2,
                        'url': url,
                        'data_coleta': datetime.now().isoformat()
                    })
                
                # Delay para não sobrecarregar o servidor
                time.sleep(0.5)
        
        except Exception as e:
            logger.error(f"Erro ao coletar preços de {categoria}: {e}")
        
        return precos
    
    def _calcular_preco_m2(self, preco: float, dimensoes: str, nome: str) -> Optional[float]:
        """Calcular preço por m² baseado nas dimensões"""
        try:
            # Padrão: 2750x1840mm
            match = re.search(r'(\d+)x(\d+)mm', dimensoes)
            if match:
                largura_mm = int(match.group(1))
                altura_mm = int(match.group(2))
                area_m2 = (largura_mm * altura_mm) / 1_000_000  # Converter mm² para m²
                return round(preco / area_m2, 2) if area_m2 > 0 else None
            
            # Padrão alternativo no nome
            match = re.search(r'(\d+\.\d+)x(\d+\.\d+)', nome)
            if match:
                largura_m = float(match.group(1))
                altura_m = float(match.group(2))
                area_m2 = largura_m * altura_m
                return round(preco / area_m2, 2) if area_m2 > 0 else None
        
        except Exception as e:
            logger.warning(f"Erro ao calcular preço/m²: {e}")
        
        return None
    
    def atualizar_precos_completo(self) -> Dict:
        """Atualizar todos os preços da Léo Madeiras"""
        logger.info("Iniciando atualização completa de preços...")
        
        todos_precos = []
        
        for categoria, url_path in self.urls_coleta.items():
            precos_categoria = self.coletar_precos_categoria(categoria, url_path)
            todos_precos.extend(precos_categoria)
            
            # Delay entre categorias
            time.sleep(2)
        
        # Processar e organizar preços
        precos_organizados = self._organizar_precos(todos_precos)
        
        # Salvar no cache
        dados_cache = {
            'precos_raw': todos_precos,
            'precos_organizados': precos_organizados,
            'total_produtos': len(todos_precos),
            'categorias_coletadas': list(self.urls_coleta.keys()),
            'status': 'sucesso'
        }
        
        self.salvar_cache(dados_cache)
        
        logger.info(f"Atualização concluída: {len(todos_precos)} produtos coletados")
        return dados_cache
    
    def _organizar_precos(self, precos_raw: List[Dict]) -> Dict:
        """Organizar preços por tipo de material"""
        organizados = {
            'mdf_15mm': [],
            'mdf_18mm': [],
            'compensado_15mm': [],
            'compensado_10mm': [],
            'mdp_15mm': [],
            'melamina_15mm': []
        }
        
        for item in precos_raw:
            nome = item['nome'].lower()
            categoria = item['categoria']
            
            # Classificar por tipo e espessura
            if 'mdf' in categoria or 'mdf' in nome:
                if '15mm' in nome:
                    organizados['mdf_15mm'].append(item)
                elif '18mm' in nome:
                    organizados['mdf_18mm'].append(item)
            
            elif 'compensado' in categoria or 'compensado' in nome:
                if '15mm' in nome:
                    organizados['compensado_15mm'].append(item)
                elif '10mm' in nome:
                    organizados['compensado_10mm'].append(item)
            
            elif 'mdp' in categoria or 'mdp' in nome:
                organizados['mdp_15mm'].append(item)
            
            elif 'melamina' in nome or 'melaminico' in nome:
                organizados['melamina_15mm'].append(item)
        
        return organizados
    
    def obter_precos_atualizados(self, forcar_atualizacao: bool = False) -> Dict:
        """Obter preços atualizados (usa cache se válido)"""
        
        if not forcar_atualizacao and self.verificar_cache_valido():
            logger.info("Usando preços do cache")
            return self.carregar_cache()
        
        logger.info("Cache inválido ou forçando atualização")
        return self.atualizar_precos_completo()
    
    def obter_preco_medio_categoria(self, categoria: str) -> Optional[float]:
        """Obter preço médio por m² de uma categoria"""
        dados = self.obter_precos_atualizados()
        
        if 'precos_organizados' not in dados:
            return None
        
        precos_categoria = dados['precos_organizados'].get(categoria, [])
        precos_m2_validos = [item['preco_m2'] for item in precos_categoria if item.get('preco_m2')]
        
        if precos_m2_validos:
            return round(sum(precos_m2_validos) / len(precos_m2_validos), 2)
        
        return None
    
    def criar_interface_atualizacao(self) -> None:
        """Criar interface Streamlit para atualização de preços"""
        st.markdown("### 🔄 Atualização de Preços")
        
        # Status atual
        dados_cache = self.carregar_cache()
        
        if dados_cache:
            ultima_atualizacao = datetime.fromisoformat(dados_cache['ultima_atualizacao'])
            tempo_desde_atualizacao = datetime.now() - ultima_atualizacao
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "📅 Última Atualização",
                    ultima_atualizacao.strftime("%d/%m/%Y %H:%M"),
                    delta=f"{tempo_desde_atualizacao.total_seconds() / 3600:.1f}h atrás"
                )
            
            with col2:
                st.metric(
                    "📦 Produtos Coletados",
                    dados_cache.get('total_produtos', 0)
                )
            
            with col3:
                cache_valido = self.verificar_cache_valido()
                st.metric(
                    "✅ Status",
                    "Atualizado" if cache_valido else "Desatualizado",
                    delta="Cache válido" if cache_valido else "Precisa atualizar"
                )
        else:
            st.warning("⚠️ Nenhuma atualização de preços encontrada")
        
        # Botões de ação
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Atualizar Preços", type="primary"):
                with st.spinner("Coletando preços da Léo Madeiras..."):
                    try:
                        dados = self.atualizar_precos_completo()
                        st.success(f"✅ Preços atualizados! {dados['total_produtos']} produtos coletados")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro na atualização: {e}")
        
        with col2:
            if st.button("📊 Ver Preços Coletados"):
                if dados_cache and 'precos_raw' in dados_cache:
                    st.markdown("#### 📋 Preços Coletados")
                    
                    # Criar DataFrame para exibição
                    import pandas as pd
                    df = pd.DataFrame(dados_cache['precos_raw'])
                    
                    if not df.empty:
                        # Filtros
                        categorias = df['categoria'].unique()
                        categoria_selecionada = st.selectbox("Filtrar por categoria:", ['Todas'] + list(categorias))
                        
                        if categoria_selecionada != 'Todas':
                            df = df[df['categoria'] == categoria_selecionada]
                        
                        # Exibir tabela
                        st.dataframe(
                            df[['categoria', 'nome', 'preco', 'preco_m2', 'dimensoes']].round(2),
                            use_container_width=True
                        )
                    else:
                        st.info("Nenhum preço encontrado")
                else:
                    st.warning("Nenhum dado de preços disponível")

# Instância global do atualizador
atualizador_precos = AtualizadorPrecos()

