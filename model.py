"""Modelo de AgroBot: lectura del mundo, estado y reglas de transición."""
from typing import NamedTuple

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


