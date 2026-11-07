"""Nodos, poda de ciclos por rama y construcción de resultados."""
import time

class Nodo:
    """
    Una 'parada' en el árbol de búsqueda. Además del estado, recuerda de dónde vino,
    para poder reconstruir el camino completo al final.
    """
    # __slots__ hace que cada nodo ocupe menos memoria (importa cuando hay cientos de miles de nodos)
    __slots__ = ("estado", "nodo_padre", "movimiento", "costo_acumulado", "profundidad")

    def __init__(self, estado, nodo_padre=None, movimiento=None, costo_acumulado=0):
        self.estado = estado
        self.nodo_padre = nodo_padre
        self.movimiento = movimiento              # movimiento que se hizo para llegar aquí
        self.costo_acumulado = costo_acumulado
        self.profundidad = 0 if nodo_padre is None else nodo_padre.profundidad + 1

    def camino_desde_la_raiz(self):
        """Devuelve la lista de nodos desde el inicio hasta este nodo, siguiendo los padres hacia atrás."""
        camino = []
        nodo = self
        while nodo is not None:
            camino.append(nodo)
            nodo = nodo.nodo_padre
        camino.reverse()
        return camino


def llego_a_un_evento(problema, nodo):
    """
    Después de un evento ( se subió a la avioneta, llegó al depósito o trató un cultivo seco) el robot SI puede devolverse por donde vino.
    """
    padre = nodo.nodo_padre
    if padre is None:
        return False                                   # la raíz no tiene evento
    estado = nodo.estado
    se_subio_a_la_avioneta = (padre.estado.combustible_avioneta is None
                              and estado.combustible_avioneta is not None)
    llego_al_deposito = (estado.fila, estado.columna) == problema.posicion_deposito
    trato_un_cultivo = len(estado.cultivos_secos) < len(padre.estado.cultivos_secos)
    return se_subio_a_la_avioneta or llego_al_deposito or trato_un_cultivo


def forma_ciclo(problema, nodo, estado_hijo):
    """
    EVITAR CICLOS.
    Se recorre la rama hacia atrás (nodo, padre, abuelo, ...). Si la casilla del hijo ya se pisó
    en esa rama, el hijo formaría un ciclo y se descarta.
    El recorrido se detiene en el último evento (avioneta, depósito o cultivo tratado): lo que pasó
    antes del evento no cuenta, y así el robot puede devolverse por donde vino.
    """
    casilla_del_hijo = (estado_hijo.fila, estado_hijo.columna)
    actual = nodo
    while actual is not None:
        if (actual.estado.fila, actual.estado.columna) == casilla_del_hijo:
            return True                                # ya pisó esa casilla: sería un ciclo
        if llego_a_un_evento(problema, actual):
            return False                               # antes de aquí no cuenta: puede devolverse
        actual = actual.nodo_padre
    return False


def armar_resultado(nodo_meta, nodos_expandidos, profundidad_maxima, hora_de_inicio,
                    limite_superado=False):
    """
    Arma el diccionario que leen el reporte y la animación.
    nodo_meta=None si no hubo solución; limite_superado=True si se detuvo por el límite de nodos
    """
    resultado = {
        "exito": nodo_meta is not None,
        "limite_superado": limite_superado,
        "nodos_expandidos": nodos_expandidos,
        "profundidad": profundidad_maxima,                 # la del árbol (el nodo más profundo creado)
        "tiempo": time.perf_counter() - hora_de_inicio,
    }
    if nodo_meta is not None:
        camino = nodo_meta.camino_desde_la_raiz()
        resultado["estados"] = [n.estado for n in camino]
        resultado["costos_acumulados"] = [n.costo_acumulado for n in camino]
        resultado["movimientos"] = [n.movimiento for n in camino[1:]]   # la raíz no tiene movimiento
        resultado["costo_total"] = nodo_meta.costo_acumulado
        resultado["profundidad_solucion"] = nodo_meta.profundidad      # cuántos pasos tiene la solución
    return resultado


