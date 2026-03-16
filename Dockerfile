# Dockerfile para executar a API Power Solis
# Base leve com Python 3.12 (mais recomendada para machine learning)

FROM python:3.12-slim

# Definindo diretório de trabalho dentro do container
WORKDIR /app

# Copiando apenas os arquivos necessários para reduzir o cache
COPY requirements.txt ./

# Instala dependências Python
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copiando código da aplicação
COPY . /app

# Expor porta usada pelo Uvicorn (80 para compatibilidade com Easypanel)
EXPOSE 80

# Comando default para iniciar a API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
