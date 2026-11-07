"""Búsquedas por amplitud, costo uniforme y profundidad."""
import heapq
import itertools
import time
from collections import deque

from model import LIMITE_NODOS_EXPANDIDOS
from .common import Nodo, forma_ciclo, armar_resultado

def busqueda_amplitud(problema):
    """
    Búsqueda preferente por amplitud (la frontera es una COLA):
    se revisan primero los nodos que se alcanzan con 1 paso, luego con 2 pasos, etc.
    Encuentra la solución con menos pasos.
    """
    hora_de_inicio = time.perf_counter()
    cola = deque([Nodo(problema.estado_inicial)])                                              # cola = nodo_raíz(problema)
    nodos_expandidos = 0
    profundidad_maxima = 0

    while True:                                                                                #loop
        if len(cola) == 0:                                                                     # if estaVacia(cola) then
            return armar_resultado(None, nodos_expandidos, profundidad_maxima, hora_de_inicio) #return fallo

        nodo = cola.popleft()                                                                  #n=sacar(cola)

        if problema.es_meta(nodo.estado):                                                      #if n es un nodo meta then
            return armar_resultado(nodo, nodos_expandidos, profundidad_maxima, hora_de_inicio) #return encontro solucion

        # Se expande: los hijos que no forman ciclo entran al FINAL de la cola
        if nodos_expandidos >= LIMITE_NODOS_EXPANDIDOS: # se rinde para no congelar el programa
            return armar_resultado(None, nodos_expandidos, profundidad_maxima, hora_de_inicio,
                                    limite_superado=True)
        nodos_expandidos += 1
        for movimiento, estado_hijo, costo in problema.sucesores(nodo.estado):                 #expandir n
            if forma_ciclo(problema, nodo, estado_hijo): #evitar ciclos
                continue
            hijo = Nodo(estado_hijo, nodo, movimiento, nodo.costo_acumulado + costo)
            profundidad_maxima = max(profundidad_maxima, hijo.profundidad)
            cola.append(hijo)                                                                  #meter hijo al final de la cola


def busqueda_costo_uniforme(problema):
    """
    Búsqueda de costo uniforme (la frontera es una COLA DE PRIORIDAD):
    siempre se expande el nodo con MENOR costo acumulado, no el de menos pasos.
    La meta se revisa al SACAR el nodo (no al crearlo); así la primera meta que sale es la más barata.
    """
    hora_de_inicio = time.perf_counter()

    # Cada elemento es (costo_acumulado, numero_de_llegada, nodo). El número de llegada solo
    # desempata: si dos nodos cuestan lo mismo, sale primero el que llegó antes.
    numero_de_llegada = itertools.count()
    cola_de_prioridad = [(0, next(numero_de_llegada), Nodo(problema.estado_inicial))]
    nodos_expandidos = 0
    profundidad_maxima = 0

    while True:
        if len(cola_de_prioridad) == 0:                    # se probó todo: no hay solución
            return armar_resultado(None, nodos_expandidos, profundidad_maxima, hora_de_inicio)

        _, _, nodo = heapq.heappop(cola_de_prioridad)      # sale el de MENOR costo

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
            heapq.heappush(cola_de_prioridad, (hijo.costo_acumulado, next(numero_de_llegada), hijo)) #meter hijo a la cola de prioridad, primero el que menos costo acumulado tenga


def busqueda_profundidad_evitando_ciclos(problema):
    """
    Búsqueda preferente por profundidad evitando ciclos (la frontera es una PILA):
    siempre sigue por el último nodo que entró, o sea, va lo más hondo posible antes de devolverse.
    No garantiza la solución más corta ni la más barata, solo encontrar una.
    """
    hora_de_inicio = time.perf_counter()
    pila = [Nodo(problema.estado_inicial)]                                      # pila = nodo raíz(problema)
    nodos_expandidos = 0
    profundidad_maxima = 0

    while True:                                                                 #loop
        if len(pila) == 0:                                                      #if estaVacia(pila) then
            return armar_resultado(None, nodos_expandidos, profundidad_maxima,  #return fallo
                                    hora_de_inicio)

        nodo = pila.pop()  #sale el último nodo que entró                       #n=pop(pila)

        if problema.es_meta(nodo.estado):                                       #if n es un nodo meta then
            return armar_resultado(nodo, nodos_expandidos, profundidad_maxima,  #return encontro solucion
                                   hora_de_inicio)

        if nodos_expandidos >= LIMITE_NODOS_EXPANDIDOS:    # se rinde para no congelar el programa
            return armar_resultado(None, nodos_expandidos, profundidad_maxima, hora_de_inicio,
                                   limite_superado=True)
        nodos_expandidos += 1
        hijos = [] #junta los hijos de este nodo, para meterlos todos a la pila de una vez
        for movimiento, estado_hijo, costo in problema.sucesores(nodo.estado): #expandir nodos
            if forma_ciclo(problema, nodo, estado_hijo): #evitar ciclos
                continue
            hijo = Nodo(estado_hijo, nodo, movimiento, nodo.costo_acumulado + costo)
            profundidad_maxima = max(profundidad_maxima, hijo.profundidad)
            hijos.append(hijo)

        # Push al revés, para que el primero en salir sea "arriba", luego "abajo", "izquierda", "derecha"
        pila.extend(reversed(hijos))


