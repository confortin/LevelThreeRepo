# Imagem do pipeline de defeitos de manufatura.
# Contexto de build: a raiz do repositorio, onde fica o requirements.txt
#   docker build -f projeto-tema2/Dockerfile -t levelthree-pipeline .
FROM python:3.12-slim

# Sem .pyc, logs sem buffer e matplotlib sem interface grafica (gera so arquivos)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

WORKDIR /app

# Dependencias primeiro, para aproveitar o cache de camadas do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# So o codigo entra na imagem; os dados entram por volume em /app/data
COPY projeto-tema2/src/ ./src/
RUN mkdir -p /app/data /app/output

CMD ["python", "src/pipeline.py"]
