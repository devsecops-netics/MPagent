# Usa una imagen oficial de Python ligera
FROM python:3.14-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copia el archivo de dependencias (si existe) y lo instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código del proyecto al contenedor
COPY . .

# Expone el puerto que está usando el servidor
EXPOSE 80

# Variable de entorno para evitar que Python escriba archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Variable de entorno para que los logs de Python se muestren sin buffer
ENV PYTHONUNBUFFERED=1

# Ejecuta el comando de ADK apuntando a la carpeta de trabajo /app,
# asumiendo que "my_agent" está dentro de /app.
# IMPORTANTE: El comando ADK web <directorio_padre> espera la ruta al
# directorio que CONTIENE tu carpeta "my_agent".
CMD ["adk", "web", ".", "--host", "0.0.0.0", "--port", "80"]
