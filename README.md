# Plataforma de Avaliação de Voz Mamãe Pingo

Uma aplicação web profissional para coletar feedback de usuários sobre a qualidade da síntese de voz através de votos positivos e negativos. Construída com Streamlit e Firebase para fácil implantação e coleta de dados em tempo real.

## Características

- **Avaliação Anônima**: Arquivos de áudio são apresentados com IDs anonimizados mantendo os nomes originais no banco de dados
- **Interface Profissional**: Design limpo e moderno com a marca Mamãe Pingo
- **Acompanhamento de Progresso**: Barra de progresso visual mostrando conclusão da avaliação
- **Categorias de Áudio**: Categorização automática baseada na estrutura de diretórios
- **Classificação de Duração**: Distingue entre arquivos de áudio curtos (<30s) e longos (>30s)
- **Gerenciamento de Sessão**: Rastreia sessões únicas de avaliação
- **Armazenamento Firebase em Tempo Real**: Todas as avaliações armazenadas instantaneamente no Firestore
- **Painel de Análise**: Página opcional de análise para visualizar resultados das avaliações
- **Suporte a Variáveis de Ambiente**: Usa arquivo `.env` para credenciais seguras

## Estrutura do Projeto

```
mamae-pingo-evaluation/
│
├── main.py                    # Aplicação Streamlit principal
├── analytics.py              # Painel de análise (opcional)
├── firebase_setup.py         # Auxiliar de configuração Firebase
├── requirements.txt          # Dependências Python
├── run.sh                   # Script de implantação
├── README.md               # Este arquivo
│
├── .env                    # Variáveis de ambiente (não no repositório)
├── .env.example           # Exemplo de configuração de ambiente
├── logo.png               # Logo Mamãe Pingo
│
├── 10%/                   # Diretório de arquivos de áudio
├── library/               # Diretório de arquivos de áudio
├── luciane/               # Diretório de arquivos de áudio
├── new_synthesized/       # Diretório de arquivos de áudio
├── synthesized/           # Diretório de arquivos de áudio
└── .streamlit/           # Configuração Streamlit (gerado automaticamente)
```

## Instalação

### 1. Clone o repositório
```bash
git clone <url-do-seu-repositorio>
cd mamae-pingo-evaluation
```

### 2. Configure o ambiente Python
```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure o Firebase

1. Acesse o [Console do Firebase](https://console.firebase.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative o Firestore Database
4. Vá para Configurações do Projeto > Contas de Serviço
5. Clique em "Gerar Nova Chave Privada"
6. Baixe o arquivo JSON

### 4. Configure as variáveis de ambiente

1. Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

2. Abra o arquivo `.env` e preencha com as credenciais do Firebase do arquivo JSON baixado:
```
FIREBASE_PROJECT_ID=seu-projeto-id
FIREBASE_PRIVATE_KEY_ID=sua-chave-privada-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=seu-email@seu-projeto.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=seu-client-id
FIREBASE_CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/...
```

### 5. Teste a conexão com o Firebase
```bash
python firebase_setup.py
```

## Executando a Aplicação

### Opção 1: Usando o script shell (Linux/Mac)
```bash
chmod +x run.sh
./run.sh
```

### Opção 2: Inicialização manual
```bash
streamlit run main.py
```

A aplicação estará disponível em `http://localhost:8501` (ou `http://seu-servidor-ip:8501` para acesso remoto).

## Implantação em um Servidor

### 1. Instale as dependências no seu servidor
```bash
sudo apt update
sudo apt install python3-pip python3-venv
```

### 2. Configure o firewall (se necessário)
```bash
sudo ufw allow 8501
```

### 3. Execute como um serviço (exemplo systemd)
Crie `/etc/systemd/system/mamae-pingo.service`:

```ini
[Unit]
Description=Mamãe Pingo Avaliação de Voz
After=network.target

[Service]
Type=simple
User=seu-usuario
WorkingDirectory=/caminho/para/mamae-pingo-evaluation
Environment="PATH=/caminho/para/mamae-pingo-evaluation/venv/bin"
ExecStart=/caminho/para/mamae-pingo-evaluation/venv/bin/streamlit run main.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

Habilite e inicie o serviço:
```bash
sudo systemctl enable mamae-pingo
sudo systemctl start mamae-pingo
sudo systemctl status mamae-pingo
```

### 4. Configure proxy reverso (exemplo Nginx)
```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

## Estrutura do Banco de Dados Firebase

### Coleção: `evaluations`
Cada documento contém:
- `anonymous_id`: Identificador anonimizado do arquivo de áudio
- `original_filename`: Nome real do arquivo (para referência interna)
- `vote`: "aprovado" ou "reprovado"
- `category`: Categoria do diretório do arquivo de áudio
- `duration`: "curto" ou "longo"
- `session_id`: Identificador único da sessão
- `timestamp`: Quando a avaliação foi feita
- `user_agent`: Informação do navegador (se disponível)

## Painel de Análise

Acesse o painel de análise executando:
```bash
streamlit run analytics.py
```

Funcionalidades:
- Contagem total de avaliações
- Porcentagem de taxa de aprovação
- Rastreamento de sessões únicas
- Gráficos de distribuição de votos
- Análise de desempenho por categoria
- Visualização de linha do tempo
- Funcionalidade de exportação (CSV e relatórios resumidos)

## Organização dos Arquivos de Áudio

A aplicação escaneia automaticamente arquivos de áudio em:
- Diretório raiz (arquivos `.wav` e `.mp3`)
- `./10%/` - Arquivos de áudio aprimorados em 10%
- `./library/` - Amostras da biblioteca de vozes
- `./luciane/` - Variações da voz Luciane
- `./new_synthesized/` - Novas vozes sintetizadas
- `./synthesized/` - Vozes sintetizadas originais

Os arquivos são automaticamente categorizados como:
- **Curto (<30s)**: Diferentes vozes dizendo o mesmo conteúdo
- **Longo (>30s)**: Leituras de postagens de blog

## Considerações de Segurança

1. **Credenciais Firebase**: Nunca faça commit do arquivo `.env` no controle de versão
2. **Controle de Acesso**: Considere implementar Regras de Segurança do Firebase
3. **Limitação de Taxa**: Streamlit tem proteções integradas, mas monitore o uso
4. **HTTPS**: Use certificados SSL para implantação em produção

## Solução de Problemas

### Problemas Comuns

1. **Erro de conexão Firebase**
   - Verifique se o arquivo `.env` existe e tem todas as credenciais
   - Verifique se o projeto Firebase tem o Firestore habilitado
   - Execute `python firebase_setup.py` para testar a conexão

2. **Arquivos de áudio não carregando**
   - Verifique se os caminhos dos arquivos estão corretos
   - Verifique as permissões dos arquivos
   - Certifique-se de que os arquivos de áudio estão em formatos suportados (.wav, .mp3)

3. **Porta já em uso**
   - Mude a porta em `run.sh` ou use a flag `--server.port XXXX`
   - Mate processos Streamlit existentes: `pkill -f streamlit`

4. **Problemas de memória com arquivos de áudio grandes**
   - Aumente o limite de tamanho de upload: `--server.maxUploadSize 50`
   - Considere a compressão de arquivos de áudio

## Contribuindo

1. Faça fork do repositório
2. Crie uma branch de funcionalidade
3. Faça commit das suas mudanças
4. Faça push para a branch
5. Crie um Pull Request

## Licença

Este projeto é proprietário da Mamãe Pingo. Todos os direitos reservados.

## Suporte

Para problemas ou perguntas, entre em contato com a equipe de desenvolvimento da Mamãe Pingo.