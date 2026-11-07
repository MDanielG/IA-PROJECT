"""
AgroBot - Íconos del tablero.

Todos los dibujos se hacen con figuras del Canvas de tkinter (no se necesitan imágenes aparte).
Cada función recibe:
    lienzo   -> el Canvas donde se dibuja
    x, y     -> esquina superior izquierda de la casilla
    tam      -> tamaño de la casilla en píxeles
    etiqueta -> nombre para agrupar las figuras (así se pueden mover o borrar juntas)
Las medidas internas se dan en "unidades" u = tam / 100, para que el ícono crezca o se encoja
con la casilla.
"""

# ------------------------------------ Colores ------------------------------------

FONDO_TABLERO = "#0f141b"
CASILLA = "#151b24"
LINEA_CASILLA = "#222a35"

MURO_SOMBRA = "#2a3039"
MURO_LUZ = "#5d6573"
MURO_CARA = "#4a515e"

AZUL_ROBOT = "#4c8ef7"
AZUL_ROBOT_OSCURO = "#1d4ed8"
CARA_ROBOT = "#dbe8ff"
OJOS_ROBOT = "#1e3a8a"
ANTENA_ROBOT = "#ef4444"

AVION_CUERPO = "#eef2f7"
AVION_BORDE = "#94a3b8"
AVION_ALA = "#3b82f6"
AVION_ALA_LEJANA = "#7aa7f5"

TIERRA_SECA = "#8b5a2b"
TIERRA_SECA_OSCURA = "#5e3b1a"
PLANTA_SECA = "#d9913f"
HALO_SECO = "#3a2914"

TIERRA_HUMEDA = "#5b3a1e"
PLANTA_VERDE = "#4ade80"
PLANTA_VERDE_OSCURA = "#16a34a"
HALO_VERDE = "#14301f"

DEPOSITO = "#22a050"
DEPOSITO_BORDE = "#15803d"
HALO_DEPOSITO = "#12291c"

RASTRO = "#24446e"
HALO_ROBOT = "#2f81f7"
HALO_AVION = "#f0803c"


# ------------------------------------ Ayudas ------------------------------------

def rectangulo_redondeado(lienzo, x1, y1, x2, y2, radio, **opciones):
    """Rectángulo con esquinas redondeadas (polígono suavizado)."""
    r = max(0.5, min(radio, (x2 - x1) / 2, (y2 - y1) / 2))
    puntos = [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r,
              x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
              x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1]
    return lienzo.create_polygon(puntos, smooth=True, **opciones)


def circulo(lienzo, cx, cy, radio, **opciones):
    return lienzo.create_oval(cx - radio, cy - radio, cx + radio, cy + radio, **opciones)


def _centro_y_unidad(x, y, tam):
    return x + tam / 2, y + tam / 2, tam / 100


# ------------------------------------ Casillas fijas ------------------------------------

def dibujar_casilla_libre(lienzo, x, y, tam, etiqueta="estatico"):
    lienzo.create_rectangle(x, y, x + tam, y + tam, fill=CASILLA, outline=LINEA_CASILLA, tags=etiqueta)


def dibujar_muro(lienzo, x, y, tam, etiqueta="estatico"):
    """Bloque gris con un poco de relieve (luz arriba-izquierda, sombra abajo-derecha)."""
    dibujar_casilla_libre(lienzo, x, y, tam, etiqueta)
    m = tam * 0.07
    rectangulo_redondeado(lienzo, x + m + 1, y + m + 1, x + tam - m + 1, y + tam - m + 1, tam * 0.06,
                          fill=MURO_SOMBRA, outline="", tags=etiqueta)
    rectangulo_redondeado(lienzo, x + m, y + m, x + tam - m, y + tam - m, tam * 0.06,
                          fill=MURO_LUZ, outline="", tags=etiqueta)
    b = tam * 0.12
    rectangulo_redondeado(lienzo, x + b, y + b, x + tam - m, y + tam - m, tam * 0.05,
                          fill=MURO_CARA, outline="", tags=etiqueta)


