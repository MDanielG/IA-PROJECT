"""
AgroBot - Proyecto 1 de Inteligencia Artificial (Univalle)
Hecho por: Andres Muñoz, Thomas Herrera y Daniel Micolta

LÓGICA DEL PROYECTO (no tiene nada visual):
    1. MODELO DEL PROBLEMA: describe el mundo, los movimientos y las reglas del robot.
    2. BÚSQUEDAS (no informadas e informadas): encuentran la lista de pasos que resuelve el problema.
    3. CATÁLOGO DE ALGORITMOS: los nombres que muestra la interfaz y la función de cada uno.

La parte visual está en interfaz.py (ventana) y dibujos.py (íconos).
"""
import heapq
import itertools
import time
from collections import deque
from typing import NamedTuple

# =====================================================================================
# 1. MODELO DEL PROBLEMA
# =====================================================================================

# Números que aparecen en el archivo de texto
CASILLA_LIBRE = 0
CASILLA_OBSTACULO = 1
CASILLA_ROBOT = 2
CASILLA_CULTIVO_SECO = 3
CASILLA_DEPOSITO = 4
CASILLA_AVIONETA = 5

# Movimientos posibles: (nombre, cuánto cambia la fila, cuánto cambia la columna)
MOVIMIENTOS = [
    ("arriba",    -1,  0),
    ("abajo",      1,  0),
    ("izquierda",  0, -1),
    ("derecha",    0,  1),
]

# Reglas del enunciado
COSTO_NORMAL = 1
COSTO_EN_AVIONETA = 0.5
COMBUSTIBLE_INICIAL_AVIONETA = 30
FERTILIZANTE_MAXIMO = 2

# Como solo se evitan ciclos dentro de cada rama, en mapas abiertos (o sin solución) el árbol puede
# ser enorme. Si una búsqueda expande más nodos que este límite, se detiene y lo informa.
LIMITE_NODOS_EXPANDIDOS = 1_000_000


VALORES_VALIDOS = "012345"
SEPARADORES = ",;"          # además de espacios y tabulaciones


def leer_mundo(ruta_archivo):
    """
    Lee el archivo de texto y devuelve el mapa como una lista de filas (cada fila, una lista de números).
    Como cada casilla es un solo dígito (0 a 5), se acepta que vengan separados por espacios, tabulaciones,
    comas, punto y coma, o incluso pegados (1114111511).
    También acepta archivos guardados en UTF-8 con BOM o en "Unicode" (UTF-16) desde el Bloc de notas.
    """
    with open(ruta_archivo, "rb") as archivo:
        contenido = archivo.read()
    if contenido.startswith((b"\xff\xfe", b"\xfe\xff")):
        texto = contenido.decode("utf-16")
    else:
        texto = contenido.decode("utf-8-sig", errors="replace")   # utf-8-sig quita el BOM si lo hay

    mapa = []
    for numero_de_linea, linea in enumerate(texto.splitlines(), start=1):
        caracteres = [c for c in linea if not c.isspace() and c not in SEPARADORES]
        if not caracteres:
            continue                                               # ignora líneas vacías
        for caracter in caracteres:
            if caracter not in VALORES_VALIDOS:
                raise ValueError(f"Línea {numero_de_linea}: «{caracter}» no es válido. "
                                 f"Cada casilla debe ser un número del 0 al 5.")
        mapa.append([int(caracter) for caracter in caracteres])

    if not mapa:
        raise ValueError("El archivo está vacío.")
    columnas_por_fila = {len(fila) for fila in mapa}
    if len(columnas_por_fila) != 1:
        raise ValueError("Todas las filas del archivo deben tener la misma cantidad de columnas.")
    return mapa


class Estado(NamedTuple):
    """
    Una 'foto' de la situación del robot en un momento dado.
    Dos fotos iguales significan que la situación es exactamente la misma.
    """
    fila: int
    columna: int
    fertilizante: int                 # unidades que lleva el robot (0, 1 o 2)
    cultivos_secos: frozenset         # casillas (fila, columna) de los cultivos que aún faltan por tratar
    combustible_avioneta: object      # None = no se ha subido; 30..0 = ya se subió y esto es lo que le queda


