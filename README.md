
# PoC  - Agente para Licitaciones de Mercado Publico

Agente basado en plataforma ADK de google para generar un agente basado en Modelos de IA para utlizar API V1 de Mercado Publico y recuperar de forma mas rapida las licitaciones que pueden ser de atractivo.


## Run Locally

Clone the project

```bash
  git clone https://github.com/devsecops-netics/MPagent.git
```

Instalar las siguientes dependencias de Python en caso de ejecucion manual

```bash
  pip install --no-cache-dir -r requirements.txt
```

Ejecucion Local SIN docker
```bash
  adk run my_agent
```


Ejecucion CON docker
```bash
  docker build -t mi-agente-buscador .
  docker run -p 80:80 mi-agente-buscador
```

Abrir un navegador en la direccion lo cual ejecutara el agente en modo web
```bash
   localhost:80
```