def dibujar_deposito(lienzo, x, y, tam, etiqueta="estatico"):
    """Bidón verde de fertilizante con una etiqueta blanca y un visto bueno."""
    cx, cy, u = _centro_y_unidad(x, y, tam)
    circulo(lienzo, cx, cy, 42 * u, fill=HALO_DEPOSITO, outline="", tags=etiqueta)
    # asa y boquilla
    rectangulo_redondeado(lienzo, cx - 14 * u, cy - 34 * u, cx + 6 * u, cy - 20 * u, 4 * u,
                          fill="", outline=DEPOSITO_BORDE, width=max(1, 4 * u), tags=etiqueta)
    lienzo.create_rectangle(cx + 9 * u, cy - 33 * u, cx + 17 * u, cy - 22 * u,
                            fill=DEPOSITO_BORDE, outline="", tags=etiqueta)
    # cuerpo
    rectangulo_redondeado(lienzo, cx - 22 * u, cy - 24 * u, cx + 22 * u, cy + 32 * u, 7 * u,
                          fill=DEPOSITO, outline=DEPOSITO_BORDE, width=max(1, 2 * u), tags=etiqueta)
    # etiqueta con visto bueno
    rectangulo_redondeado(lienzo, cx - 13 * u, cy - 10 * u, cx + 13 * u, cy + 18 * u, 4 * u,
                          fill="#ffffff", outline="", tags=etiqueta)
    lienzo.create_line(cx - 7 * u, cy + 4 * u, cx - 1 * u, cy + 11 * u, cx + 8 * u, cy - 3 * u,
                       fill=PLANTA_VERDE_OSCURA, width=max(2, 4 * u), capstyle="round",
                       joinstyle="round", tags=etiqueta)


# ------------------------------------ Casillas que cambian ------------------------------------

def dibujar_cultivo_seco(lienzo, x, y, tam, etiqueta="dinamico"):
    """Montoncito de tierra seca con una planta marchita (doblada hacia abajo)."""
    cx, cy, u = _centro_y_unidad(x, y, tam)
    circulo(lienzo, cx, cy, 42 * u, fill=HALO_SECO, outline="", tags=etiqueta)
    lienzo.create_oval(cx - 30 * u, cy + 8 * u, cx + 30 * u, cy + 30 * u,
                       fill=TIERRA_SECA, outline=TIERRA_SECA_OSCURA, width=max(1, 2 * u), tags=etiqueta)
    # grietas de la tierra
    lienzo.create_line(cx - 16 * u, cy + 18 * u, cx - 10 * u, cy + 22 * u, cx - 12 * u, cy + 26 * u,
                       fill=TIERRA_SECA_OSCURA, width=max(1, 2 * u), tags=etiqueta)
    lienzo.create_line(cx + 12 * u, cy + 16 * u, cx + 17 * u, cy + 21 * u,
                       fill=TIERRA_SECA_OSCURA, width=max(1, 2 * u), tags=etiqueta)
    # tallo doblado
    grosor = max(2, 4 * u)
    lienzo.create_line(cx - 2 * u, cy + 14 * u, cx - 3 * u, cy - 6 * u, cx + 4 * u, cy - 20 * u,
                       cx + 16 * u, cy - 14 * u, cx + 20 * u, cy - 2 * u, smooth=True,
                       fill=PLANTA_SECA, width=grosor, capstyle="round", tags=etiqueta)
    # hojas caídas
    lienzo.create_polygon(cx - 3 * u, cy - 2 * u, cx - 18 * u, cy - 4 * u, cx - 24 * u, cy + 6 * u,
                          cx - 12 * u, cy + 4 * u, smooth=True, fill=PLANTA_SECA, outline="", tags=etiqueta)
    lienzo.create_polygon(cx + 2 * u, cy - 14 * u, cx + 12 * u, cy - 24 * u, cx + 24 * u, cy - 22 * u,
                          cx + 12 * u, cy - 12 * u, smooth=True, fill="#c27a2c", outline="", tags=etiqueta)


def dibujar_cultivo_tratado(lienzo, x, y, tam, etiqueta="dinamico"):
    """La misma planta, pero verde y derecha."""
    cx, cy, u = _centro_y_unidad(x, y, tam)
    circulo(lienzo, cx, cy, 42 * u, fill=HALO_VERDE, outline="", tags=etiqueta)
    lienzo.create_oval(cx - 30 * u, cy + 8 * u, cx + 30 * u, cy + 30 * u,
                       fill=TIERRA_HUMEDA, outline="#3e2713", width=max(1, 2 * u), tags=etiqueta)
    lienzo.create_line(cx, cy + 14 * u, cx, cy - 24 * u, fill=PLANTA_VERDE_OSCURA,
                       width=max(2, 4 * u), capstyle="round", tags=etiqueta)
    lienzo.create_polygon(cx, cy - 2 * u, cx - 14 * u, cy - 14 * u, cx - 26 * u, cy - 12 * u,
                          cx - 14 * u, cy + 2 * u, smooth=True, fill=PLANTA_VERDE, outline="", tags=etiqueta)
    lienzo.create_polygon(cx, cy - 12 * u, cx + 14 * u, cy - 26 * u, cx + 26 * u, cy - 24 * u,
                          cx + 14 * u, cy - 8 * u, smooth=True, fill=PLANTA_VERDE, outline="", tags=etiqueta)
    circulo(lienzo, cx, cy - 26 * u, 5 * u, fill=PLANTA_VERDE, outline="", tags=etiqueta)
    # gotita de fertilizante
    lienzo.create_polygon(cx + 20 * u, cy + 2 * u, cx + 25 * u, cy + 10 * u, cx + 20 * u, cy + 14 * u,
                          cx + 15 * u, cy + 10 * u, smooth=True, fill="#7dd3fc", outline="", tags=etiqueta)


