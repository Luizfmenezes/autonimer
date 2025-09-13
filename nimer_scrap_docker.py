import os
import sys
import time
import requests
from datetime import datetime, timedelta

# --- Bibliotecas para a automação ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# --- CONFIGURAÇÕES GERAIS ---
URL_LOGIN = "https://sistema.nimer.com.br/Identity/Account/Login?ReturnUrl=/"
URL_DASHBOARD = "https://sistema.nimer.com.br/Dashboard/Lines"
OUTPUT_DIR = "/app/output"

# --- LISTA DE LINHAS ALVO (BASEADA NO SEU SCRIPT FUNCIONAL) ---
LINHAS_ALVO = [
    "1017-10", "1020-10", "1024-10", "1025-10", "1026-10",
    "8015-10", "8016-10", "848L-10", "9784-10"
]

# --- CONFIGURAÇÕES DA API ---
USUARIO = os.getenv("NIMER_USER")
SENHA = os.getenv("NIMER_PASS")
WAHA_ENDPOINT = os.getenv("WAHA_ENDPOINT")
WAHA_GROUP_ID = os.getenv("WAHA_GROUP_ID")
WAHA_API_KEY = os.getenv("WAHA_API_KEY")

# --- FUNÇÕES DO WHATSAPP ---
def wait_for_session_ready(api_url, session_name, api_key, timeout_seconds=180):
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
        except requests.exceptions.RequestException:
            print("AVISO: API do WAHA ainda não está respondendo, aguardando...")
        time.sleep(10)
    print(f"❌ ERRO CRÍTICO: A sessão '{session_name}' não conectou a tempo.")
    return False

# --- FUNÇÃO DE FORMATAÇÃO ATUALIZADA PARA OS DADOS DE PROGRESSO ---
def formatar_mensagem_texto(dados, data_pesquisa):
    print("INFO: Formatando mensagem de texto do relatório...")
    dados_ordenados = sorted(dados, key=lambda x: x.get('linha', ''))
    mensagem_partes = [f"📊 *Resumo de Fotos e Pendências: {data_pesquisa}*", ""]

    for item in dados_ordenados:
        linha = item.get('linha', 'N/A')
        fotos = float(item.get('fotos_pct', 0))
        pendencias = float(item.get('pendencias_pct', 0))
        
        # Emoji para status rápido
        status_emoji = "✅" if fotos > 90 else "⚠️" if fotos > 70 else "❌"

        mensagem_partes.append(f"{status_emoji} *LINHA: {linha}*")
        mensagem_partes.append(f"  - _Fotos_: {fotos:.1f}%")
        mensagem_partes.append(f"  - _Pendências_: {pendencias:.1f}%")
        mensagem_partes.append("")

    if len(mensagem_partes) <= 2: return None
    mensagem_final = "\n".join(mensagem_partes)
    print("✅ Mensagem formatada com sucesso.")
    return mensagem_final

def enviar_texto_whatsapp(mensagem):
    if not all([WAHA_GROUP_ID, WAHA_API_KEY, WAHA_ENDPOINT]):
        print("❌ ERRO: WAHA_GROUP_ID, WAHA_API_KEY ou WAHA_ENDPOINT não definidos.")
        return False
    url = f"{WAHA_ENDPOINT}/api/sendText"
    headers = {"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"}
    payload = {"session": "default", "chatId": WAHA_GROUP_ID, "text": mensagem}
    try:
        print(f"INFO: [WAHA] Enviando relatório para o grupo {WAHA_GROUP_ID}...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code in [200, 201]:
            print("✅ Relatório em texto enviado com sucesso!")
            return True
        else:
            print(f"❌ Falha ao enviar texto. Status: {response.status_code}, Resposta: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ocorreu um erro de conexão ao tentar enviar o texto: {e}")
        return False

# --- FUNÇÕES DA AUTOMAÇÃO (SELENIUM) ---
def iniciar_driver():
    print("INFO: Iniciando o WebDriver do Chrome em modo headless...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def fazer_login(driver, wait, usuario, senha):
    try:
        print("INFO: Acessando a página de login...")
        driver.get(URL_LOGIN)
        wait.until(EC.visibility_of_element_located((By.ID, "Input_UserName"))).send_keys(usuario)
        driver.find_element(By.ID, "Input_Password").send_keys(senha)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/Identity/Account/Logout')]")))
        print("✅ Login bem-sucedido.")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"❌ ERRO inesperado durante o login: {e}")
        return False

def filtrar_por_data(driver, wait, data_filtro):
    try:
        print(f"INFO: Navegando e aplicando filtro para a data {data_filtro}...")
        driver.get(URL_DASHBOARD)
        date_input = wait.until(EC.visibility_of_element_located((By.ID, "Date")))
        date_input.clear()
        date_input.send_keys(data_filtro)
        update_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'main-button') and text()='Atualizar']")))
        update_button.click()
        print("INFO: Aguardando o carregamento dos dados das linhas...")
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".searchable-card h2")))
        print(f"✅ Filtro para {data_filtro} aplicado e dados carregados.")
        return True
    except TimeoutException:
        print(f"AVISO: Tempo esgotado. Nenhum dado de linha foi carregado para o dia {data_filtro}.")
        return False
    except Exception as e:
        print(f"❌ ERRO inesperado ao filtrar pela data {data_filtro}: {e}")
        return False

