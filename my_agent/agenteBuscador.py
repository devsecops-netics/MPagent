import httpx
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Union, Dict
from google.adk.agents.llm_agent import Agent


def get_today_date_str() -> str:
    """Retorna la fecha de hoy en formato DDMMYYYY para la API."""
    return datetime.now().strftime("%d%m%Y")


def get_date_range_str(days_back: int) -> List[str]:
    """Retorna una lista de fechas desde hace N días hasta hoy en formato DDMMYYYY."""
    today = datetime.now()
    return [(today - timedelta(days=i)).strftime("%d%m%Y") for i in range(days_back + 1)]


def load_properties(filepath: str) -> Dict[str, str]:
    properties = {}
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        properties[key.strip()] = value.strip()
    return properties


# Cargar configuración
config_path = os.path.join(os.path.dirname(__file__), "config.properties")
config = load_properties(config_path)
API_LICITACION_URL= config.get("API_LICITACION_URL", "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json")
API_ORDENESDECOMPRA_URL= config.get("API_ORDENESDECOMPRA_URL")
TICKET = config.get("TICKET", "F8537A18-6766-4DEF-9E59-426B4FEE2844")


def _fetch_api_data(url: str, description: str) -> Union[Dict, List]:
    """
    Función de utilidad (helper) para realizar peticiones GET a la API con manejo estandarizado de errores.

    Args:
        url (str): La URL completa a consultar.
        description (str): Descripción para los logs.

    Returns:
        dict | list: Los datos en formato JSON retornados por la API, o un diccionario con el detalle del error.
    """
    print(f"{description}: {url}")
    try:
        with httpx.Client() as client:
            response = client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {
            "error": f"Error de HTTP: {e.response.status_code}",
            "detail": e.response.text
        }
    except Exception as e:
        return {"error": f"Error inesperado en {description}: {str(e)}"}


def getLicitacionPorCodigo(codigo: str) -> Union[Dict, List]:
    """
    Obtiene la información de una licitación específica según su código.

    Args:
        codigo (str): El código único de la licitación.

    Returns:
        dict | list: Resultado de la API con los detalles de la licitación.
    """
    url = f"{API_LICITACION_URL}?codigo={codigo}&ticket={TICKET}"
    return _fetch_api_data(url, f"Buscando licitaciones por codigo '{codigo}'")

def busqueda_diaria(search_term: Optional[str] = None, fecha: Optional[str] = None) -> Union[Dict, List]:
    """
    Realiza una búsqueda de licitaciones en Mercado Público solo por ticket como resultado trae todo lo del dia sino se especifica un rango de fechas.

    Args:
        search_term (str, optional): Término de búsqueda para filtrar las licitaciones por nombre.
        fecha (str, optional): Fecha en formato DDMMYYYY. Si no se provee, usa la fecha de hoy.

    Returns:
        dict | list: Resultado de la API o lista filtrada.
    """
    if not fecha:
        fecha = get_today_date_str()

    url = f"{API_LICITACION_URL}?fecha={fecha}&ticket={TICKET}"
    data = _fetch_api_data(url, f"Buscando en fecha {fecha}")

    # Si la petición fue exitosa (no retornó un error estructurado) y hay término de búsqueda, filtramos
    if isinstance(data, dict) and "error" not in data and search_term:
        return getCodeFromDescription(data, search_term)
    return data



def getLicitacionEstadoDiaActual(estado: str, fecha: Optional[str] = None) -> Union[Dict, List]:
    """
    Obtiene las licitaciones por estado.

    Args:
        estado (str): Estado de la licitación (ej. 'activas', 'publicadas').
        fecha (str, optional): Fecha en formato DDMMYYYY.

    Returns:
        dict | list: Resultado de la API.
    """
    url = f"{API_LICITACION_URL}?estado={estado}&ticket={TICKET}&fecha={fecha}" if fecha else f"{API_LICITACION_URL}?estado={estado}&ticket={TICKET}"
    return _fetch_api_data(url, f"Buscando licitaciones en estado '{estado}'")





def getLicitacionPorCodigoProveedor(fecha: str, codigo_proveedor: str) -> Union[Dict, List]:
    """
    Obtiene las licitaciones para un proveedor segun su codigo

    Args:
        fecha (str): indica el dia a buscar
        codigo_proveedor (str): el codigo del proveedor registrado en MercadoPublico

    Returns:
        dict | list: Resultado de la API.
    """
    url = f"{API_LICITACION_URL}?CodigoProveedor={codigo_proveedor}&ticket={TICKET}&fecha={fecha}"
    return _fetch_api_data(url, f"Buscando licitaciones en estado '{codigo_proveedor}'")