def dibujar_avioneta(lienzo, x, y, tam, etiqueta="dinamico", con_halo=True):
    """Avioneta blanca de lado, mirando a la derecha."""
    cx, cy, u = _centro_y_unidad(x, y, tam)
    if con_halo:
        circulo(lienzo, cx, cy, 42 * u, fill="#1a2433", outline="", tags=etiqueta)
    _cuerpo_de_avioneta(lienzo, cx, cy, u, etiqueta)


def _cuerpo_de_avioneta(lienzo, cx, cy, u, etiqueta, piloto=None):
    # ala del otro lado (más clara, queda detrás)
    lienzo.create_polygon(cx - 2 * u, cy - 3 * u, cx + 8 * u, cy - 3 * u, cx - 8 * u, cy - 22 * u,
                          cx - 17 * u, cy - 22 * u, fill=AVION_ALA_LEJANA, outline="", tags=etiqueta)
    # cola
    lienzo.create_polygon(cx - 30 * u, cy - 3 * u, cx - 20 * u, cy - 3 * u, cx - 33 * u, cy - 22 * u,
                          cx - 40 * u, cy - 22 * u, fill=AVION_ALA, outline="", tags=etiqueta)
    if piloto is not None:
        piloto()                                   # el robot se dibuja aquí, para que el fuselaje lo tape
    # fuselaje
    lienzo.create_polygon(cx - 38 * u, cy - 4 * u, cx - 10 * u, cy - 9 * u, cx + 22 * u, cy - 9 * u,
                          cx + 32 * u, cy - 4 * u, cx + 33 * u, cy + 1 * u, cx + 24 * u, cy + 8 * u,
                          cx - 10 * u, cy + 8 * u, cx - 38 * u, cy + 2 * u, smooth=True,
                          fill=AVION_CUERPO, outline=AVION_BORDE, width=max(1, 1.5 * u), tags=etiqueta)
    # franja azul y ventanas
    lienzo.create_line(cx - 34 * u, cy + 2 * u, cx + 26 * u, cy + 2 * u, fill=AVION_ALA,
                       width=max(1, 2 * u), tags=etiqueta)
    for desplazamiento in (-14, -5, 4):
        circulo(lienzo, cx + desplazamiento * u, cy - 3 * u, 2.6 * u, fill=OJOS_ROBOT, outline="", tags=etiqueta)
    lienzo.create_polygon(cx + 13 * u, cy - 8 * u, cx + 22 * u, cy - 8 * u, cx + 27 * u, cy - 3 * u,
                          cx + 13 * u, cy - 3 * u, fill="#60a5fa", outline="", tags=etiqueta)
    # ala de este lado (queda delante)
    lienzo.create_polygon(cx - 4 * u, cy + 3 * u, cx + 8 * u, cy + 3 * u, cx - 6 * u, cy + 24 * u,
                          cx - 16 * u, cy + 24 * u, fill=AVION_ALA, outline=AZUL_ROBOT_OSCURO,
                          width=1, tags=etiqueta)
    # hélice
    lienzo.create_oval(cx + 33 * u, cy - 15 * u, cx + 37 * u, cy + 15 * u, fill="#cbd5e1", outline="", tags=etiqueta)
    circulo(lienzo, cx + 34 * u, cy, 3 * u, fill="#64748b", outline="", tags=etiqueta)


def dibujar_rastro(lienzo, x, y, tam, etiqueta="rastro"):
    """Puntico que marca por dónde ya pasó el robot."""
    cx, cy, u = _centro_y_unidad(x, y, tam)
    circulo(lienzo, cx, cy, max(2, 7 * u), fill=RASTRO, outline="", tags=etiqueta)


# ------------------------------------ Robot ------------------------------------

