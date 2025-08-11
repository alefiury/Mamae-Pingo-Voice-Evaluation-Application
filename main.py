import os
import json
import base64
import random
import hashlib
import requests
from datetime import datetime

import boto3
import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore


# Configuração inicial do Streamlit
st.set_page_config(
    page_title="Mamãe Pingo - Avaliação de Voz",
    page_icon="🐧",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# Carregar o logo em base64 ANTES de renderizar qualquer HTML
logo_path = "./logo.png"
logo_data = None
if os.path.exists(logo_path):
    try:
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
    except Exception:
        logo_data = None


# Estilo da página
st.markdown("""
<style>
    /* BARRA SUPERIOR FIXA */
    .app-header {
        position: fixed;
        /* Move a barra para baixo para ficar abaixo do cabeçalho do Streamlit (aprox. 3rem de altura) */
        top: 3rem;
        left: 0;
        right: 0;
        height: 70px; /* Altura fixa da barra */
        padding: 0 2rem; /* Espaçamento interno */
        background-color: white;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); /* Sombra sutil */
        z-index: 999; /* Garante que fique acima do conteúdo mas abaixo do menu do Streamlit */
    }

    .app-header img {
        max-height: 50px; /* Altura máxima do logo */
    }

    /* Estilo do container principal com ajuste para AMBAS as barras superiores */
    .main {
        padding: 2rem;
        /* Adiciona espaço para o cabeçalho do Streamlit (3rem) + sua barra (70px) + margem */
        padding-top: calc(3rem + 90px);
        max-width: 1000px;
        margin: 0 auto;
    }

    /* Estilo do cabeçalho */
    .header-container {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 3rem;
        background: linear-gradient(135deg, #00a8a8 0%, #00d4d4 100%);
        border-radius: 15px;
        color: white;
    }

    /* Estilo dos cards */
    .audio-card {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
        border: 1px solid #e0e0e0;
    }

    /* Estilo das diretrizes */
    .guidelines-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid #e3e3e3;
    }

    .score-table {
        width: 100%;
        margin: 1rem 0;
        border-collapse: collapse;
    }

    .score-table th {
        background-color: #00a8a8;
        color: white;
        padding: 0.8rem;
        text-align: center;
    }

    .score-table td {
        padding: 0.8rem;
        border: 1px solid #ddd;
        text-align: center;
    }

    .score-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }

    /* Estilo dos botões de pontuação */
    .score-button {
        width: 100%;
        padding: 1.2rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s;
        border: 2px solid transparent;
        cursor: pointer;
    }

    .score-1 {
        background-color: #ffebee;
        color: #c62828;
        border-color: #ffcdd2;
    }

    .score-1:hover {
        background-color: #ffcdd2;
        transform: scale(1.02);
    }

    .score-2 {
        background-color: #fff3e0;
        color: #e65100;
        border-color: #ffe0b2;
    }

    .score-2:hover {
        background-color: #ffe0b2;
        transform: scale(1.02);
    }

    .score-3 {
        background-color: #fffde7;
        color: #f57c00;
        border-color: #fff9c4;
    }

    .score-3:hover {
        background-color: #fff9c4;
        transform: scale(1.02);
    }

    .score-4 {
        background-color: #f1f8e9;
        color: #558b2f;
        border-color: #dcedc8;
    }

    .score-4:hover {
        background-color: #dcedc8;
        transform: scale(1.02);
    }

    .score-5 {
        background-color: #e8f5e9;
        color: #2e7d32;
        border-color: #c8e6c9;
    }

    .score-5:hover {
        background-color: #c8e6c9;
        transform: scale(1.02);
    }

    /* Estilo da barra de progresso */
    .progress-container {
        background-color: #f0f0f0;
        border-radius: 25px;
        padding: 3px;
        margin: 2rem 0;
    }

    .progress-bar {
        background: linear-gradient(90deg, #00a8a8 0%, #00d4d4 100%);
        height: 30px;
        border-radius: 25px;
        transition: width 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: flex-start; /* MODIFICADO: Alinha o texto à esquerda */
        padding-left: 15px;          /* ADICIONADO: Espaçamento interno */
        color: white;
        font-weight: bold;
        white-space: nowrap;         /* ADICIONADO: Impede a quebra de linha */
    }

    .completion-message {
        text-align: center;
        padding: 3rem;
        background-color: #e8f5e9;
        border-radius: 15px;
        margin: 2rem 0;
    }

    /* Navegação */
    .navigation-buttons {
        display: flex;
        justify-content: space-between;
        margin-top: 2rem;
    }

    .selected-score {
        background-color: #00a8a8 !important;
        color: white !important;
        border-color: #00a8a8 !important;
    }
</style>
""", unsafe_allow_html=True)


# Renderiza a barra superior fixa com a logo
if logo_data:
    st.markdown(
        f'''
        <div class="app-header">
            <img src="data:image/png;base64,{logo_data}" alt="Logo Mamãe Pingo">
        </div>
        ''',
        unsafe_allow_html=True
    )


# Inicializar Firebase
@st.cache_resource
def init_firebase():
    """Inicializar Firebase Database"""
    try:
        # Verificar se já foi inicializado
        firebase_admin.get_app()
    except ValueError:
        # Criar credenciais
        firebase_creds = {
            "type": "service_account",
            "project_id": st.secrets["FIREBASE_PROJECT_ID"],
            "private_key_id": st.secrets["FIREBASE_PRIVATE_KEY_ID"],
            "private_key": st.secrets["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n"),
            "client_email": st.secrets["FIREBASE_CLIENT_EMAIL"],
            "client_id": st.secrets["FIREBASE_CLIENT_ID"],
            "auth_uri": st.secrets["FIREBASE_AUTH_URI"],
            "token_uri": st.secrets["FIREBASE_TOKEN_URI"],
            "auth_provider_x509_cert_url": st.secrets["FIREBASE_AUTH_PROVIDER_CERT_URL"],
            "client_x509_cert_url": st.secrets["FIREBASE_CLIENT_CERT_URL"]
        }

        cred = credentials.Certificate(firebase_creds)
        firebase_admin.initialize_app(cred)

    return firestore.client()


@st.cache_resource
def init_s3_client():
    """Inicializar cliente S3"""
    try:
        s3_client = boto3.client(
            "s3",
            region_name=st.secrets["AWS_REGION"],
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
        )
        return s3_client
    except Exception as e:
        st.error(f"Erro ao conectar com S3: {e}")
        return None


# Carregar e preparar arquivos de áudio do S3
@st.cache_data
def load_audio_files_from_s3():
    """Carregar metadata dos arquivos de áudio do S3"""
    s3_client = init_s3_client()
    if not s3_client:
        return []

    bucket_name = st.secrets["AWS_S3_BUCKET"]
    s3_prefix = st.secrets["S3_PREFIX"]

    # Lista arquivos diretamente do S3
    audio_files = []

    paginator = s3_client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(
        Bucket=bucket_name,
        Prefix=s3_prefix
    )

    for page in page_iterator:
        if "Contents" in page:
            for obj in page["Contents"]:
                key = obj["Key"]

                # Ignorar o arquivo de metadata e diretórios
                if key.endswith(".json") or key.endswith('/'):
                    continue

                # Verificar se é arquivo de áudio
                if key.endswith((".wav", ".mp3", ".flac", ".m4a", ".ogg", ".opus")):
                    # Extrair informações do caminho
                    parts = key.replace(s3_prefix, '').split('/')
                    category = parts[0] if len(parts) > 1 else 'raiz'
                    filename = parts[-1]

                    # Determinar duração
                    duration = 'longo' if 'pingocast' in filename.lower() else 'curto'

                    # Gerar ID anônimo
                    hash_obj = hashlib.md5(filename.encode())
                    anonymous_id = f"audio_{hash_obj.hexdigest()[:8]}_{len(audio_files)}"

                    audio_files.append({
                        "anonymous_id": anonymous_id,
                        "original_name": filename,
                        "category": category,
                        "duration": duration,
                        "s3_key": key,
                        "bucket": bucket_name,
                        "content_type": 'audio/wav' if key.endswith('.wav') else 'audio/mpeg'
                    })

    # Embaralhar a lista
    random.shuffle(audio_files)
    return audio_files


# Função para obter URL pré-assinada do S3
@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_presigned_url(bucket, key):
    """Gerar URL pré-assinada para acesso ao arquivo de áudio"""
    s3_client = init_s3_client()
    if not s3_client:
        return None

    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600  # URL válida por 1 hora
        )
        return url
    except Exception as e:
        st.error(f"Erro ao gerar URL: {e}")
        return None

