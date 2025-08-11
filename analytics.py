
import os
from datetime import datetime

import pandas as pd
import firebase_admin
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from firebase_admin import credentials, firestore

from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="Mamãe Pingo - Painel de Análise",
    page_icon="🐧",
    layout="wide"
)

# CSS customizado
st.markdown(
    """
        <style>
            .metric-card {
                background: white;
                border-radius: 10px;
                padding: 1.5rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }
            .metric-value {
                font-size: 2rem;
                font-weight: bold;
                color: #00a8a8;
            }
            .metric-label {
                color: #666;
                font-size: 0.9rem;
            }
        </style>
    """,
    unsafe_allow_html=True
)

# Inicializar Firebase
@st.cache_resource
def init_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        # Cria credenciais
        firebase_creds = {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
        }

        cred = credentials.Certificate(firebase_creds)
        firebase_admin.initialize_app(cred)
    return firestore.client()

# Carrega avaliações do Firebase
@st.cache_data(ttl=60)  # Cache por 1 minuto
def load_evaluations():
    db = init_firebase()
    evaluations = []

    docs = db.collection("evaluations").stream()
    for doc in docs:
        data = doc.to_dict()
        evaluations.append(data)

    return pd.DataFrame(evaluations)

# Cabeçalho
st.markdown(
    """
        <div style="text-align: center; padding: 2rem 0;">
            <h1>📊 Painel de Análise - Mamãe Pingo</h1>
            <p style="color: #666;">Em Busca da Identidade Vocal</p>
        </div>
    """,
    unsafe_allow_html=True
)

