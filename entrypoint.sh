#!/bin/sh
set -e

echo "========================================="
echo "==> INICIANDO PROCESSO DE AUTOMAÇÃO <=="
echo "========================================="

# Passo 1: Executar o script de extração de dados
echo "\n--- [ETAPA 1/2] Executando o script de extração (nimer_scrap_docker.py) ---"
python nimer_scrap_docker.py

# Passo 2: Executar o script de envio para o WhatsApp
echo "\n--- [ETAPA 2/2] Executando o script de envio (send_whatsapp.py) ---"
python send_whatsapp.py

echo "\n========================================="
echo "==> PROCESSO DE AUTOMAÇÃO FINALIZADO <=="
echo "========================================="