"""
Sistema de Autenticação e Assinaturas SaaS
Módulo profissional para aplicação de orçamento de marcenaria
"""

import streamlit as st
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import uuid
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SistemaAuth:
    """Sistema completo de autenticação e assinaturas"""
    
    def __init__(self):
        self.db_path = Path("usuarios.db")
        self.init_database()
        
        # Planos de assinatura
        self.planos = {
            'free': {
                'nome': 'Gratuito',
                'preco': 0,
                'limite_projetos_mes': 3,
                'visualizacao_3d': False,
                'atualizacao_precos': False,
                'exportacao_pdf': False,
                'suporte': 'Comunidade'
            },
            'basic': {
                'nome': 'Básico',
                'preco': 49.90,
                'limite_projetos_mes': 50,
                'visualizacao_3d': True,
                'atualizacao_precos': True,
                'exportacao_pdf': True,
                'suporte': 'Email'
            },
            'pro': {
                'nome': 'Profissional',
                'preco': 99.90,
                'limite_projetos_mes': 200,
                'visualizacao_3d': True,
                'atualizacao_precos': True,
                'exportacao_pdf': True,
                'suporte': 'WhatsApp + Email',
                'api_access': True,
                'white_label': True
            },
            'enterprise': {
                'nome': 'Empresarial',
                'preco': 299.90,
                'limite_projetos_mes': -1,  # Ilimitado
                'visualizacao_3d': True,
                'atualizacao_precos': True,
                'exportacao_pdf': True,
                'suporte': 'Dedicado',
                'api_access': True,
                'white_label': True,
                'multi_usuarios': True,
                'integracao_personalizada': True
            }
        }
    
    def init_database(self):
        """Inicializar banco de dados SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                senha_hash TEXT NOT NULL,
                plano TEXT DEFAULT 'free',
                data_criacao TEXT NOT NULL,
                data_ultimo_login TEXT,
                ativo BOOLEAN DEFAULT 1,
                projetos_mes_atual INTEGER DEFAULT 0,
                data_reset_projetos TEXT
            )
        ''')
        
        # Tabela de assinaturas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assinaturas (
                id TEXT PRIMARY KEY,
                usuario_id TEXT NOT NULL,
                plano TEXT NOT NULL,
                status TEXT NOT NULL,
                data_inicio TEXT NOT NULL,
                data_fim TEXT NOT NULL,
                valor REAL NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabela de projetos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projetos (
                id TEXT PRIMARY KEY,
                usuario_id TEXT NOT NULL,
                nome TEXT NOT NULL,
                data_criacao TEXT NOT NULL,
                dados_projeto TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_senha(self, senha: str) -> str:
        """Criar hash seguro da senha"""
        return hashlib.sha256(senha.encode()).hexdigest()
    
    def criar_usuario(self, email: str, nome: str, senha: str) -> bool:
        """Criar novo usuário"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            usuario_id = str(uuid.uuid4())
            senha_hash = self.hash_senha(senha)
            data_criacao = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO usuarios (id, email, nome, senha_hash, data_criacao, data_reset_projetos)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (usuario_id, email, nome, senha_hash, data_criacao, data_criacao))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Usuário criado: {email}")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"Email já existe: {email}")
            return False
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {e}")
            return False
    
    def autenticar_usuario(self, email: str, senha: str) -> Optional[Dict]:
        """Autenticar usuário"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            senha_hash = self.hash_senha(senha)
            
            cursor.execute('''
                SELECT id, email, nome, plano, projetos_mes_atual, data_reset_projetos
                FROM usuarios 
                WHERE email = ? AND senha_hash = ? AND ativo = 1
            ''', (email, senha_hash))
            
            resultado = cursor.fetchone()
            
            if resultado:
                # Atualizar último login
                cursor.execute('''
                    UPDATE usuarios SET data_ultimo_login = ? WHERE id = ?
                ''', (datetime.now().isoformat(), resultado[0]))
                
                conn.commit()
                
                usuario = {
                    'id': resultado[0],
                    'email': resultado[1],
                    'nome': resultado[2],
                    'plano': resultado[3],
                    'projetos_mes_atual': resultado[4],
                    'data_reset_projetos': resultado[5]
                }
                
                # Verificar se precisa resetar contador de projetos
                self._verificar_reset_projetos(usuario['id'])
                
                conn.close()
                logger.info(f"Login realizado: {email}")
                return usuario
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            return None
    
    def _verificar_reset_projetos(self, usuario_id: str):
        """Verificar se deve resetar contador de projetos mensais"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT data_reset_projetos FROM usuarios WHERE id = ?
            ''', (usuario_id,))
            
            resultado = cursor.fetchone()
            if resultado:
                data_reset = datetime.fromisoformat(resultado[0])
                agora = datetime.now()
                
                # Se passou um mês, resetar contador
                if agora.month != data_reset.month or agora.year != data_reset.year:
                    cursor.execute('''
                        UPDATE usuarios 
                        SET projetos_mes_atual = 0, data_reset_projetos = ?
                        WHERE id = ?
                    ''', (agora.isoformat(), usuario_id))
                    
                    conn.commit()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao verificar reset de projetos: {e}")
    
    def verificar_limite_projetos(self, usuario_id: str) -> bool:
        """Verificar se usuário pode criar mais projetos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT plano, projetos_mes_atual FROM usuarios WHERE id = ?
            ''', (usuario_id,))
            
            resultado = cursor.fetchone()
            conn.close()
            
            if resultado:
                plano, projetos_atual = resultado
                limite = self.planos[plano]['limite_projetos_mes']
                
                # -1 significa ilimitado
                if limite == -1:
                    return True
                
                return projetos_atual < limite
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar limite: {e}")
            return False
    
    def incrementar_contador_projetos(self, usuario_id: str):
        """Incrementar contador de projetos do usuário"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE usuarios 
                SET projetos_mes_atual = projetos_mes_atual + 1
                WHERE id = ?
            ''', (usuario_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao incrementar contador: {e}")
    
    def verificar_funcionalidade(self, usuario_plano: str, funcionalidade: str) -> bool:
        """Verificar se usuário tem acesso a funcionalidade"""
        return self.planos.get(usuario_plano, {}).get(funcionalidade, False)
    
    def criar_interface_login(self) -> Optional[Dict]:
        """Criar interface de login/registro"""
        
        if 'usuario_logado' in st.session_state:
            return st.session_state.usuario_logado
        
        st.markdown("### 🔐 Acesso ao Sistema")
        
        tab_login, tab_registro = st.tabs(["🚪 Login", "📝 Criar Conta"])
        
        with tab_login:
            with st.form("form_login"):
                st.markdown("#### Fazer Login")
                email = st.text_input("📧 Email")
                senha = st.text_input("🔒 Senha", type="password")
                
                if st.form_submit_button("🚀 Entrar", type="primary"):
                    if email and senha:
                        usuario = self.autenticar_usuario(email, senha)
                        if usuario:
                            st.session_state.usuario_logado = usuario
                            st.success("✅ Login realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Email ou senha incorretos")
                    else:
                        st.error("⚠️ Preencha todos os campos")
        
        with tab_registro:
            with st.form("form_registro"):
                st.markdown("#### Criar Nova Conta")
                nome = st.text_input("👤 Nome Completo")
                email = st.text_input("📧 Email")
                senha = st.text_input("🔒 Senha", type="password")
                confirmar_senha = st.text_input("🔒 Confirmar Senha", type="password")
                
                aceitar_termos = st.checkbox("Aceito os termos de uso e política de privacidade")
                
                if st.form_submit_button("✨ Criar Conta", type="primary"):
                    if not all([nome, email, senha, confirmar_senha]):
                        st.error("⚠️ Preencha todos os campos")
                    elif senha != confirmar_senha:
                        st.error("❌ Senhas não coincidem")
                    elif len(senha) < 6:
                        st.error("❌ Senha deve ter pelo menos 6 caracteres")
                    elif not aceitar_termos:
                        st.error("⚠️ Aceite os termos para continuar")
                    else:
                        if self.criar_usuario(email, nome, senha):
                            st.success("✅ Conta criada com sucesso! Faça login para continuar.")
                        else:
                            st.error("❌ Email já cadastrado ou erro interno")
        
        return None
    
    def criar_interface_planos(self):
        """Criar interface de planos de assinatura"""
        st.markdown("### 💎 Planos de Assinatura")
        
        cols = st.columns(len(self.planos))
        
        for i, (plano_id, plano) in enumerate(self.planos.items()):
            with cols[i]:
                # Destacar plano recomendado
                if plano_id == 'pro':
                    st.markdown("🌟 **RECOMENDADO**")
                
                st.markdown(f"#### {plano['nome']}")
                
                if plano['preco'] == 0:
                    st.markdown("### 🆓 Gratuito")
                else:
                    st.markdown(f"### R$ {plano['preco']:.2f}/mês")
                
                # Funcionalidades
                st.markdown("**Funcionalidades:**")
                
                limite = plano['limite_projetos_mes']
                if limite == -1:
                    st.write("✅ Projetos ilimitados")
                else:
                    st.write(f"✅ {limite} projetos/mês")
                
                if plano.get('visualizacao_3d'):
                    st.write("✅ Visualização 3D")
                else:
                    st.write("❌ Visualização 3D")
                
                if plano.get('atualizacao_precos'):
                    st.write("✅ Preços atualizados")
                else:
                    st.write("❌ Preços atualizados")
                
                if plano.get('exportacao_pdf'):
                    st.write("✅ Exportação PDF")
                else:
                    st.write("❌ Exportação PDF")
                
                st.write(f"🎧 Suporte: {plano['suporte']}")
                
                # Funcionalidades premium
                if plano.get('api_access'):
                    st.write("✅ Acesso API")
                if plano.get('white_label'):
                    st.write("✅ White Label")
                if plano.get('multi_usuarios'):
                    st.write("✅ Multi-usuários")
                
                # Botão de ação
                if plano_id == 'free':
                    st.button("🚀 Começar Grátis", key=f"btn_{plano_id}")
                else:
                    st.button(f"💳 Assinar por R$ {plano['preco']:.2f}", key=f"btn_{plano_id}")
    
    def criar_dashboard_usuario(self, usuario: Dict):
        """Criar dashboard do usuário logado"""
        st.markdown("### 👤 Minha Conta")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📧 Email", usuario['email'])
        
        with col2:
            plano_nome = self.planos[usuario['plano']]['nome']
            st.metric("💎 Plano", plano_nome)
        
        with col3:
            limite = self.planos[usuario['plano']]['limite_projetos_mes']
            if limite == -1:
                st.metric("📊 Projetos", f"{usuario['projetos_mes_atual']}/∞")
            else:
                st.metric("📊 Projetos", f"{usuario['projetos_mes_atual']}/{limite}")
        
        # Botão de logout
        if st.button("🚪 Sair"):
            del st.session_state.usuario_logado
            st.rerun()

# Instância global do sistema de autenticação
sistema_auth = SistemaAuth()

