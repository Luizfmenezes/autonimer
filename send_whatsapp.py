# send_whatsapp.py (versão corrigida para WAHA 2025.9.2 / WEBJS)

import os
import sys
import time
import requests

# --- CONFIGURAÇÕES ---
WAHA_ENDPOINT = os.getenv("WAHA_ENDPOINT")
WAHA_API_KEY = os.getenv("WAHA_API_KEY")
WAHA_GROUP_ID = os.getenv("WAHA_GROUP_ID")
CAPTION = os.getenv("CAPTION", "Segue o relatório de linhas do dia.")
OUTPUT_DIR = "/app/output"
SENT_MARKER = ".sent"
# --- FUNÇÕES DO WHATSAPP (Apenas a função de envio precisa ser substituída) ---

def wait_for_session_ready(api_url, session_name, api_key, timeout_seconds=180):
    """Verifica se a sessão do WAHA está conectada e pronta."""
    print(f"INFO: Aguardando a sessão '{session_name}' do WAHA ficar pronta...")
    start_time = time.time()
    headers = {'X-Api-Key': api_key}
    
    while time.time() - start_time < timeout_seconds:
        try:
            response = requests.get(f"{api_url}/api/sessions/{session_name}", timeout=10, headers=headers)
            if response.status_code == 200:
                status = response.json().get("status")
                print(f"INFO: Status atual da sessão '{session_name}': {status}")
                if status in ["CONNECTED", "WORKING"]:
                    print(f"✅ Sessão '{session_name}' está pronta para uso (Status: {status})!")
                    return True
            else:
                print(f"AVISO: Sessão '{session_name}' ainda não encontrada (Status: {response.status_code}), aguardando...")
        except requests.exceptions.RequestException:
            print("AVISO: API do WAHA ainda não está respondendo, aguardando...")
        time.sleep(10)

    print(f"❌ ERRO CRÍTICO: A sessão '{session_name}' não conectou a tempo.")
    return False

# --- SUBSTITUA A FUNÇÃO ANTIGA POR ESTA ---
def enviar_imagem_whatsapp(filepath):
    """Envia uma imagem para o grupo configurado via API do WAHA."""
    if not all([WAHA_GROUP_ID, WAHA_API_KEY, WAHA_ENDPOINT]):
        print("❌ ERRO: WAHA_GROUP_ID, WAHA_API_KEY ou WAHA_ENDPOINT não definidos.")
        return False

    url = f"{WAHA_ENDPOINT}/api/sendFile"
    # Apenas a chave da API é necessária no header
    headers = {
        "X-Api-Key": WAHA_API_KEY
    }
    filename = os.path.basename(filepath)

    try:
        data_relatorio = filename.split('_')[-1].replace('.png', '').replace('-', '/')
        caption_completo = f"{CAPTION} ({data_relatorio})"
    except:
        caption_completo = CAPTION

    try:
        with open(filepath, "rb") as image_file:
            # Todos os dados, incluindo a 'session', são enviados como multipart/form-data
            files = {
                'file': (filename, image_file, 'image/png'),
                'chatId': (None, WAHA_GROUP_ID),
                'caption': (None, caption_completo),
                'session': (None, "default")  # <- O parâmetro 'session' está aqui
            }

            print(f"INFO: [WAHA] Enviando arquivo '{filename}' para o grupo {WAHA_GROUP_ID}...")
            response = requests.post(url, files=files, headers=headers, timeout=60)

            if response.status_code in [200, 201]:
                print(f"✅ Imagem '{filename}' enviada com sucesso!")
                return True
            else:
                print(f"❌ Falha ao enviar imagem. Status: {response.status_code}, Resposta: {response.text}")
                return False

    except FileNotFoundError:
        print(f"❌ ERRO: O arquivo de imagem '{filename}' não foi encontrado.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ocorreu um erro de conexão ao tentar enviar a imagem: {e}")
        return False

    """Envia uma imagem para o grupo configurado via API do WAHA."""
    if not all([WAHA_GROUP_ID, WAHA_API_KEY, WAHA_ENDPOINT]):
        print("❌ ERRO: WAHA_GROUP_ID, WAHA_API_KEY ou WAHA_ENDPOINT não definidos.")
        return False

    url = f"{WAHA_ENDPOINT}/api/sendFile"
    # O header 'X-Session-Id' foi removido. Apenas a chave da API é necessária.
    headers = {
        "X-Api-Key": WAHA_API_KEY
    }
    filename = os.path.basename(filepath)

    try:
        # Monta a legenda da imagem
        data_relatorio = filename.split('_')[-1].replace('.png', '').replace('-', '/')
        caption_completo = f"{CAPTION} ({data_relatorio})"
    except:
        caption_completo = CAPTION

    try:
        with open(filepath, "rb") as image_file:
            # Todos os dados, incluindo a 'session', são enviados como multipart/form-data
            files = {
                'file': (filename, image_file, 'image/png'),
                'chatId': (None, WAHA_GROUP_ID),
                'caption': (None, caption_completo),
                'session': (None, "default")  # <--- CORREÇÃO APLICADA AQUI
            }

            print(f"INFO: [WAHA] Enviando arquivo '{filename}' para o grupo {WAHA_GROUP_ID}...")
            # O parâmetro 'data' foi removido, pois todos os dados já estão em 'files'
            response = requests.post(url, files=files, headers=headers, timeout=60)

            if response.status_code in [200, 201]:
                print(f"✅ Imagem '{filename}' enviada com sucesso!")
                return True
            else:
                print(f"❌ Falha ao enviar imagem. Status: {response.status_code}, Resposta: {response.text}")
                return False

    except FileNotFoundError:
        print(f"❌ ERRO: O arquivo de imagem '{filename}' não foi encontrado.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ocorreu um erro de conexão ao tentar enviar a imagem: {e}")
        return False

def main():
    if not wait_for_session_ready(WAHA_ENDPOINT, "default", WAHA_API_KEY):
        sys.exit(1)

    try:
        files_in_output = os.listdir(OUTPUT_DIR)
    except FileNotFoundError:
        print(f"AVISO: O diretório de output '{OUTPUT_DIR}' não foi encontrado.")
        files_in_output = []
        
    reports_to_send = [f for f in files_in_output if f.startswith("Relatorio_") and f.endswith(".png")]
    
    if not reports_to_send:
        print("INFO: Nenhum novo relatório encontrado para enviar.")
    else:
        print(f"INFO: {len(reports_to_send)} relatório(s) encontrado(s) para enviar.")
        sucesso_total = True
        for filename in sorted(reports_to_send):
            filepath = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(filepath + SENT_MARKER):
                print(f"INFO: O arquivo '{filename}' já foi enviado anteriormente. Pulando.")
                continue

            # --- LINHA CORRIGIDA ---
            # O nome da função foi corrigido para 'enviar_imagem_whatsapp'
            # e agora passa apenas o argumento 'filepath', como a função espera.
            success = enviar_imagem_whatsapp(filepath)
            # --- FIM DA CORREÇÃO ---

            if success:
                with open(filepath + SENT_MARKER, 'w') as f:
                    pass
                print(f"INFO: Arquivo marcado como enviado para evitar reenvio.")
            else:
                sucesso_total = False
                print(f"AVISO: O envio de '{filename}' falhou.")
            time.sleep(3)
        
        if not sucesso_total:
             sys.exit(1)
             
    print("\nINFO: Script de envio para WhatsApp finalizado.")

if __name__ == "__main__":
    main()
