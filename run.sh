#!/bin/bash

# Aplicação de Avaliação de Voz Mamãe Pingo - Script de Implantação

echo "🎙️ Iniciando Aplicação de Avaliação de Voz Mamãe Pingo..."

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  Aviso: arquivo .env não encontrado!"
    echo "Por favor, copie .env.example para .env e adicione suas credenciais do Firebase."
    echo "cp .env.example .env"
    exit 1
fi

# Verificar se as variáveis essenciais estão definidas
if ! grep -q "FIREBASE_PROJECT_ID=" .env || grep -q "FIREBASE_PROJECT_ID=seu-projeto-id" .env; then
    echo "⚠️  Aviso: FIREBASE_PROJECT_ID não está configurado no arquivo .env!"
    echo "Por favor, adicione suas credenciais do Firebase ao arquivo .env"
    exit 1
fi

# Configurar Streamlit
mkdir -p .streamlit

cat > .streamlit/config.toml << EOF
[theme]
primaryColor = "#00a8a8"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
address = "0.0.0.0"
headless = true

[browser]
gatherUsageStats = false
EOF

# Executar aplicação Streamlit
echo "Iniciando aplicação Streamlit em http://0.0.0.0:8501"
streamlit run main.py --server.maxUploadSize 50