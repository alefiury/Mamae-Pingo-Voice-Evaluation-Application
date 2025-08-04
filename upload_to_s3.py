#!/usr/bin/env python3
"""
Script para fazer upload de arquivos de áudio para o S3
Este script deve ser executado uma vez para enviar todos os arquivos de áudio para o bucket S3
"""

import os
import boto3
from pathlib import Path
from dotenv import load_dotenv
import json
import hashlib
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# Configurar cliente S3
s3_client = boto3.client(
    's3',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

BUCKET_NAME = os.getenv('AWS_S3_BUCKET', 'mamae-pingo-audio-files')
S3_PREFIX = os.getenv('S3_PREFIX', 'audio-evaluations/')

def create_bucket_if_not_exists():
    """Criar bucket S3 se não existir"""
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        print(f"✅ Bucket '{BUCKET_NAME}' já existe")
    except:
        try:
            s3_client.create_bucket(Bucket=BUCKET_NAME)
            print(f"✅ Bucket '{BUCKET_NAME}' criado com sucesso")

            # Configurar CORS para permitir acesso do navegador
            cors_configuration = {
                'CORSRules': [{
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'HEAD'],
                    'AllowedOrigins': ['*'],
                    'ExposeHeaders': ['ETag']
                }]
            }
            s3_client.put_bucket_cors(
                Bucket=BUCKET_NAME,
                CORSConfiguration=cors_configuration
            )
            print("✅ CORS configurado para o bucket")
        except Exception as e:
            print(f"❌ Erro ao criar bucket: {e}")
            return False
    return True

def upload_audio_files():
    """Fazer upload de todos os arquivos de áudio para o S3"""

    # Diretórios de áudio
    audio_dirs = [
        '../library',
        '../luciane/no-enhancement',
        '../luciane/with-enhancement-10',
        '../luciane/with-enhancement-30',
        '../new_synthesized',
        '../synthesized',
        # '.'  # Diretório raiz
    ]

    audio_extensions = ['.wav', '.mp3']
    uploaded_files = []
    audio_metadata = []

    print("\n📤 Iniciando upload dos arquivos de áudio...\n")

    for dir_path in audio_dirs:
        if not os.path.exists(dir_path):
            print(f"⚠️  Diretório '{dir_path}' não encontrado, pulando...")
            continue

        # Listar arquivos no diretório
        files = os.listdir(dir_path) if dir_path != '.' else [f for f in os.listdir(dir_path) if os.path.isfile(f)]

        for file in files:
            if any(file.endswith(ext) for ext in audio_extensions):
                file_path = os.path.join(dir_path, file) if dir_path != '.' else file

                # Determinar categoria
                if dir_path == '.':
                    category = 'raiz'
                else:
                    category = os.path.basename(dir_path)

                # Determinar duração
                duration = 'longo' if 'pingocast' in file.lower() or len(file) > 50 else 'curto'

                # Gerar ID único
                hash_obj = hashlib.md5(file.encode())
                anonymous_id = f"audio_{hash_obj.hexdigest()[:8]}_{len(uploaded_files)}"

                # Criar chave S3
                s3_key = f"{S3_PREFIX}{category}/{file}"

                try:
                    # Upload do arquivo
                    print(f"📤 Enviando: {file_path} -> s3://{BUCKET_NAME}/{s3_key}")

                    # Detectar content type
                    content_type = 'audio/wav' if file.endswith('.wav') else 'audio/mpeg'

                    s3_client.upload_file(
                        file_path,
                        BUCKET_NAME,
                        s3_key,
                        ExtraArgs={
                            'ContentType': content_type,
                            'CacheControl': 'public, max-age=86400'  # Cache por 24 horas
                        }
                    )

                    # Adicionar metadata
                    metadata = {
                        'anonymous_id': anonymous_id,
                        'original_name': file,
                        'category': category,
                        'duration': duration,
                        's3_key': s3_key,
                        'bucket': BUCKET_NAME,
                        'content_type': content_type
                    }
                    audio_metadata.append(metadata)
                    uploaded_files.append(file_path)

                    print(f"✅ Upload concluído: {file}")

                except Exception as e:
                    print(f"❌ Erro no upload de {file}: {e}")

    # Salvar metadata em um arquivo JSON
    metadata_file = 'audio_metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump({
            'upload_date': datetime.now().isoformat(),
            'total_files': len(audio_metadata),
            'bucket': BUCKET_NAME,
            'prefix': S3_PREFIX,
            'files': audio_metadata
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Upload concluído!")
    print(f"📊 Total de arquivos enviados: {len(uploaded_files)}")
    print(f"📄 Metadata salvo em: {metadata_file}")

    # Upload do arquivo de metadata para o S3
    try:
        s3_client.upload_file(
            metadata_file,
            BUCKET_NAME,
            f"{S3_PREFIX}metadata.json",
            ExtraArgs={'ContentType': 'application/json'}
        )
        print(f"✅ Metadata enviado para S3: s3://{BUCKET_NAME}/{S3_PREFIX}metadata.json")
    except Exception as e:
        print(f"❌ Erro ao enviar metadata: {e}")

    return audio_metadata

def test_s3_access():
    """Testar acesso aos arquivos no S3"""
    print("\n🧪 Testando acesso aos arquivos no S3...")

    try:
        # Listar objetos no bucket
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=S3_PREFIX,
            MaxKeys=5
        )

        if 'Contents' in response:
            print(f"✅ Acesso ao S3 confirmado. Primeiros arquivos:")
            for obj in response['Contents'][:5]:
                print(f"   - {obj['Key']} ({obj['Size']} bytes)")

            # Gerar URL pré-assinada para teste
            if response['Contents']:
                test_key = response['Contents'][0]['Key']
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': BUCKET_NAME, 'Key': test_key},
                    ExpiresIn=3600  # 1 hora
                )
                print(f"\n🔗 URL de teste (válida por 1 hora):")
                print(f"   {presigned_url}")
        else:
            print("⚠️  Nenhum arquivo encontrado no bucket")

    except Exception as e:
        print(f"❌ Erro ao acessar S3: {e}")

if __name__ == "__main__":
    print("🚀 Script de Upload de Áudios para S3")
    print("=" * 50)

    # Verificar variáveis de ambiente
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        print("Por favor, configure o arquivo .env com suas credenciais AWS")
        exit(1)

    # Criar bucket se necessário
    if not create_bucket_if_not_exists():
        exit(1)

    # Fazer upload dos arquivos
    metadata = upload_audio_files()

    # Testar acesso
    if metadata:
        test_s3_access()

    print("\n✨ Script concluído!")