def getLicitacionOrganismoPublico(fecha: str, cod_organismo_publico: str) -> Union[Dict, List]:
    """
    Licitaciones de un organismo público específico

    Args:
        fecha (str): indica el dia a buscar
        cod_organismo_publico (str): el codigo del organismo publico que libera la licitacion

    Returns:
        dict | list: Resultado de la API.
    """
    url = f"{API_LICITACION_URL}?CodigoOrganismo={cod_organismo_publico}&ticket={TICKET}&fecha={fecha}"
    return _fetch_api_data(url, f"Buscando licitaciones en estado '{cod_organismo_publico}'")



def getCodeFromDescription(data: dict, search_term: str) -> list:
    """
    Filtra el JSON de respuesta por el nombre de la licitación y devuelve los códigos externos.

    Args:
        data (dict): El JSON devuelto por la API de Mercado Público.
        search_term (str): El criterio de búsqueda (término contenido en Listado.Nombre).

    Returns:
        list: Una lista de diccionarios con Nombre y CodigoExterno de las licitaciones que coinciden.
    """
    print("entre a buscar el termino que me dijiste...", search_term)

    if "Listado" not in data or data["Listado"] is None:
        return [{"error": "No se encontraron licitaciones en los datos proporcionados."}]

    results = []
    search_term_lower = search_term.lower()

    for licitacion in data["Listado"]:
        nombre = licitacion.get("Nombre", "")
        if search_term_lower in nombre.lower():
            results.append({
                "Nombre": nombre,
                "CodigoExterno": licitacion.get("CodigoExterno", "No disponible")
            })
            print(f"Licitación encontrada: {nombre} | Código: {licitacion.get('CodigoExterno')}")

    return results if results else [{"message": f"No se encontraron licitaciones que coincidan con '{search_term}'"}]


def obtener_detalles_exportar(codigo: str) -> Union[Dict, List]:
    """
    Obtiene los detalles de una licitación específica usando su código y exporta el resultado a un archivo JSON local.

    Args:
        codigo (str): El código de la licitación.

    Returns:
        dict: Resultado de la API con los detalles de la licitación o un mensaje de error.
    """
    url = f"{API_LICITACION_URL}?codigo={codigo}&ticket={TICKET}"
    data = _fetch_api_data(url, f"Obteniendo detalles para el código {codigo}")

    if isinstance(data, dict) and "error" not in data:
        filename = f"detalle_licitacion_{codigo}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f'Detalles exportados exitosamente a {filename}')
            return {"status": "success", "message": f"Archivo exportado a {filename}", "data": data}
        except Exception as e:
            return {"error": f"Error guardando el archivo {filename}: {str(e)}"}

    return data


def get_codigo_proveedor(rut_empresa: str) -> Union[Dict, List]:
    """
    Obtiene el código de proveedor asociado a un RUT de empresa.

    Args:
        rut_empresa (str): El RUT de la empresa proveedora.

    Returns:
        dict | list: Resultado de la API con la información del proveedor.
    """
    url = f"{API_LICITACION_URL}?rutempresaproveedor={rut_empresa}&ticket={TICKET}"
    return _fetch_api_data(url, f"Buscando código de proveedor para RUT '{rut_empresa}'")


def get_comprador() -> Union[Dict, List]:
    """
    Busca información de un comprador por su RUT.

    Returns:
        dict | list: Resultado de la API con la información del comprador.
    """
    url = f"https://api.mercadopublico.cl/servicios/v1/Publico/Empresas/BuscarComprador?ticket={TICKET}"
    return _fetch_api_data(url, f"Recuperando listado de compradores")


##Seccion para endpoint Ordenes de compra
## Aún en desarrollo


def getOCByCodigo(codigo: str) -> Union[Dict, List]:
    """
    Busca información por el codigo de Orden de Compra

    Returns:
        dict | list: Resultado de la API con la información de la orden
    """
    url = f"{API_ORDENESDECOMPRA_URL}?codigo={codigo}&ticket={TICKET}"
    return _fetch_api_data(url, f"Recuperando orden de Compras por codigo: {codigo}")


def getOCDiaActual() -> Union[Dict, List]:
    """
    Devuelve tolas OC del dia que esten en curso

    Returns:
        dict | list: Resultado de la API con la información de la orden
    """
    url = f"{API_ORDENESDECOMPRA_URL}?estado=todos&ticket={TICKET}"
    return _fetch_api_data(url, f"Recuperando orden de Compras del Dia actual: ")


