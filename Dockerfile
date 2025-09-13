# Estágio 1: Imagem Base
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala o Google Chrome e o WebDriver necessários para o Selenium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Estágio 2: Dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Estágio 3: Aplicação
# Copia todo o projeto para o contêiner
COPY . .

# Define o comando padrão para executar o script principal
CMD ["python", "nimer_scrap_docker.py"]