# --- FUNÇÃO AUXILIAR PARA EXTRAIR VALOR DA BARRA DE PROGRESSO ---
def _extrair_valor_progresso(style_attribute):
    try:
        parts = style_attribute.split(';')
        for part in parts:
            if '--value:' in part:
                return part.split(':')[1].strip()
        return "0"
    except:
        return "0"

# --- FUNÇÃO DE EXTRAÇÃO ATUALIZADA COM A LÓGICA QUE FUNCIONA ---
def extrair_dados_das_linhas(driver):
    print("INFO: Extraindo dados das barras de progresso...")
    dados_extraidos = []
    cards = driver.find_elements(By.CLASS_NAME, "searchable-card")

    for card in cards:
        try:
            nome_linha = card.find_element(By.TAG_NAME, "h2").text
            if nome_linha in LINHAS_ALVO:
                barras_progresso = card.find_elements(By.TAG_NAME, "progress")
                pct_fotos = "0"
                pct_pendencias = "0"
                if len(barras_progresso) >= 2:
                    pct_fotos = _extrair_valor_progresso(barras_progresso[0].get_attribute("style"))
                    pct_pendencias = _extrair_valor_progresso(barras_progresso[1].get_attribute("style"))
                
                print(f"  - Linha {nome_linha}: Fotos {pct_fotos}%, Pendências {pct_pendencias}%")
                dados_extraidos.append({"linha": nome_linha, "fotos_pct": pct_fotos, "pendencias_pct": pct_pendencias})
        except NoSuchElementException:
            continue # Ignora cards que não têm o título h2, como esperado
        except Exception as e:
            print(f"AVISO: Ocorreu um erro inesperado ao processar um card. Erro: {e}")
            continue
            
    print(f"✅ Dados extraídos para {len(dados_extraidos)} linhas.")
    return dados_extraidos

# --- FUNÇÃO PRINCIPAL (SEM ALTERAÇÕES) ---
def main():
    if not all([USUARIO, SENHA, WAHA_ENDPOINT]):
        print("❌ ERRO CRÍTICO: Verifique as variáveis de ambiente.")
        sys.exit(1)
    if not wait_for_session_ready(WAHA_ENDPOINT, "default", WAHA_API_KEY):
        sys.exit(1)
    driver = None
    try:
        if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
        driver = iniciar_driver()
        wait = WebDriverWait(driver, 30)
        if not fazer_login(driver, wait, USUARIO, SENHA): raise Exception("Falha crítica no login.")
        hoje = datetime.now()
        datas_para_verificar = [(hoje - timedelta(days=i)) for i in range(1, 4)]
        for data_alvo in reversed(datas_para_verificar):
            data_str_filtro = data_alvo.strftime("%d/%m/%Y")
            data_str_arquivo = data_alvo.strftime("%d-%m-%Y")
            marcador_path = os.path.join(OUTPUT_DIR, f"enviado_{data_str_arquivo}.txt")
            print(f"\n{'='*70}\n## VERIFICANDO DIA: {data_str_filtro}\n{'='*70}")
            if os.path.exists(marcador_path):
                print(f"✅ INFO: Relatório do dia {data_str_filtro} já foi enviado. Pulando.")
                continue
            print(f"⚠️ AVISO: Relatório do dia {data_str_filtro} não foi enviado. Processando agora...")
            if filtrar_por_data(driver, wait, data_str_filtro):
                dados = extrair_dados_das_linhas(driver)
                if dados:
                    mensagem = formatar_mensagem_texto(dados, data_str_filtro)
                    if mensagem:
                        sucesso_envio = enviar_texto_whatsapp(mensagem)
                        if sucesso_envio:
                            with open(marcador_path, 'w') as f: f.write(datetime.now().isoformat())
                            print(f"✅ INFO: Marcador de envio criado para {data_str_filtro}.")
                else:
                    print(f"⚠️ Nenhum dado foi extraído para as linhas alvo no dia {data_str_filtro}.")
            else:
                print(f"⚠️ Falha ao filtrar os dados para {data_str_filtro}.")
            time.sleep(3)
    except Exception as e:
        print(f"❌ Ocorreu um erro fatal na automação: {e}")
    finally:
        if driver: driver.quit()
        print("\nINFO: Automação finalizada.")

if __name__ == "__main__":
    main()

