FROM python:3.10-slim

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && apt-get clean

# Crea carpeta de trabajo
WORKDIR /app

# Copia todo el proyecto
COPY . /app

# Instala Python deps
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expón el puerto
EXPOSE 8000

# Comando para arrancar la app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]