# Carrega dados
try:
    df = load_evaluations()

    if not df.empty:
        # Converter timestamp para datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Linha de métricas
        col1, col2, col3 = st.columns(3)

        with col1:
            total_evals = len(df)
            st.markdown(
                f"""
                    <div class="metric-card">
                        <div class="metric-value">{total_evals}</div>
                        <div class="metric-label">Total de Avaliações</div>
                    </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            avg_score = df["score"].mean()
            st.markdown(
                f"""
                    <div class="metric-card">
                        <div class="metric-value">{avg_score:.2f}</div>
                        <div class="metric-label">Nota Média</div>
                    </div>
                """,
                unsafe_allow_html=True
            )

        with col3:
            unique_sessions = df["session_id"].nunique()
            st.markdown(
                f"""
                    <div class="metric-card">
                        <div class="metric-value">{unique_sessions}</div>
                        <div class="metric-label">Sessões Únicas</div>
                    </div>
                """,
                unsafe_allow_html=True
            )

        avg_per_session = total_evals / unique_sessions if unique_sessions > 0 else 0

        # with col4:
        #     avg_per_session = total_evals / unique_sessions if unique_sessions > 0 else 0
        #     st.markdown(
        #         f"""
        #             <div class="metric-card">
        #                 <div class="metric-value">{avg_per_session:.1f}</div>
        #                 <div class="metric-label">Média por Sessão</div>
        #             </div>
        #         """,
        #         unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráficos
        col1, col2 = st.columns(2)

        with col1:
            # Distribuição de notas
            score_counts = df["score"].value_counts().sort_index()

            # Criar labels personalizados
            score_labels = {
                1: "1 - Muito Inadequada",
                2: "2 - Inadequada",
                3: "3 - Razoável",
                4: "4 - Boa",
                5: "5 - Excelente"
            }

            fig_scores = px.bar(
                x=[score_labels.get(x, str(x)) for x in score_counts.index],
                y=score_counts.values,
                title="Distribuição das Notas",
                labels={'x': "Nota", 'y': "Quantidade"},
                color=score_counts.index,
                color_continuous_scale='RdYlGn'
            )
            fig_scores.update_traces(showlegend=False)
            st.plotly_chart(fig_scores, use_container_width=True)

        with col2:
            # Score médio por categoria
            category_scores = df.groupby("category")["score"].agg(["mean", "count"])
            if not category_scores.empty:
                category_scores = category_scores.sort_values("mean", ascending=False)

                # change names of the categories for the x axis
                category_labels = {
                    "with-enhancement-10": "Luciane - SE 10%",
                    "with-enhancement-30": "Luciane - SE 30%",
                    "no-enhancement": "Luciane",
                    "synthesized": "Voz Sintética - v1",
                    "new_synthesized": "Voz Sintética - v2",
                    "library": "Biblioteca - ElevenLabs"
                }
                fig_category = px.bar(
                    x=category_scores.index.map(category_labels),
                    y=category_scores["mean"],
                    title="Nota Média por Categoria",
                    labels={'x': "Categoria", 'y': "Nota Média"},
                    color=category_scores["mean"],
                    color_continuous_scale="RdYlGn",
                    text=category_scores["mean"].round(2)
                )
                fig_category.update_traces(texttemplate="%{text}", textposition="outside")
                fig_category.update_layout(yaxis_range=[0, 5.5])
                st.plotly_chart(fig_category, use_container_width=True)

        # Show a table with the mean "score" for "original_filename"
        st.markdown("### 📊 Média de Notas por Voz")

        mean_scores = df.groupby("original_filename")["score"].mean().reset_index()
        mean_scores["score"] = mean_scores["score"].round(2)

        # change columns names for table
        mean_scores.columns = ["Voz", "Nota (Média)"]

        # Change the name from original_filename just to show
        mean_scores["Voz"] = mean_scores["Voz"].str.replace("original_filename_", "")

        st.dataframe(mean_scores, use_container_width=True, hide_index=True)


        # Show a vertical violin plot and scatter plot for every score of original_filename for the top 10 original_filename
        top_files = mean_scores.nlargest(5, "Nota (Média)")
        scores_per_file = df[df["original_filename"].isin(top_files["Voz"])]

        # Show violin plot and scatter plot for each file, plot side by side
        for file in top_files["Voz"]:
            file_scores = scores_per_file[scores_per_file["original_filename"] == file]["score"]
            fig = px.violin(file_scores, y="score", box=True, points="all", title=f"Distribuição de Notas - {file}")
            st.plotly_chart(fig, use_container_width=True)

        # Tabela detalhada
        st.markdown("### 📋 Avaliações Recentes")

        # Preparar dataframe para exibição
        display_df = df[["anonymous_id", "score", "category", "duration", "timestamp", "session_id"]].copy()
        display_df = display_df.sort_values("timestamp", ascending=False).head(100)

        # Traduzir valores
        score_labels = {
            1: "1 ⭐ - Muito Inadequada",
            2: "2 ⭐⭐ - Inadequada",
            3: "3 ⭐⭐⭐ - Razoável",
            4: "4 ⭐⭐⭐⭐ - Boa",
            5: "5 ⭐⭐⭐⭐⭐ - Excelente"
        }
        display_df["score"] = display_df["score"].map(score_labels)
        display_df["duration"] = display_df["duration"].map({"curto": "Curto", "longo": "Longo"})

        # Renomear colunas
        display_df.columns = ["ID Anônimo", "Nota", "Categoria", "Duração", "Data/Hora", "ID da Sessão"]

        # Estilizar o dataframe
        def style_score(val):
            if "5 ⭐" in str(val):
                return "color: #2e7d32; font-weight: bold;"
            elif "4 ⭐" in str(val):
                return "color: #558b2f; font-weight: bold;"
            elif "3 ⭐" in str(val):
                return "color: #f57c00; font-weight: bold;"
            elif "2 ⭐" in str(val):
                return "color: #e65100; font-weight: bold;"
            elif "1 ⭐" in str(val):
                return "color: #c62828; font-weight: bold;"
            return ''

        styled_df = display_df.style.applymap(style_score, subset=["Nota"])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Análise adicional
        st.markdown("### 📊 Análise Detalhada")

        col1, col2 = st.columns(2)

        with col1:
            # Top 10 maiores arquivos
            top_files = df.nlargest(10, 'score')[['anonymous_id', 'score', 'category']]
            st.markdown("#### 🏆 Top 10 Maiores Avaliações")
            for _, row in top_files.iterrows():
                category = row["category"]

                if category == "with-enhancement-10":
                    category = "Luciane - SE 10%"
                elif category == "with-enhancement-30":
                    category = "Luciane - SE 30%"
                elif category == "no-enhancement":
                    category = "Luciane"
                elif category == "synthesized":
                    category = "Voz Sintética - v1"
                elif category == "new_synthesized":
                    category = "Voz Sintética - v2"
                elif category == "library":
                    category = "Biblioteca - ElevenLabs"

                st.write(f"• {row['anonymous_id']} - Nota {row['score']:.1f} (**{category}**)")

        # with col2:
        #     # Distribuição por sessão
        #     session_stats = df.groupby('session_id').agg({
        #         'score': ['mean', 'count']
        #     }).round(2)
        #     session_stats.columns = ['Nota Média', 'Quantidade']
        #     session_stats = session_stats.sort_values('Nota Média', ascending=False).head(5)

        #     st.markdown("#### 👥 Top 5 Sessões por Nota Média")
        #     for session_id, row in session_stats.iterrows():
        #         st.write(f"• **{session_id[:8]}...** - Média {row['Nota Média']} ({row['Quantidade']} avaliações)")

        # Funcionalidade de exportação
        st.markdown("### 📥 Exportar Dados")
        col1, col2 = st.columns(2)

        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="Baixar Dataset Completo (CSV)",
                data=csv,
                file_name=f"mamae_pingo_avaliacoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        with col2:
            # Relatório resumido
            summary = {
                'Total de Avaliações': total_evals,
                'Nota Média Geral': f"{avg_score:.2f}",
                'Nota Mais Frequente': df['score'].mode()[0] if not df['score'].mode().empty else 'N/A',
                'Desvio Padrão': f"{df['score'].std():.2f}",
                'Sessões Únicas': unique_sessions,
                'Média por Sessão': f"{avg_per_session:.1f}",
                'Período': f"{df['timestamp'].min().strftime('%d/%m/%Y')} a {df['timestamp'].max().strftime('%d/%m/%Y')}"
            }

            # Adicionar distribuição de notas
            score_dist = df['score'].value_counts().sort_index()
            for score in range(1, 6):
                count = score_dist.get(score, 0)
                percentage = (count / total_evals * 100) if total_evals > 0 else 0
                summary[f'Nota {score}'] = f"{count} ({percentage:.1f}%)"

            summary_text = '\n'.join([f"{k}: {v}" for k, v in summary.items()])
            st.download_button(
                label="Baixar Relatório Resumido (TXT)",
                data=summary_text,
                file_name=f"mamae_pingo_resumo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

    else:
        st.info("Nenhuma avaliação encontrada ainda. Comece a coletar feedback usando a aplicação principal!")

except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    st.info("Verifique se o Firebase está configurado corretamente e se há dados no banco de dados.")

# Botão de atualização
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()
