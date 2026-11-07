AgroBot - Proyecto 1 de Inteligencia Artificial (Univalle)
Hecho por: Andres Muñoz, Thomas Herrera y Daniel Micolta

Cómo ejecutar:
    1. Copie su archivo Prueba1.txt dentro de esta carpeta (se carga solo al abrir).
    2. Ejecute:  python interfaz.py

Archivos:
    interfaz.py  -> la ventana (este es el que se ejecuta)
    logica.py    -> punto de acceso, catálogo y ejecución en proceso separado
    modelo.py    -> lectura del mundo, estados, constantes y reglas del robot
    busquedas/comunes.py       -> nodos, ciclos y resultados
    busquedas/no_informadas.py -> amplitud, costo uniforme y profundidad
    busquedas/informadas.py    -> heurística, avara y A*
    dibujos.py   -> íconos del tablero

Informe técnico:
    INFORME_PROYECTO.md -> arquitectura, reglas, algoritmos, demostración de
                           admisibilidad y consistencia, pruebas y limitaciones.

Pruebas (desde esta carpeta):
    python -m unittest discover -s tests -v

Requisitos:
    Python 3 con tkinter disponible. No requiere paquetes de pip ni imágenes externas.
    Prueba1.txt es opcional; también se puede cargar un mundo desde la ventana.