def dibujar_figura_robot(lienzo, cx, cy, u, etiqueta):
    """El robot centrado en (cx, cy). Mide unas 80 unidades de alto."""
    ancho_linea = max(1, 2 * u)
    # antena
    lienzo.create_line(cx, cy - 26 * u, cx, cy - 36 * u, fill="#94a3b8", width=ancho_linea, tags=etiqueta)
    circulo(lienzo, cx, cy - 38 * u, 4.5 * u, fill=ANTENA_ROBOT, outline="", tags=etiqueta)
    # orejas
    rectangulo_redondeado(lienzo, cx - 33 * u, cy - 17 * u, cx - 26 * u, cy - 5 * u, 2 * u,
                          fill=AZUL_ROBOT_OSCURO, outline="", tags=etiqueta)
    rectangulo_redondeado(lienzo, cx + 26 * u, cy - 17 * u, cx + 33 * u, cy - 5 * u, 2 * u,
                          fill=AZUL_ROBOT_OSCURO, outline="", tags=etiqueta)
    # cabeza y cara
    rectangulo_redondeado(lienzo, cx - 28 * u, cy - 27 * u, cx + 28 * u, cy + 4 * u, 8 * u,
                          fill=AZUL_ROBOT, outline=AZUL_ROBOT_OSCURO, width=ancho_linea, tags=etiqueta)
    rectangulo_redondeado(lienzo, cx - 21 * u, cy - 21 * u, cx + 21 * u, cy - 2 * u, 5 * u,
                          fill=CARA_ROBOT, outline="", tags=etiqueta)
    for lado in (-1, 1):
        rectangulo_redondeado(lienzo, cx + lado * 10 * u - 4.5 * u, cy - 16 * u,
                              cx + lado * 10 * u + 4.5 * u, cy - 7 * u, 2 * u,
                              fill=OJOS_ROBOT, outline="", tags=etiqueta)
    # brazos
    for lado in (-1, 1):
        x_brazo = cx + lado * 26 * u
        rectangulo_redondeado(lienzo, x_brazo - 4 * u, cy + 9 * u, x_brazo + 4 * u, cy + 25 * u, 3 * u,
                              fill=AZUL_ROBOT_OSCURO, outline="", tags=etiqueta)
    # cuerpo
    rectangulo_redondeado(lienzo, cx - 20 * u, cy + 7 * u, cx + 20 * u, cy + 30 * u, 6 * u,
                          fill=AZUL_ROBOT, outline=AZUL_ROBOT_OSCURO, width=ancho_linea, tags=etiqueta)
    rectangulo_redondeado(lienzo, cx - 10 * u, cy + 12 * u, cx + 10 * u, cy + 22 * u, 3 * u,
                          fill=CARA_ROBOT, outline="", tags=etiqueta)
    circulo(lienzo, cx - 4 * u, cy + 17 * u, 2 * u, fill="#22c55e", outline="", tags=etiqueta)
    circulo(lienzo, cx + 4 * u, cy + 17 * u, 2 * u, fill="#f59e0b", outline="", tags=etiqueta)
    # pies
    for lado in (-1, 1):
        lienzo.create_rectangle(cx + lado * 10 * u - 5 * u, cy + 30 * u, cx + lado * 10 * u + 5 * u,
                                cy + 36 * u, fill=AZUL_ROBOT_OSCURO, outline="", tags=etiqueta)


def dibujar_robot(lienzo, x, y, tam, fertilizante=None, en_avioneta=False, etiqueta="robot",
                  fuente_insignia="Arial"):
    """
    El AgroBot en su casilla. Si va en avioneta, se dibuja sentado dentro de ella.
    fertilizante=None no dibuja la insignia (se usa en el logo del encabezado).
    """
    cx, cy, u = _centro_y_unidad(x, y, tam)

    if en_avioneta:
        circulo(lienzo, cx, cy, 44 * u, fill="", outline=HALO_AVION, width=max(1, 2 * u),
                dash=(3, 3), tags=etiqueta)
        escala = 0.42

        def piloto():
            dibujar_figura_robot(lienzo, cx + 4 * u, cy - 14 * u, u * escala, etiqueta)

        _cuerpo_de_avioneta(lienzo, cx, cy + 4 * u, u, etiqueta, piloto=piloto)
    else:
        circulo(lienzo, cx, cy, 44 * u, fill="", outline=HALO_ROBOT, width=max(1, 2 * u),
                dash=(3, 3), tags=etiqueta)
        dibujar_figura_robot(lienzo, cx, cy + 2 * u, u * 0.92, etiqueta)

    if fertilizante is not None:
        # insignia con las unidades de fertilizante (arriba a la derecha)
        bx, by, radio = cx + 30 * u, cy - 30 * u, 12 * u
        color = "#22c55e" if fertilizante > 0 else "#475569"
        circulo(lienzo, bx, by, radio, fill=color, outline=FONDO_TABLERO, width=max(1, 2 * u), tags=etiqueta)
        lienzo.create_text(bx, by, text=str(fertilizante), fill="#ffffff",
                           font=(fuente_insignia, max(7, int(tam * 0.15)), "bold"), tags=etiqueta)
