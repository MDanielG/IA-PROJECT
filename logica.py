"""
AgroBot - Punto de acceso a la lógica para la interfaz.

El modelo está en modelo.py; las búsquedas y sus utilidades, en busquedas/.
Se conservan los nombres públicos, el catálogo y el trabajador del proceso.
"""
from model import (
    CASILLA_LIBRE,
    CASILLA_OBSTACULO,
    CASILLA_ROBOT,
    CASILLA_CULTIVO_SECO,
    CASILLA_DEPOSITO,
    CASILLA_AVIONETA,
    MOVIMIENTOS,
    COSTO_NORMAL,
    COSTO_EN_AVIONETA,
    COMBUSTIBLE_INICIAL_AVIONETA,
    FERTILIZANTE_MAXIMO,
    LIMITE_NODOS_EXPANDIDOS,
    VALORES_VALIDOS,
    SEPARADORES,
    leer_mundo,
    Estado,
    Problema,
)
from busquedas.common import Nodo, llego_a_un_evento, forma_ciclo, armar_resultado
from busquedas.no_informadas import (
    busqueda_amplitud, busqueda_costo_uniforme, busqueda_profundidad_evitando_ciclos,
)
from busquedas.informadas import heuristica, busqueda_avara, busqueda_a_estrella


ALGORITMOS_POR_TIPO = {
    "No informada": ["Amplitud", "Costo uniforme", "Profundidad evitando ciclos"],
    "Informada": ["Avara", "A*"],
}

ALGORITMOS = {
    "Amplitud": busqueda_amplitud,
    "Costo uniforme": busqueda_costo_uniforme,
    "Profundidad evitando ciclos": busqueda_profundidad_evitando_ciclos,
    "Avara": busqueda_avara,
    "A*": busqueda_a_estrella,
}

# Algoritmos para los que el enunciado pide mostrar el costo de la solución
ALGORITMOS_QUE_MUESTRAN_COSTO = ["Costo uniforme", "A*"]


def ejecutar_busqueda_en_proceso(nombre_algoritmo, problema, cola_de_resultados):
    """
    La interfaz corre la búsqueda en un proceso aparte (para que la ventana no se congele y para
    poder cancelarla). Este proceso solo corre el algoritmo y devuelve el resultado por la cola.
    """
    try:
        resultado = ALGORITMOS[nombre_algoritmo](problema)
        cola_de_resultados.put(("ok", resultado))
    except MemoryError:
        cola_de_resultados.put(("memoria", None))
    except Exception as error:                      # cualquier otro error se muestra en la ventana
        cola_de_resultados.put(("error", f"{type(error).__name__}: {error}"))