# Função para baixar áudio do S3
@st.cache_data(ttl=3600)
def download_audio_from_s3(bucket, key):
    """Baixar arquivo de áudio do S3"""
    url = get_presigned_url(bucket, key)
    if not url:
        return None

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Erro ao baixar áudio: Status {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro ao baixar áudio: {e}")
        return None


# Salvar avaliação no Firebase
def save_evaluation(db, audio_id, original_name, score, category, duration, session_id):
    doc_ref = db.collection(st.secrets["FIREBASE_DB_NAME"]).document(f"{session_id}_{audio_id}")
    doc_ref.set({
        "anonymous_id": audio_id,
        "original_filename": original_name,
        "score": score,
        "category": category,
        "duration": duration,
        "session_id": session_id,
        "timestamp": datetime.now(),
        "user_agent": st.session_state.get('user_agent', 'unknown')
    })

# Inicializar estado da sessão
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
    st.session_state.evaluations = {}
    st.session_state.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16]

# Carregar arquivos de áudio
audio_files = load_audio_files_from_s3()

# Inicializar Firebase
db = init_firebase()

# Cabeçalho da página
st.markdown(
    """
        <div class="header-container">
            <h1 style="margin: 0;">Avaliação de Voz</h1>
            <p style="margin-top: 0.5rem; font-size: 1.2rem;">Em busca da identidade vocal</p>
        </div>
    """,
    unsafe_allow_html=True
)