def getOCPorFecha(fecha: str) -> Union[Dict, List]:
    """
    Trae las ordenes de compra de una fecha en especifico

    Returns:
        dict | list: Resultado de la API con la información de la orden
    """
    url = f"{API_ORDENESDECOMPRA_URL}?fecha={fecha}&ticket={TICKET}"
    return _fetch_api_data(url, f"Recuperando orden de Compras de la fecha: {fecha}")


def getOCPorFechayEstado(fecha: str, estado: str) -> Union[Dict, List]:
    """
    Trae las Ordenes de compra por Fecha y estado indicados

    Returns:
        dict | list: Resultado de la API con la información de la orden
    """
    url = f"{API_ORDENESDECOMPRA_URL}?fecha={fecha}&ticket={TICKET}&estado={estado}"
    return _fetch_api_data(url, f"Recuperando orden de Compras del Dia {fecha} con estado: {estado}")


def getOCPorCodigoOrganismo(fecha: str, codigo: str) -> Union[Dict, List]:
    """
    Recupera OC emitidas por un Organismo Publico

    Returns:
        dict | list: Resultado de la API con la información de la orden
    """
    url = f"{API_ORDENESDECOMPRA_URL}?fecha={fecha}&ticket={TICKET}&CodigoOrganismo={codigo}"
    return _fetch_api_data(url, f"Recuperando orden de Compras emitidas por el organismo: {codigo}")

def getOCPorCodigoProveedor(fecha: str, codigo_proveedor: str) -> Union[Dict, List]:
    """
    Recupera OC emitidas por un proveedor segun su codigo

    Returns:
        dict | list: Resultado de la API con la información de la orden
    """
    url = f"{API_ORDENESDECOMPRA_URL}?fecha={fecha}&ticket={TICKET}&CodigoProveedor={codigo_proveedor}"
    return _fetch_api_data(url, f"Recuperando orden de Compras emitidas por el proveedor: {codigo_proveedor}")

agente_buscador = Agent(
    model='gemini-2.5-flash',
    name='agente_buscador',
    description="Buscare en el mercado los terminos que me digas y del dia de hoy",
    instruction=(
        "Tu rol como asistente sera de buscar en el dentro de Mercado Publico usando la API que esta disponible licitaciones del dia y me filtraras por criterios, realiza estas operaciones: "
        "1. Usa 'busqueda_diaria' pasándole el término de búsqueda del usuario (search_term) para obtener el listado de licitaciones ya filtradas. "
        "2. Cuando tengas el listado, llamaras a 'obtener_detalles_exportar' para tomar el Codigo de Licitacion, consultar su detalle y sacarme un archivo con los detalles "
        "3. Usa 'getLicitacionEstadoDiaActual' si te pido licitaciones por estado (ej. activas, publicadas), recuerdame que al buscar asi segun la API serán las del dia."
        "4. Usa 'getLicitacionPorCodigo' para buscar la información puntual de una licitación."
        "5. Usa 'getLicitacionOrganismoPublico' cuando te pida buscar licitaciones de una institución u organismo específico."
        "6. Usa 'getLicitacionPorCodigoProveedor' cuando se te pida buscar licitaciones de un proveedor específico."
        "7. Usa 'get_codigo_proveedor' para obtener el código de un proveedor a partir de su RUT."
        "8. Usa 'get_comprador' para buscar un listado de compradores devolviendo nombre y codigo de empresa."
        "9. Para buscar Órdenes de Compra (OC), puedes usar las siguientes herramientas:"
        "   - 'getOCByCodigo' para buscar una OC específica por su código."
        "   - 'getOCDiaActual' para obtener las OC del día actual en curso."
        "   - 'getOCPorFecha' para buscar OC en una fecha específica (formato DDMMYYYY)."
        "   - 'getOCPorFechayEstado' para buscar OC filtrando por fecha y estado (ej. aceptada, enviada)."
        "   - 'getOCPorCodigoOrganismo' para buscar OC emitidas por un organismo público en una fecha."
        "   - 'getOCPorCodigoProveedor' para buscar OC emitidas a un proveedor en una fecha."
        "Puedes hacerme sugerencias de mejoras."
    ),
    tools=[
        busqueda_diaria,
        getCodeFromDescription,
        obtener_detalles_exportar,
        getLicitacionEstadoDiaActual,
        getLicitacionPorCodigo,
        getLicitacionOrganismoPublico,
        getLicitacionPorCodigoProveedor,
        get_codigo_proveedor,
        get_comprador,
        getOCByCodigo,
        getOCDiaActual,
        getOCPorFecha,
        getOCPorFechayEstado,
        getOCPorCodigoOrganismo,
        getOCPorCodigoProveedor
    ],
)