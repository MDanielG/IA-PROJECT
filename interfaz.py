"""
AgroBot - Proyecto 1 de Inteligencia Artificial (Univalle)
Hecho por: Andres Muñoz, Thomas Herrera, Brandon Franco y Daniel Micolta

INTERFAZ GRÁFICA (este es el archivo que se ejecuta):
    - Usa logica.py para leer el mundo y correr las búsquedas.
    - Usa dibujos.py para dibujar los íconos del tablero.

La búsqueda corre en un proceso aparte: así la ventana no se congela mientras busca
y se puede cancelar con el botón «Cancelar búsqueda».
"""
import multiprocessing
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import font as tkfont

import dibujos
import logica

AUTORES = "Andres Muñoz, Thomas Herrera, Brandon Franco y Daniel Micolta"

# ------------------------------------ Colores de la ventana ------------------------------------

FONDO = "#0d1117"
PANEL = "#161b22"
PANEL_HUNDIDO = "#0f141b"
BORDE = "#30363d"
TEXTO = "#e6edf3"
TEXTO_SUAVE = "#8b949e"
TEXTO_APAGADO = "#545d68"
ACENTO = "#3b82f6"
ACENTO_CLARO = "#79b0ff"
VERDE = "#22c55e"
NARANJA = "#f0803c"
ROJO = "#f85149"
AMARILLO = "#e3b341"

FLECHAS = {"arriba": "↑", "abajo": "↓", "izquierda": "←", "derecha": "→"}


def formatear_costo(costo):
    """Muestra 25 en vez de 25.0 (los costos siempre son enteros o terminan en .5)."""
    return str(int(costo)) if costo == int(costo) else str(costo)


# =====================================================================================
# Barra de progreso redondeada (las de ttk no se dejan pintar bien en tema oscuro)
# =====================================================================================

class BarraProgreso(tk.Canvas):
    def __init__(self, padre, alto=8, color=ACENTO):
        super().__init__(padre, height=alto, bg=PANEL, highlightthickness=0, bd=0)
        self.fraccion = 0.0
        self.color = color
        self.bind("<Configure>", lambda _evento: self._redibujar())

    def poner(self, fraccion, color=None):
        self.fraccion = max(0.0, min(1.0, fraccion))
        if color is not None:
            self.color = color
        self._redibujar()

    def _redibujar(self):
        self.delete("all")
        ancho, alto = self.winfo_width(), int(self["height"])
        if ancho <= 1:
            return
        dibujos.rectangulo_redondeado(self, 0, 0, ancho, alto, alto / 2, fill=PANEL_HUNDIDO, outline="")
        if self.fraccion > 0:
            relleno = max(alto, ancho * self.fraccion)
            dibujos.rectangulo_redondeado(self, 0, 0, relleno, alto, alto / 2, fill=self.color, outline="")


# =====================================================================================
# Ventana principal
# =====================================================================================