# Barra de progresso
progress = (st.session_state.current_index / len(audio_files)) * 100 if len(audio_files) > 0 else 0
evaluated_count = len(st.session_state.evaluations)
st.markdown(
    f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {progress}%;">
                {st.session_state.current_index} / {len(audio_files)} ({evaluated_count} avaliados)
            </div>
        </div>
    """,
    unsafe_allow_html=True
)

# Interface principal de avaliação
if st.session_state.current_index < len(audio_files):
    current_audio = audio_files[st.session_state.current_index]

     # Diretrizes de avaliação
    st.markdown("""
    <div class="guidelines-card">
        <h3 style="color: #00a8a8; margin-bottom: 1rem;">📋 Diretrizes de Avaliação</h3>
        <p><strong>Objetivo:</strong> Nos ajude a encontrar a voz perfeita para a "Mamãe Pingo"! Você ouvirá a mesma frase dita por diferentes vozes e deverá dar uma nota de 1 a 5.</p>
        <p><strong>O que buscamos?</strong> Uma voz para narrar nossos posts de blog com clareza, naturalidade e um estilo que cative.
        <p>Concentre sua avaliação nos seguintes pontos:</p>
        <ul>
            <li>🤗 <strong>Acolhimento</strong> - A voz soa calorosa e amigável?</li>
            <li>🎯 <strong>Clareza</strong> - A fala é clara e fácil de entender?</li>
            <li>🌟 <strong>Naturalidade</strong> - Soa natural e agradável de ouvir?</li>
        </ul>
        <table class="score-table">
            <thead>
                <tr>
                    <th>Nota</th>
                    <th>Classificação</th>
                    <th>Descrição para Mamãe Pingo</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>5</strong></td>
                    <td><strong>Excelente</strong></td>
                    <td>Voz perfeita para a Mamãe Pingo - acolhedora, clara e natural</td>
                </tr>
                <tr>
                    <td><strong>4</strong></td>
                    <td><strong>Boa</strong></td>
                    <td>Voz adequada com pequenos ajustes necessários</td>
                </tr>
                <tr>
                    <td><strong>3</strong></td>
                    <td><strong>Razoável</strong></td>
                    <td>Voz aceitável mas falta personalidade ou clareza</td>
                </tr>
                <tr>
                    <td><strong>2</strong></td>
                    <td><strong>Inadequada</strong></td>
                    <td>Voz não transmite as características necessárias</td>
                </tr>
                <tr>
                    <td><strong>1</strong></td>
                    <td><strong>Muito Inadequada</strong></td>
                    <td>Voz completamente inapropriada para o contexto</td>
                </tr>
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

   # Card do áudio com título
    st.markdown(f"""
    <h3 style='text-align: center; margin-bottom: 1.5rem;'>🎧 Ouça o Áudio {st.session_state.current_index + 1} de {len(audio_files)}</h3>
    """, unsafe_allow_html=True)

    # Player de áudio centralizado
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        audio_bytes = download_audio_from_s3(
            current_audio.get("bucket", st.secrets["AWS_S3_BUCKET"]),
            current_audio["s3_key"]
        )
        st.audio(audio_bytes, format=current_audio.get('content_type', 'audio/mpeg'))

    # Verificar se já foi avaliado
    current_score = st.session_state.evaluations.get(current_audio['anonymous_id'], None)
    if current_score:
        st.info(f"✅ Este áudio já foi avaliado com a nota {current_score}. A avaliação pode ser alterada a qualquer momento.")

    # Botões de pontuação
    st.markdown("<h4 style='text-align: center; margin: 2rem 0 1rem 0;'>Qual nota você daria para esta voz?</h4>", unsafe_allow_html=True)

    score_cols = st.columns(5)
    scores = [
        ("1 - Muito Inadequada", "❌", 1),
        ("2 - Inadequada", "👎", 2),
        ("3 - Razoável", "😐", 3),
        ("4 - Boa", "👍", 4),
        ("5 - Excelente", "⭐", 5)
    ]

    selected_score = None
    for col, (label, emoji, score) in zip(score_cols, scores):
        with col:
            button_key = f"score_{score}_{st.session_state.current_index}"
            if st.button(f"{emoji}\n{score}", key=button_key, use_container_width=True):
                selected_score = score
                save_evaluation(
                    db,
                    current_audio['anonymous_id'],
                    current_audio['original_name'],
                    score,
                    current_audio['category'],
                    current_audio['duration'],
                    st.session_state.session_id
                )
                st.session_state.evaluations[current_audio['anonymous_id']] = score
                st.session_state.current_index += 1
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Botões de navegação
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.session_state.current_index > 0:
            if st.button("⬅️ Anterior", key="prev", use_container_width=True):
                st.session_state.current_index -= 1
                st.rerun()

    with col2:
        if st.button("Pular ⏭️", key="skip", use_container_width=True):
            st.session_state.current_index += 1
            st.rerun()

    with col3:
        # Mostrar botão próximo apenas se já avaliou
        if current_audio['anonymous_id'] in st.session_state.evaluations:
            if st.button("Próximo ➡️", key="next", use_container_width=True):
                st.session_state.current_index += 1
                st.rerun()

else:
    # Mensagem de conclusão
    st.markdown(f"""
    <div class="completion-message">
        <h2>🎉 Obrigado por concluir a avaliação!</h2>
        <p style="font-size: 1.2rem;">Sua opinião é fundamental para criarmos a melhor experiência com a Mamãe Pingo.</p>
        <p>Você avaliou <strong>{len(st.session_state.evaluations)}</strong> de <strong>{len(audio_files)}</strong> arquivos de áudio.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.current_index > 0:
            if st.button("⬅️ Voltar para revisar", use_container_width=True):
                st.session_state.current_index = len(audio_files) - 1 if audio_files else 0
                st.rerun()

    with col2:
        if st.button("🔄 Iniciar Nova Sessão", use_container_width=True):
            # Limpa o estado da sessão para um novo começo
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>© 2025 Mamãe Pingo.</p>
</div>
""", unsafe_allow_html=True)