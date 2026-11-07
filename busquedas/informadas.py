"""Heurística Manhattan escalada y búsquedas avara y A*."""
import heapq
import itertools
import time

from model import LIMITE_NODOS_EXPANDIDOS
from .common import Nodo, forma_ciclo, armar_resultado

def heuristica(problema, estado):
    """
    h(n) = (distancia Manhattan al cultivo seco más cercano) / 2

    - Para terminar, el robot tiene que llegar por lo menos al cultivo seco más cercano.
    - Para eso necesita como mínimo tantos pasos como la distancia Manhattan (sin muros ni desvíos).
    - Cada paso cuesta como mínimo 1/2 (en avioneta).
    Por eso h(n) nunca es mayor que el costo real que falta: es admisible.
    Cuando ya no quedan cultivos secos (meta), h(n) = 0.
    """
    if len(estado.cultivos_secos) == 0:
        return 0
    distancia_al_mas_cercano = min(abs(estado.fila - fila) + abs(estado.columna - columna)
                                   for fila, columna in estado.cultivos_secos)
    return distancia_al_mas_cercano / 2


def busqueda_avara(problema):
    """
    Búsqueda avara (la frontera es una COLA DE PRIORIDAD ordenada por h(n)):
    siempre expande el nodo que PARECE estar más cerca de la meta, sin mirar lo que ya gastó.
    Suele expandir pocos nodos, pero no garantiza la solución más barata.
    """
    hora_de_inicio = time.perf_counter()
    numero_de_llegada = itertools.count()          # desempate: si empatan, sale el que llegó antes
    raiz = Nodo(problema.estado_inicial)
    cola_de_prioridad = [(heuristica(problema, raiz.estado), next(numero_de_llegada), raiz)]
    nodos_expandidos = 0
    profundidad_maxima = 0

    while True:
        if len(cola_de_prioridad) == 0:                    # se probó todo: no hay solución
            return armar_resultado(None, nodos_expandidos, profundidad_maxima, hora_de_inicio)

        _, _, nodo = heapq.heappop(cola_de_prioridad)      # sale el de MENOR h(n)

        if problema.es_meta(nodo.estado):
            return armar_resultado(nodo, nodos_expandidos, profundidad_maxima, hora_de_inicio)

        if nodos_expandidos >= LIMITE_NODOS_EXPANDIDOS:    # se rinde para no congelar el programa
            return armar_resultado(None, nodos_expandidos, profundidad_maxima, hora_de_inicio,
                                   limite_superado=True)
        nodos_expandidos += 1
        for movimiento, estado_hijo, costo in problema.sucesores(nodo.estado): #expandir nodos
            if forma_ciclo(problema, nodo, estado_hijo): #evitar ciclos
                continue
            hijo = Nodo(estado_hijo, nodo, movimiento, nodo.costo_acumulado + costo)
            profundidad_maxima = max(profundidad_maxima, hijo.profundidad)
            h = heuristica(problema, estado_hijo)
            heapq.heappush(cola_de_prioridad, (h, next(numero_de_llegada), hijo)) #meter hijo a la cola de prioridad, primero el que menos h(n) tenga


def busqueda_a_estrella(problema):
    """
    Búsqueda A* (la frontera es una COLA DE PRIORIDAD ordenada por f(n) = g(n) + h(n)):
      g(n) = costo acumulado desde el inicio (lo que ya gastó)
      h(n) = heurística (lo que estima que le falta)
    Con una heurística admisible, la primera meta que sale de la cola es la de menor costo.
    """
    hora_de_inicio = time.perf_counter()
    numero_de_llegada = itertools.count()
    raiz = Nodo(problema.estado_inicial)
    cola_de_prioridad = [(0 + heuristica(problema, raiz.estado), next(numero_de_llegada), raiz)]
    nodos_expandidos = 0
    profundidad_maxima = 0

    while True:
        if len(cola_de_prioridad) == 0:                    # se probó todo: no hay solución
            return armar_resultado(None, nodos_expandidos, profundidad_maxima, hora_de_inicio)

        _, _, nodo = heapq.heappop(cola_de_prioridad)      # sale el de MENOR f(n)

        if problema.es_meta(nodo.estado):                  # la meta se revisa al SACAR el nodo
            return armar_resultado(nodo, nodos_expandidos, profundidad_maxima, hora_de_inicio)

        if nodos_expandidos >= LIMITE_NODOS_EXPANDIDOS:    # se rinde para no congelar el programa
            return armar_resultado(None, nodos_expandidos, profundidad_maxima, hora_de_inicio,
                                   limite_superado=True)
        nodos_expandidos += 1
        for movimiento, estado_hijo, costo in problema.sucesores(nodo.estado): #expandir nodos
            if forma_ciclo(problema, nodo, estado_hijo): #evitar ciclos
                continue
            hijo = Nodo(estado_hijo, nodo, movimiento, nodo.costo_acumulado + costo)
            profundidad_maxima = max(profundidad_maxima, hijo.profundidad)
            f = hijo.costo_acumulado + heuristica(problema, estado_hijo)     # f(n) = g(n) + h(n)
            heapq.heappush(cola_de_prioridad, (f, next(numero_de_llegada), hijo))


