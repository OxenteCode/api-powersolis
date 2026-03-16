# Dockerfile para executar a API Power Solis
# Base leve com Python 3.13

FROM python:3.13-slim

# Definindo diretório de trabalho dentro do container
WORKDIR /app

# Copiando apenas os arquivos necessários para reduzir o cache
COPY requirements.txt ./

# Instala dependências Python
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copiando código da aplicação
COPY . /app

# Expor porta usada pelo Uvicorn
EXPOSE 8000

# Comando default para iniciar a API
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
