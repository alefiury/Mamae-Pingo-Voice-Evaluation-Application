"""
Instruções de Configuração do Firebase

1. Acesse o Console do Firebase (https://console.firebase.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Vá para Configurações do Projeto > Contas de Serviço
4. Clique em "Gerar Nova Chave Privada"
5. Baixe o arquivo JSON
6. Copie os valores do JSON para o arquivo .env

Estrutura do banco de dados Firestore:
Coleção: evaluations
  Campos do documento:
    - anonymous_id: string (identificador anônimo do áudio)
    - original_filename: string (nome real do arquivo)
    - vote: string ('aprovado' ou 'reprovado')
    - category: string (categoria da pasta)
    - duration: string ('curto' ou 'longo')
    - session_id: string (identificador único da sessão)
    - timestamp: timestamp
    - user_agent: string (informação do navegador se disponível)
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def test_firebase_connection():
    """Testar conexão com o Firebase"""
    try:
        # Criar credenciais a partir das variáveis de ambiente
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

        # Verificar se as credenciais essenciais estão presentes
        if not firebase_creds["project_id"]:
            print("❌ FIREBASE_PROJECT_ID não encontrado no arquivo .env")
            return

        # Inicializar Firebase
        cred = credentials.Certificate(firebase_creds)
        firebase_admin.initialize_app(cred)

        # Obter cliente Firestore
        db = firestore.client()

        # Teste de escrita
        test_doc = db.collection('test').document('test_connection')
        test_doc.set({
            'test': True,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        # Teste de leitura
        doc = test_doc.get()
        if doc.exists:
            print("✅ Conexão com Firebase bem-sucedida!")
            print(f"Dados do documento de teste: {doc.to_dict()}")

            # Limpar documento de teste
            test_doc.delete()
            print("✅ Documento de teste removido")
        else:
            print("❌ Não foi possível ler o documento de teste")

    except Exception as e:
        print(f"❌ Conexão com Firebase falhou: {str(e)}")
        print("\nVerifique se:")
        print("1. O arquivo .env existe e contém todas as credenciais")
        print("2. As credenciais do Firebase estão corretas")
        print("3. O Firestore está ativado no seu projeto Firebase")


if __name__ == "__main__":
    test_firebase_connection()