class Problema:
    """Guarda el mapa y conoce las reglas: estado inicial, movimientos válidos y cuándo se ganó."""

    def __init__(self, mapa):
        self.mapa = mapa
        self.total_filas = len(mapa)
        self.total_columnas = len(mapa[0])
        self.posicion_inicial = None
        self.posicion_deposito = None
        self.posicion_avioneta = None
        self.cultivos_secos_iniciales = self._ubicar_elementos_del_mapa()

        # El robot siempre empieza sin fertilizante y sin haberse subido a la avioneta
        self.estado_inicial = Estado(
            fila=self.posicion_inicial[0],
            columna=self.posicion_inicial[1],
            fertilizante=0,
            cultivos_secos=self.cultivos_secos_iniciales,
            combustible_avioneta=None,
        )

    def _ubicar_elementos_del_mapa(self):
        """Recorre el mapa y guarda dónde están el robot, el depósito, la avioneta y los cultivos secos."""
        robots, depositos, avionetas, cultivos = [], [], [], []
        for fila in range(self.total_filas):
            for columna in range(self.total_columnas):
                valor = self.mapa[fila][columna]
                if valor == CASILLA_ROBOT:
                    robots.append((fila, columna))
                elif valor == CASILLA_DEPOSITO:
                    depositos.append((fila, columna))
                elif valor == CASILLA_AVIONETA:
                    avionetas.append((fila, columna))
                elif valor == CASILLA_CULTIVO_SECO:
                    cultivos.append((fila, columna))

        # Antes, si había dos robots o dos depósitos, se quedaba en silencio con el último.
        if len(robots) != 1:
            raise ValueError(f"El mundo debe tener exactamente un AgroBot (2) y tiene {len(robots)}.")
        if len(depositos) > 1 or len(avionetas) > 1:
            raise ValueError("El mundo debe tener un solo depósito (4) y una sola avioneta (5).")

        self.posicion_inicial = robots[0]
        # Si faltara el depósito o la avioneta, el programa igual funciona: sin depósito no hay
        # solución (salvo que no haya cultivos) y sin avioneta todos los movimientos cuestan 1.
        self.posicion_deposito = depositos[0] if depositos else None
        self.posicion_avioneta = avionetas[0] if avionetas else None
        return frozenset(cultivos)

    def es_meta(self, estado):
        """Se gana cuando ya no queda ningún cultivo seco."""
        return len(estado.cultivos_secos) == 0

    def casilla_es_transitable(self, fila, columna):
        """Una casilla se puede pisar si está dentro del mapa y no es un obstáculo."""
        dentro_del_mapa = 0 <= fila < self.total_filas and 0 <= columna < self.total_columnas
        return dentro_del_mapa and self.mapa[fila][columna] != CASILLA_OBSTACULO

    def sucesores(self, estado):
        """
        Dado un estado, entrega todos los estados a los que se puede llegar con UN movimiento.
        Por cada uno entrega: (nombre_del_movimiento, estado_nuevo, costo_del_movimiento).
        """
        for nombre, cambio_fila, cambio_columna in MOVIMIENTOS:
            nueva_fila = estado.fila + cambio_fila
            nueva_columna = estado.columna + cambio_columna

            if not self.casilla_es_transitable(nueva_fila, nueva_columna):
                continue                                   # choca con un muro o se sale del mapa

            # --- Costo del movimiento y combustible de la avioneta ---
            va_en_avioneta = estado.combustible_avioneta is not None and estado.combustible_avioneta > 0
            if va_en_avioneta:
                costo = COSTO_EN_AVIONETA
                combustible = estado.combustible_avioneta - 1
            else:
                costo = COSTO_NORMAL
                combustible = estado.combustible_avioneta

            # --- Lo que pasa automáticamente al llegar a la casilla nueva ---
            posicion = (nueva_fila, nueva_columna)
            fertilizante = estado.fertilizante
            cultivos_secos = estado.cultivos_secos

            if posicion == self.posicion_deposito:
                fertilizante = FERTILIZANTE_MAXIMO                 # recarga completa

            if posicion in cultivos_secos and fertilizante > 0:
                fertilizante -= 1                                  # usa una unidad
                cultivos_secos = cultivos_secos - {posicion}       # el cultivo ya queda tratado

            if posicion == self.posicion_avioneta and combustible is None:
                combustible = COMBUSTIBLE_INICIAL_AVIONETA         # se sube a la avioneta

            estado_nuevo = Estado(nueva_fila, nueva_columna, fertilizante, cultivos_secos, combustible)
            yield nombre, estado_nuevo, costo


# =====================================================================================
# 2. BÚSQUEDAS: AMPLITUD, COSTO UNIFORME, PROFUNDIDAD, AVARA Y A*
# =====================================================================================

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


# ----------------------------------- Búsquedas informadas -----------------------------------

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


# =====================================================================================
# 3. CATÁLOGO DE ALGORITMOS (lo usa la interfaz para armar los menús)
# =====================================================================================

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
