# AgroBot — Proyecto 1 de Inteligencia Artificial (Univalle)

**Hecho por:** Andres Muñoz, Thomas Herrera, Brandon Franco y Daniel Micolta

AgroBot es un robot agrícola que se mueve por una cuadrícula y aplica fertilizante en todos los
cultivos secos. La aplicación lee el mundo desde un archivo de texto, lo dibuja, ejecuta el
algoritmo de búsqueda elegido, anima la solución y muestra un reporte con nodos expandidos,
profundidad del árbol, tiempo de cómputo y, para Costo uniforme y A*, el costo de la solución.

## Requisitos

- Python 3 con `tkinter` disponible.
- No requiere paquetes de pip ni imágenes externas: los íconos se dibujan en el Canvas.

## Cómo ejecutar

1. (Opcional) Copie su archivo `Prueba1.txt` dentro de esta carpeta. Si existe, se carga solo al abrir.
2. Desde esta carpeta, ejecute:

   ```
   python interfaz.py
   ```

3. Si no copió `Prueba1.txt`, use el botón **Cargar mundo...** para elegir cualquier archivo `.txt`.
4. Elija el tipo de búsqueda (**No informada** o **Informada**), el algoritmo y pulse **Buscar** (o Enter).

## Formato del archivo del mundo

Cada casilla es un número del 0 al 5. Se aceptan separados por espacios, tabulaciones, comas,
punto y coma o pegados. Todas las filas deben tener la misma cantidad de columnas.

| Valor | Significado |
|---|---|
| 0 | Casilla libre |
| 1 | Obstáculo (muro) |
| 2 | AgroBot (exactamente uno) |
| 3 | Cultivo seco |
| 4 | Depósito de fertilizante (uno) |
| 5 | Avioneta (una) |

Ejemplo (mundo del enunciado):

```
1 1 4 1 1 1 5 1 1 1
0 0 0 0 0 0 0 0 0 0
0 1 1 0 1 1 1 1 1 0
0 1 1 0 0 0 0 0 0 0
2 0 0 3 1 1 0 1 1 1
0 1 1 3 1 1 0 1 1 1
0 1 1 0 1 1 0 0 3 1
0 0 0 0 1 1 0 1 0 1
1 1 1 0 1 1 0 1 0 1
1 1 1 0 0 0 0 0 0 1
```

## Estructura del proyecto

```
AgroBot/
├── interfaz.py              # Ventana en tkinter. Es el archivo que se ejecuta.
├── logica.py                # Punto de acceso a la lógica: catálogo de algoritmos y ejecución en proceso aparte.
├── model.py                 # Lectura del mundo, constantes, clase Estado y clase Problema (reglas del robot).
├── dibujos.py               # Íconos del tablero (muros, robot, avioneta, depósito, cultivos) en el Canvas.
├── busquedas/
│   ├── __init__.py          # Paquete de los algoritmos de búsqueda.
│   ├── common.py            # Clase Nodo, poda de ciclos por rama y armado del resultado.
│   ├── no_informadas.py     # Amplitud, Costo uniforme y Profundidad evitando ciclos.
│   └── informadas.py        # Heurística, Avara y A*.
├── .gitignore
└── README.md
```

### Cómo se relacionan los módulos

```
interfaz.py ──► logica.py ──► model.py
     │              │
     │              └──► busquedas/no_informadas.py ─┐
     │              └──► busquedas/informadas.py ────┼──► busquedas/common.py
     │                                               └──► model.py (límite de nodos)
     └──► dibujos.py
```

- `interfaz.py` solo habla con `logica.py` (datos y algoritmos) y con `dibujos.py` (íconos).
- `logica.py` reúne en un solo lugar las constantes, `leer_mundo`, `Problema` y los cinco
  algoritmos, y define `ejecutar_busqueda_en_proceso`, que corre la búsqueda en un proceso aparte
  para que la ventana no se congele y se pueda cancelar.
- Todos los algoritmos usan `Nodo`, `forma_ciclo` y `armar_resultado` de `busquedas/common.py`.

## Algoritmos disponibles

| Tipo | Algoritmo | Frontera | Muestra costo |
|---|---|---|---|
| No informada | Amplitud | Cola (FIFO) | No |
| No informada | Costo uniforme | Cola de prioridad por g(n) | Sí |
| No informada | Profundidad evitando ciclos | Pila (LIFO) | No |
| Informada | Avara | Cola de prioridad por h(n) | No |
| Informada | A* | Cola de prioridad por f(n) = g(n) + h(n) | Sí |

Todos evitan ciclos dentro de cada rama. La revisión se reinicia después de un evento (subirse a la
avioneta, llegar al depósito o tratar un cultivo), para que el robot pueda devolverse por donde vino.
Si una búsqueda supera 1.000.000 de nodos expandidos, se detiene y lo informa.

## Heurística

```
h(n) = (distancia Manhattan al cultivo seco más cercano) / 2
```

Es admisible: el robot debe llegar al menos a un cultivo seco, necesita como mínimo tantos
movimientos como esa distancia y cada movimiento cuesta como mínimo 1/2 (en avioneta).
La explicación completa y la justificación de la admisibilidad están en el informe del proyecto.