class AplicacionAgroBot:

    def __init__(self, ventana):
        self.ventana = ventana
        self.problema = None                 # se llena al cargar un mundo
        self.nombre_mundo = "Ningún mundo cargado"
        self.tam_casilla = 56

        # Búsqueda en curso
        self.proceso = None                  # proceso (o hilo) que está buscando
        self.cola = None                     # por aquí llega el resultado
        self.hora_inicio_busqueda = 0.0
        self.revision_pendiente = None

        # Animación
        self.resultado = None
        self.nombre_resultado = ""
        self.paso_actual = 0
        self.animacion_pendiente = None
        self.en_pausa = False
        self.animacion_terminada = False

        ventana.title("AgroBot - Proyecto 1 de Inteligencia Artificial")
        ventana.configure(bg=FONDO)
        ventana.protocol("WM_DELETE_WINDOW", self.cerrar)

        self._crear_fuentes()
        self._crear_estilos()
        self._crear_encabezado()
        self._crear_cuerpo()

        ventana.bind("<Return>", lambda _evento: self.buscar())     # Enter = Buscar

        self._cargar_mundo_de_ejemplo_si_existe()
        self._centrar_ventana()

    # ================================ Apariencia ================================

    def _crear_fuentes(self):
        disponibles = set(tkfont.families(self.ventana))
        familia = next((f for f in ("Segoe UI", "Helvetica Neue", "Ubuntu", "DejaVu Sans", "Arial")
                        if f in disponibles), "TkDefaultFont")
        self.familia = familia
        self.f_titulo = tkfont.Font(family=familia, size=30, weight="bold")
        self.f_subtitulo = tkfont.Font(family=familia, size=11)
        self.f_seccion = tkfont.Font(family=familia, size=11, weight="bold")
        self.f_normal = tkfont.Font(family=familia, size=10)
        self.f_negrita = tkfont.Font(family=familia, size=10, weight="bold")
        self.f_pequena = tkfont.Font(family=familia, size=8)
        self.f_dato = tkfont.Font(family=familia, size=15, weight="bold")
        self.f_boton = tkfont.Font(family=familia, size=11, weight="bold")

    def _crear_estilos(self):
        estilo = ttk.Style(self.ventana)
        estilo.theme_use("clam")      # 'clam' es el único tema que deja cambiar todos los colores
        estilo.configure(".", background=PANEL, foreground=TEXTO, font=self.f_normal,
                         bordercolor=BORDE, focuscolor=PANEL, lightcolor=PANEL, darkcolor=PANEL)

        # Botón normal (gris oscuro)
        estilo.configure("TButton", background="#21262d", foreground=TEXTO, bordercolor=BORDE,
                         lightcolor="#21262d", darkcolor="#21262d", padding=(10, 5), relief="flat",
                         focusthickness=0)
        estilo.map("TButton",
                   background=[("disabled", PANEL), ("pressed", "#3a414b"), ("active", "#30363d")],
                   lightcolor=[("disabled", PANEL), ("pressed", "#3a414b"), ("active", "#30363d")],
                   darkcolor=[("disabled", PANEL), ("pressed", "#3a414b"), ("active", "#30363d")],
                   foreground=[("disabled", TEXTO_APAGADO)],
                   bordercolor=[("disabled", "#21262d")])

        # Botón principal (azul)
        estilo.configure("Acento.TButton", background="#2563eb", foreground="#ffffff",
                         bordercolor="#3b82f6", lightcolor="#2563eb", darkcolor="#2563eb",
                         font=self.f_boton, padding=(10, 7))
        estilo.map("Acento.TButton",
                   background=[("disabled", "#1a2740"), ("pressed", "#1d4ed8"), ("active", "#3b82f6")],
                   lightcolor=[("disabled", "#1a2740"), ("pressed", "#1d4ed8"), ("active", "#3b82f6")],
                   darkcolor=[("disabled", "#1a2740"), ("pressed", "#1d4ed8"), ("active", "#3b82f6")],
                   foreground=[("disabled", "#5a6b88")],
                   bordercolor=[("disabled", "#22324f")])

        # Pestaña elegida del selector "No informada / Informada"
        estilo.configure("Elegido.TButton", background="#1f3a66", foreground="#ffffff",
                         bordercolor=ACENTO, lightcolor="#1f3a66", darkcolor="#1f3a66",
                         font=self.f_negrita, padding=(8, 4))
        estilo.map("Elegido.TButton", background=[("active", "#25467a")],
                   lightcolor=[("active", "#25467a")], darkcolor=[("active", "#25467a")])
        estilo.configure("Pestana.TButton", padding=(8, 4))

        # Botones de radio
        estilo.configure("TRadiobutton", background=PANEL, foreground=TEXTO, padding=(2, 3),
                         indicatorbackground=PANEL_HUNDIDO, indicatorforeground=ACENTO,
                         upperbordercolor="#57606a", lowerbordercolor="#57606a", indicatormargin=(0, 0, 8, 0),
                         focusthickness=0)
        estilo.map("TRadiobutton",
                   background=[("active", PANEL)],
                   foreground=[("active", "#ffffff"), ("disabled", TEXTO_APAGADO)],
                   indicatorbackground=[("pressed", "#1f3a66"), ("selected", PANEL_HUNDIDO)],
                   upperbordercolor=[("selected", ACENTO)], lowerbordercolor=[("selected", ACENTO)])

        # Barra deslizante de la velocidad
        estilo.configure("Horizontal.TScale", background="#3a414b", troughcolor=PANEL_HUNDIDO,
                         bordercolor=BORDE, lightcolor="#4b535e", darkcolor="#3a414b")
        estilo.map("Horizontal.TScale", background=[("active", ACENTO)])

    # ================================ Construcción ================================

    def _crear_encabezado(self):
        encabezado = tk.Frame(self.ventana, bg=FONDO)
        encabezado.pack(fill="x", pady=(12, 8))
        centro = tk.Frame(encabezado, bg=FONDO)
        centro.pack()

        logo = tk.Canvas(centro, width=70, height=70, bg=FONDO, highlightthickness=0)
        logo.pack(side="left", padx=(0, 26))
        dibujos.dibujar_figura_robot(logo, 35, 37, 0.85, "logo")

        textos = tk.Frame(centro, bg=FONDO)
        textos.pack(side="left")
        tk.Label(textos, text="AgroBot", font=self.f_titulo, fg=ACENTO, bg=FONDO).pack()
        tk.Label(textos, text=f"Hecho por: {AUTORES}", font=self.f_subtitulo,
                 fg=TEXTO_SUAVE, bg=FONDO).pack()

        avion = tk.Canvas(centro, width=80, height=70, bg=FONDO, highlightthickness=0)
        avion.pack(side="left", padx=(26, 0))
        dibujos.dibujar_avioneta(avion, 0, -5, 80, "logo", con_halo=False)

        tk.Frame(self.ventana, bg=BORDE, height=1).pack(fill="x", padx=14)

    def _crear_cuerpo(self):
        cuerpo = tk.Frame(self.ventana, bg=FONDO)
        cuerpo.pack(fill="both", expand=True, padx=14, pady=(10, 14))

        izquierda = tk.Frame(cuerpo, bg=FONDO)
        izquierda.pack(side="left", fill="both", expand=True)
        derecha = tk.Frame(cuerpo, bg=FONDO)
        derecha.pack(side="left", fill="y", padx=(16, 0))
        # ancho mínimo fijo, para que el panel no cambie de tamaño cuando cambian los textos
        tk.Frame(derecha, bg=FONDO, height=1, width=int(310 * self._escala())).pack()

        self._crear_tablero(izquierda)
        self._crear_reporte(izquierda)

        self._crear_seccion_mundo(derecha)
        self._crear_seccion_busqueda(derecha)
        self._crear_seccion_animacion(derecha)
        self._crear_seccion_estado(derecha)

    def _seccion(self, padre, titulo, primera=False):
        """Título azul + tarjeta con borde, como en el diseño."""
        etiqueta = tk.Label(padre, text=titulo, font=self.f_seccion, fg=ACENTO, bg=FONDO, anchor="w")
        etiqueta.pack(fill="x", pady=(0 if primera else 10, 3))
        tarjeta = tk.Frame(padre, bg=PANEL, highlightthickness=1, highlightbackground=BORDE,
                           padx=10, pady=8)
        tarjeta.pack(fill="x")
        return etiqueta, tarjeta

    # ---- Tablero ----

    def _crear_tablero(self, padre):
        marco = tk.Frame(padre, bg=ACENTO, padx=2, pady=2)        # el borde azul del tablero
        marco.pack(pady=(4, 0))
        self.lienzo = tk.Canvas(marco, width=560, height=560, bg=dibujos.FONDO_TABLERO,
                                highlightthickness=0, bd=0)
        self.lienzo.pack()

        self.texto_barra = tk.StringVar(value="Cargue un archivo de mundo para comenzar.")
        self.barra_estado = tk.Label(padre, textvariable=self.texto_barra, font=self.f_negrita,
                                     fg=ACENTO_CLARO, bg=PANEL, padx=16, pady=6,
                                     highlightthickness=1, highlightbackground=BORDE)
        self.barra_estado.pack(pady=(12, 0))

    def _crear_reporte(self, padre):
        contenedor = tk.Frame(padre, bg=FONDO)
        contenedor.pack(fill="x", pady=(10, 0))
        _, tarjeta = self._seccion(contenedor, "Reporte", primera=True)

        fila_datos = tk.Frame(tarjeta, bg=PANEL)
        fila_datos.pack(fill="x")
        self.datos_reporte = {}
        titulos = [("nodos", "Nodos expandidos"), ("profundidad", "Profundidad del árbol"),
                   ("tiempo", "Tiempo de cómputo"), ("pasos", "Pasos de la solución"),
                   ("costo", "Costo de la solución")]
        for columna, (clave, titulo) in enumerate(titulos):
            fila_datos.columnconfigure(columna, weight=1, uniform="datos")
            caja = tk.Frame(fila_datos, bg=PANEL_HUNDIDO, highlightthickness=1,
                            highlightbackground="#1f2630", padx=6, pady=5)
            caja.grid(row=0, column=columna, sticky="nsew", padx=3)
            valor = tk.Label(caja, text="—", font=self.f_dato, fg=TEXTO, bg=PANEL_HUNDIDO)
            valor.pack()
            tk.Label(caja, text=titulo, font=self.f_pequena, fg=TEXTO_SUAVE, bg=PANEL_HUNDIDO).pack()
            self.datos_reporte[clave] = valor

        self.mensaje_reporte = tk.Label(tarjeta, text="Aún no se ha ejecutado ningún algoritmo.",
                                        font=self.f_negrita, fg=TEXTO_SUAVE, bg=PANEL,
                                        anchor="w", justify="left")
        self.mensaje_reporte.pack(fill="x", pady=(8, 0))
        self.camino_reporte = tk.Label(tarjeta, text="", font=self.f_normal, fg=TEXTO_SUAVE,
                                       bg=PANEL, anchor="w", justify="left")
        self.camino_reporte.pack(fill="x")

    # ---- Panel derecho ----

    def _crear_seccion_mundo(self, padre):
        _, tarjeta = self._seccion(padre, "Mundo", primera=True)
        self.boton_cargar = ttk.Button(tarjeta, text="Cargar mundo...", command=self.pedir_archivo_y_cargar)
        self.boton_cargar.pack(fill="x")
        self.etiqueta_archivo = tk.Label(tarjeta, text="Ningún mundo cargado", font=self.f_normal,
                                         fg=TEXTO_SUAVE, bg=PANEL, anchor="w")
        self.etiqueta_archivo.pack(fill="x", pady=(6, 0))

    def _crear_seccion_busqueda(self, padre):
        self.titulo_busqueda, tarjeta = self._seccion(padre, "Búsqueda no informada")

        # Selector del tipo de búsqueda (primero se elige el tipo y luego el algoritmo)
        selector = tk.Frame(tarjeta, bg=PANEL)
        selector.pack(fill="x", pady=(0, 6))
        self.botones_tipo = {}
        for columna, tipo in enumerate(logica.ALGORITMOS_POR_TIPO):
            selector.columnconfigure(columna, weight=1, uniform="tipo")
            boton = ttk.Button(selector, text=tipo, command=lambda t=tipo: self.cambiar_tipo(t))
            boton.grid(row=0, column=columna, sticky="ew", padx=(0 if columna == 0 else 3, 0))
            self.botones_tipo[tipo] = boton

        self.algoritmo_elegido = tk.StringVar()
        self.marco_algoritmos = tk.Frame(tarjeta, bg=PANEL)
        self.marco_algoritmos.pack(fill="x")

        self.boton_buscar = ttk.Button(tarjeta, text="Buscar", style="Acento.TButton", command=self.buscar)
        self.boton_buscar.pack(fill="x", pady=(8, 4))
        self.boton_cancelar = ttk.Button(tarjeta, text="Cancelar búsqueda", command=self.cancelar_busqueda,
                                         state="disabled")
        self.boton_cancelar.pack(fill="x")

        self.cambiar_tipo("No informada")

    def _crear_seccion_animacion(self, padre):
        _, tarjeta = self._seccion(padre, "Animación")
        botones = tk.Frame(tarjeta, bg=PANEL)
        botones.pack(fill="x")
        botones.columnconfigure(0, weight=1, uniform="anim")
        botones.columnconfigure(1, weight=1, uniform="anim")
        self.boton_pausa = ttk.Button(botones, text="Pausar", command=self.pausar_o_continuar, state="disabled")
        self.boton_pausa.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self.boton_reiniciar = ttk.Button(botones, text="Reiniciar", command=self.reiniciar_animacion,
                                          state="disabled")
        self.boton_reiniciar.grid(row=0, column=1, sticky="ew", padx=(3, 0))

        tk.Label(tarjeta, text="Rápido   ←   velocidad   →   Lento", font=self.f_pequena,
                 fg=TEXTO_SUAVE, bg=PANEL).pack(pady=(8, 2))
        self.pausa_ms = tk.DoubleVar(value=250)                 # milisegundos por paso
        ttk.Scale(tarjeta, from_=30, to=800, variable=self.pausa_ms).pack(fill="x")

    def _crear_seccion_estado(self, padre):
        _, tarjeta = self._seccion(padre, "Estado del robot")

        def fila(titulo):
            marco = tk.Frame(tarjeta, bg=PANEL)
            marco.pack(fill="x", pady=(3, 0))
            tk.Label(marco, text=titulo, font=self.f_normal, fg=TEXTO_SUAVE, bg=PANEL).pack(side="left")
            valor = tk.Label(marco, text="", font=self.f_negrita, fg=TEXTO, bg=PANEL)
            valor.pack(side="left", padx=(4, 0))
            return valor

        def barra(color):
            b = BarraProgreso(tarjeta, color=color)
            b.pack(fill="x", pady=(4, 4))
            return b

        self.valor_paso = fila("Paso:")
        self.barra_paso = barra(ACENTO)
        self.valor_movimiento = fila("Movimiento:")
        self.valor_fertilizante = fila("Fertilizante:")
        self.valor_avioneta = fila("Avioneta:")
        self.barra_avioneta = barra(NARANJA)
        self.valor_cultivos = fila("Cultivos tratados:")
        self.barra_cultivos = barra(VERDE)
        self.valor_costo = fila("Costo acumulado:")

    def _centrar_ventana(self):
        self.ventana.update_idletasks()
        ancho, alto = self.ventana.winfo_reqwidth(), self.ventana.winfo_reqheight()
        x = max(0, (self.ventana.winfo_screenwidth() - ancho) // 2)
        y = max(0, (self.ventana.winfo_screenheight() - alto) // 2 - 20)
        self.ventana.geometry(f"+{x}+{y}")

    # ================================ Mundo ================================

    def _cargar_mundo_de_ejemplo_si_existe(self):
        carpeta_del_script = os.path.dirname(os.path.abspath(__file__))
        ruta = os.path.join(carpeta_del_script, "Prueba1.txt")
        if os.path.exists(ruta):
            self.cargar_mundo(ruta)
        else:
            self._actualizar_botones()

    def pedir_archivo_y_cargar(self):
        ruta = filedialog.askopenfilename(title="Seleccione el archivo del mundo",
                                          filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if ruta:
            self.cargar_mundo(ruta)

    def cargar_mundo(self, ruta):
        """Lee el archivo, crea el problema y dibuja el estado inicial."""
        try:
            problema = logica.Problema(logica.leer_mundo(ruta))
        except Exception as error:
            messagebox.showerror("Error al leer el mundo", str(error))
            return
        self.cancelar_busqueda(silencioso=True)
        self._detener_animacion()
        self.problema = problema
        self.nombre_mundo = os.path.basename(ruta)
        self.etiqueta_archivo.config(text=self.nombre_mundo, fg=TEXTO)
        self.resultado = None
        self._limpiar_reporte()

        self.tam_casilla = self._calcular_tamano_de_casilla()
        ancho_tablero = problema.total_columnas * self.tam_casilla
        self.lienzo.config(width=ancho_tablero, height=problema.total_filas * self.tam_casilla)
        # los textos largos se parten en varias líneas en vez de ensanchar la ventana
        ancho_texto = max(ancho_tablero, int(470 * self._escala())) - 30
        for etiqueta in (self.barra_estado, self.mensaje_reporte, self.camino_reporte):
            etiqueta.config(wraplength=ancho_texto)
        self._dibujar_capa_fija()
        self.paso_actual = 0
        self.mostrar_paso(0)

        total = len(problema.cultivos_secos_iniciales)
        self.texto_barra.set(f"Mundo cargado: {problema.total_filas}x{problema.total_columnas} · "
                             f"{total} cultivo{'s' if total != 1 else ''} seco{'s' if total != 1 else ''} · "
                             f"elige un algoritmo y pulsa Buscar")
        self.barra_estado.config(fg=ACENTO_CLARO)
        self._actualizar_botones()

    def _calcular_tamano_de_casilla(self):
        """Casillas grandes en mapas pequeños y más chicas en mapas grandes, sin salirse de la pantalla."""
        escala = self._escala()
        alto_libre = self.ventana.winfo_screenheight() - int(380 * escala)
        ancho_libre = self.ventana.winfo_screenwidth() - int(420 * escala)
        tam = min(alto_libre // self.problema.total_filas,
                  ancho_libre // self.problema.total_columnas,
                  int(60 * escala))
        return max(18, tam)

    def _escala(self):
        """1.0 en pantallas normales; 1.25, 1.5... si Windows tiene la pantalla ampliada."""
        return self.ventana.winfo_fpixels("1i") / 96

    # ================================ Dibujo del tablero ================================

    def _dibujar_capa_fija(self):
        """Lo que nunca cambia: casillas, muros y depósito."""
        problema, tam = self.problema, self.tam_casilla
        self.lienzo.delete("all")
        for fila in range(problema.total_filas):
            for columna in range(problema.total_columnas):
                x, y = columna * tam, fila * tam
                if problema.mapa[fila][columna] == logica.CASILLA_OBSTACULO:
                    dibujos.dibujar_muro(self.lienzo, x, y, tam)
                else:
                    dibujos.dibujar_casilla_libre(self.lienzo, x, y, tam)
        if problema.posicion_deposito is not None:
            fila, columna = problema.posicion_deposito
            dibujos.dibujar_deposito(self.lienzo, columna * tam, fila * tam, tam)

    def _estados(self):
        if self.resultado is not None and self.resultado["exito"]:
            return self.resultado["estados"]
        return [self.problema.estado_inicial]

    def _dibujar_capa_que_cambia(self, numero_de_paso):
        """Rastro, cultivos (secos o tratados), avioneta (si nadie la ha tomado) y robot."""
        problema, tam, lienzo = self.problema, self.tam_casilla, self.lienzo
        estados = self._estados()
        estado = estados[numero_de_paso]
        for etiqueta in ("rastro", "dinamico", "robot"):
            lienzo.delete(etiqueta)

        # rastro de las casillas por las que ya pasó
        ya_marcadas = {(estado.fila, estado.columna), problema.posicion_deposito}
        for anterior in estados[:numero_de_paso]:
            posicion = (anterior.fila, anterior.columna)
            if posicion not in ya_marcadas:
                ya_marcadas.add(posicion)
                dibujos.dibujar_rastro(lienzo, anterior.columna * tam, anterior.fila * tam, tam)

        for fila, columna in problema.cultivos_secos_iniciales:
            if (fila, columna) in estado.cultivos_secos:
                dibujos.dibujar_cultivo_seco(lienzo, columna * tam, fila * tam, tam)
            else:
                dibujos.dibujar_cultivo_tratado(lienzo, columna * tam, fila * tam, tam)

        if problema.posicion_avioneta is not None and estado.combustible_avioneta is None:
            fila, columna = problema.posicion_avioneta
            dibujos.dibujar_avioneta(lienzo, columna * tam, fila * tam, tam)

        en_avioneta = estado.combustible_avioneta is not None and estado.combustible_avioneta > 0
        dibujos.dibujar_robot(lienzo, estado.columna * tam, estado.fila * tam, tam,
                              fertilizante=estado.fertilizante, en_avioneta=en_avioneta,
                              fuente_insignia=self.familia)

    def mostrar_paso(self, numero_de_paso):
        """Dibuja el tablero y llena el panel 'Estado del robot' para un paso de la solución."""
        self._dibujar_capa_que_cambia(numero_de_paso)
        estados = self._estados()
        estado = estados[numero_de_paso]
        ultimo = len(estados) - 1

        self.valor_paso.config(text=f"{numero_de_paso} / {ultimo}")
        self.barra_paso.poner(numero_de_paso / ultimo if ultimo else 0)

        if numero_de_paso > 0:
            movimiento = self.resultado["movimientos"][numero_de_paso - 1]
            self.valor_movimiento.config(text=f"{FLECHAS.get(movimiento, '')}  {movimiento}")
        else:
            self.valor_movimiento.config(text="-")

        unidades = estado.fertilizante
        self.valor_fertilizante.config(
            text="●" * unidades + "○" * (logica.FERTILIZANTE_MAXIMO - unidades)
                 + f"  ({unidades}/{logica.FERTILIZANTE_MAXIMO})",
            fg=VERDE if unidades > 0 else TEXTO)

        combustible = estado.combustible_avioneta
        maximo = logica.COMBUSTIBLE_INICIAL_AVIONETA
        if combustible is None:
            self.valor_avioneta.config(text="aún no la toma", fg=TEXTO)
            self.barra_avioneta.poner(0)
        elif combustible > 0:
            self.valor_avioneta.config(text=f"en vuelo · combustible {combustible}/{maximo}", fg=NARANJA)
            self.barra_avioneta.poner(combustible / maximo)
        else:
            self.valor_avioneta.config(text="sin combustible", fg=ROJO)
            self.barra_avioneta.poner(0)

        total = len(self.problema.cultivos_secos_iniciales)
        tratados = total - len(estado.cultivos_secos)
        self.valor_cultivos.config(text=f"{tratados} / {total}")
        self.barra_cultivos.poner(tratados / total if total else 1)

        if self.resultado is not None and self.resultado["exito"]:
            costo = self.resultado["costos_acumulados"][numero_de_paso]
        else:
            costo = 0
        self.valor_costo.config(text=formatear_costo(costo))

    # ================================ Selección de algoritmo ================================

    def cambiar_tipo(self, tipo):
        """Cuando cambia el tipo (informada / no informada) se muestran solo sus algoritmos."""
        self.tipo_elegido = tipo
        self.titulo_busqueda.config(text=f"Búsqueda {tipo.lower()}")
        for nombre, boton in self.botones_tipo.items():
            boton.config(style="Elegido.TButton" if nombre == tipo else "Pestana.TButton")

        for hijo in self.marco_algoritmos.winfo_children():
            hijo.destroy()
        algoritmos = logica.ALGORITMOS_POR_TIPO[tipo]
        self.algoritmo_elegido.set(algoritmos[0])
        for nombre in algoritmos:
            ttk.Radiobutton(self.marco_algoritmos, text=nombre, value=nombre,
                            variable=self.algoritmo_elegido).pack(anchor="w")

    # ================================ Búsqueda ================================

    def buscar(self):
        if self.problema is None:
            messagebox.showwarning("Aviso", "Primero cargue un mundo.")
            return
        if self._buscando():
            return

        self._detener_animacion()
        self.resultado = None
        self.paso_actual = 0
        self.en_pausa = False
        self.animacion_terminada = False
        self.mostrar_paso(0)
        self._limpiar_reporte()

        nombre = self.algoritmo_elegido.get()
        self.nombre_resultado = nombre
        self.hora_inicio_busqueda = time.perf_counter()
        self._iniciar_proceso(nombre)
        self.barra_estado.config(fg=AMARILLO)
        self.mensaje_reporte.config(text=f"Buscando con «{nombre}»...", fg=AMARILLO)
        self._actualizar_botones()
        self._revisar_busqueda()

    def _iniciar_proceso(self, nombre):
        """
        Lanza la búsqueda en un proceso aparte. Si por alguna razón no se puede (algunos entornos
        no lo permiten), la corre en un hilo: la ventana sigue respondiendo, pero no se puede cortar.
        """
        try:
            contexto = multiprocessing.get_context("spawn")
            self.cola = contexto.Queue()
            self.proceso = contexto.Process(target=logica.ejecutar_busqueda_en_proceso,
                                            args=(nombre, self.problema, self.cola), daemon=True)
            self.proceso.start()
        except Exception:
            self.cola = queue.Queue()
            self.proceso = threading.Thread(target=logica.ejecutar_busqueda_en_proceso,
                                            args=(nombre, self.problema, self.cola), daemon=True)
            self.proceso.start()

    def _buscando(self):
        return self.proceso is not None

    def _revisar_busqueda(self):
        """Cada 100 ms mira si ya llegó el resultado (sin congelar la ventana)."""
        self.revision_pendiente = None
        if self.proceso is None:
            return
        try:
            tipo, datos = self.cola.get_nowait()
        except queue.Empty:
            if self.proceso.is_alive():
                segundos = time.perf_counter() - self.hora_inicio_busqueda
                self.texto_barra.set(f"Buscando con «{self.nombre_resultado}»...  {segundos:.1f} s")
                self.revision_pendiente = self.ventana.after(100, self._revisar_busqueda)
                return
            try:                                       # terminó justo ahora: el dato puede venir en camino
                tipo, datos = self.cola.get(timeout=1)
            except queue.Empty:
                tipo, datos = "error", "La búsqueda terminó de forma inesperada."

        self._soltar_proceso()
        if tipo == "ok":
            self._mostrar_resultado(datos)
        elif tipo == "memoria":
            self._mostrar_falla("Sin memoria: este mundo tiene demasiados estados para esta búsqueda.")
        else:
            self._mostrar_falla(f"Error durante la búsqueda: {datos}")

    def cancelar_busqueda(self, silencioso=False):
        if not self._buscando():
            return
        if hasattr(self.proceso, "terminate"):         # los procesos se pueden cortar; los hilos no
            self.proceso.terminate()
            self.proceso.join(timeout=1)
        self._soltar_proceso()                         # si era un hilo, su resultado se ignora
        if not silencioso:
            self.texto_barra.set("Búsqueda cancelada.")
            self.barra_estado.config(fg=TEXTO_SUAVE)
            self.mensaje_reporte.config(text=f"Se canceló la búsqueda con «{self.nombre_resultado}».",
                                        fg=TEXTO_SUAVE)
            self._actualizar_botones()

    def _soltar_proceso(self):
        if self.revision_pendiente is not None:
            self.ventana.after_cancel(self.revision_pendiente)
            self.revision_pendiente = None
        self.proceso = None
        self.cola = None

    # ================================ Reporte ================================

    def _limpiar_reporte(self):
        for valor in self.datos_reporte.values():
            valor.config(text="—", fg=TEXTO)
        self.mensaje_reporte.config(text="Aún no se ha ejecutado ningún algoritmo.", fg=TEXTO_SUAVE)
        self.camino_reporte.config(text="")

    def _mostrar_resultado(self, resultado):
        nombre = self.nombre_resultado
        datos = self.datos_reporte
        datos["nodos"].config(text=f"{resultado['nodos_expandidos']:,}".replace(",", "."))
        datos["profundidad"].config(text=str(resultado["profundidad"]))
        datos["tiempo"].config(text=f"{resultado['tiempo']:.4f} s")

        if resultado["limite_superado"]:
            limite = f"{logica.LIMITE_NODOS_EXPANDIDOS:,}".replace(",", ".")
            self._mostrar_falla(f"«{nombre}» se detuvo: superó el límite de {limite} nodos expandidos "
                                f"sin encontrar solución.")
            return
        if not resultado["exito"]:
            self._mostrar_falla(f"«{nombre}» falló: no existe solución para este mundo.")
            return

        datos["pasos"].config(text=str(resultado["profundidad_solucion"]))
        if nombre in logica.ALGORITMOS_QUE_MUESTRAN_COSTO:
            datos["costo"].config(text=formatear_costo(resultado["costo_total"]), fg=VERDE)
        else:
            datos["costo"].config(text="—", fg=TEXTO_APAGADO)
        self.mensaje_reporte.config(text=f"✔  Solución encontrada con «{nombre}».", fg=VERDE)
        self.camino_reporte.config(
            text="Camino:  " + " ".join(FLECHAS.get(m, m) for m in resultado["movimientos"]))

        self.resultado = resultado
        self.paso_actual = 0
        self.en_pausa = False
        self.animacion_terminada = False
        self.texto_barra.set(f"«{nombre}» encontró una solución de "
                             f"{resultado['profundidad_solucion']} pasos · animando...")
        self.barra_estado.config(fg=ACENTO_CLARO)
        self._actualizar_botones()
        self.mostrar_paso(0)
        self.animacion_pendiente = self.ventana.after(400, self._animar_siguiente_paso)

    def _mostrar_falla(self, mensaje):
        self.mensaje_reporte.config(text=f"✖  {mensaje}", fg=ROJO)
        self.texto_barra.set(mensaje)
        self.barra_estado.config(fg=ROJO)
        self._actualizar_botones()

    # ================================ Animación ================================

    def _animar_siguiente_paso(self):
        """Desliza el robot de la casilla actual a la siguiente, en varios cuadritos."""
        self.animacion_pendiente = None
        if self.resultado is None or self.en_pausa:
            return
        estados = self.resultado["estados"]
        if self.paso_actual >= len(estados) - 1:
            self._terminar_animacion()
            return

        origen, destino = estados[self.paso_actual], estados[self.paso_actual + 1]
        duracion = float(self.pausa_ms.get())
        cuadros = max(1, min(10, int(duracion // 25)))
        dx = (destino.columna - origen.columna) * self.tam_casilla / cuadros
        dy = (destino.fila - origen.fila) * self.tam_casilla / cuadros
        self._deslizar(cuadros, dx, dy, max(10, int(duracion / cuadros)))

    def _deslizar(self, cuadros_restantes, dx, dy, intervalo):
        self.lienzo.move("robot", dx, dy)
        if cuadros_restantes > 1:
            self.animacion_pendiente = self.ventana.after(
                intervalo, self._deslizar, cuadros_restantes - 1, dx, dy, intervalo)
        else:
            self.paso_actual += 1
            self.mostrar_paso(self.paso_actual)        # al llegar: trata cultivo, recarga, sube a avioneta...
            self.animacion_pendiente = self.ventana.after(intervalo, self._animar_siguiente_paso)

    def _terminar_animacion(self):
        self.animacion_terminada = True
        self.texto_barra.set(f"¡Todos los cultivos tratados!  ·  «{self.nombre_resultado}» · "
                             f"{self.resultado['profundidad_solucion']} pasos")
        self.barra_estado.config(fg=VERDE)
        self._actualizar_botones()

    def _detener_animacion(self):
        if self.animacion_pendiente is not None:
            self.ventana.after_cancel(self.animacion_pendiente)
            self.animacion_pendiente = None

    def pausar_o_continuar(self):
        if self.resultado is None or not self.resultado["exito"]:
            return
        if self.animacion_terminada:                   # "Repetir"
            self.reiniciar_animacion()
            self.en_pausa = False
        elif not self.en_pausa:                        # "Pausar"
            self.en_pausa = True
            self._detener_animacion()
            self.mostrar_paso(self.paso_actual)        # deja el robot justo en su casilla
            self.texto_barra.set(f"Animación en pausa · paso {self.paso_actual}")
            self._actualizar_botones()
            return
        else:                                          # "Continuar"
            self.en_pausa = False
        self.texto_barra.set(f"«{self.nombre_resultado}» · animando...")
        self.barra_estado.config(fg=ACENTO_CLARO)
        self._actualizar_botones()
        self._animar_siguiente_paso()

    def reiniciar_animacion(self):
        """Vuelve el robot al inicio. La solución se conserva para poder reproducirla otra vez."""
        if self.problema is None:
            return
        self._detener_animacion()
        self.paso_actual = 0
        self.en_pausa = True
        self.animacion_terminada = False
        self.mostrar_paso(0)
        if self.resultado is not None and self.resultado["exito"]:
            self.texto_barra.set("Animación reiniciada · pulsa «Reproducir»")
            self.barra_estado.config(fg=ACENTO_CLARO)
        self._actualizar_botones()

    # ================================ Botones ================================

    def _actualizar_botones(self):
        buscando = self._buscando()
        hay_solucion = self.resultado is not None and self.resultado["exito"]

        self.boton_buscar.config(state="disabled" if buscando or self.problema is None else "normal",
                                 text="Buscando..." if buscando else "Buscar")
        self.boton_cancelar.config(state="normal" if buscando else "disabled")
        self.boton_cargar.config(state="disabled" if buscando else "normal")
        for boton in self.botones_tipo.values():
            boton.config(state="disabled" if buscando else "normal")
        for radio in self.marco_algoritmos.winfo_children():
            radio.config(state="disabled" if buscando else "normal")

        if not hay_solucion:
            self.boton_pausa.config(text="Pausar", state="disabled")
            self.boton_reiniciar.config(state="disabled")
            return
        if self.animacion_terminada:
            texto = "Repetir"
        elif self.en_pausa:
            texto = "Reproducir" if self.paso_actual == 0 else "Continuar"
        else:
            texto = "Pausar"
        self.boton_pausa.config(text=texto, state="normal")
        self.boton_reiniciar.config(state="normal")

    def cerrar(self):
        self.cancelar_busqueda(silencioso=True)
        self.ventana.destroy()


def activar_nitidez_en_windows():
    """En pantallas con escala (125 %, 150 %...) Windows dibuja la ventana borrosa si no se le avisa."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


if __name__ == "__main__":
    multiprocessing.freeze_support()
    activar_nitidez_en_windows()
    ventana_principal = tk.Tk()
    AplicacionAgroBot(ventana_principal)
    ventana_principal.mainloop()
