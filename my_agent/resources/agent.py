import sys
import os

# Asegurar que el directorio padre esté en el path para poder importar desde ..
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agenteBuscador import agente_buscador

# La herramienta de ADK busca específicamente la variable "root_agent".
# Referenciamos tu agente_buscador como el root_agent.
root_agent = agente_buscador
