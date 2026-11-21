"""Pantallas del sistema.

Cada lista recibe una 'fuente': una función de vistas_qt/datos.py que,
con el texto del buscador y los filtros elegidos, devuelve las filas reales
de la base de datos.
"""
from typing import Callable

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QGridLayout,
)

from .tabla import ModeloTabla, crear_tabla


def _encabezado(titulo: str, subtitulo: str, boton: str | None = None):
    fila = QHBoxLayout()
    textos = QVBoxLayout()
    textos.setSpacing(2)
    t = QLabel(titulo); t.setObjectName("tituloPagina")
    s = QLabel(subtitulo); s.setObjectName("subtituloPagina")
    textos.addWidget(t); textos.addWidget(s)
    fila.addLayout(textos)
    fila.addStretch()
    b = None
    if boton:
        b = QPushButton(boton); b.setObjectName("botonPrincipal")
        b.setCursor(Qt.PointingHandCursor)
        fila.addWidget(b, alignment=Qt.AlignTop)
    return fila, b, t, s


class PaginaInicio(QWidget):
    """Números grandes sueltos, sin tarjetas. 'fuente' devuelve [(valor, etiqueta), ...]."""

    def __init__(self, fuente: Callable[[], list[tuple[str, str]]],
                 titulo: str = "Inicio", subtitulo: str = "Lo que necesita tu atención hoy"):
        super().__init__()
        self.fuente = fuente
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 32, 40, 32)
        lay.setSpacing(36)
        enc, _, _, _ = _encabezado(titulo, subtitulo)
        lay.addLayout(enc)

        self.grilla = QGridLayout()
        self.grilla.setHorizontalSpacing(64)
        self.grilla.setVerticalSpacing(0)
        lay.addLayout(self.grilla)
        lay.addStretch()
        self.numeros: list[QLabel] = []
        self.etiquetas: list[QLabel] = []

    def recargar(self):
        datos = self.fuente()
        while len(self.numeros) < len(datos):
            i = len(self.numeros)
            n = QLabel(); n.setObjectName("numeroGrande")
            e = QLabel(); e.setObjectName("etiquetaNumero")
            self.grilla.addWidget(n, 0, i); self.grilla.addWidget(e, 1, i)
            self.numeros.append(n); self.etiquetas.append(e)
        self.grilla.setColumnStretch(len(datos), 1)
        for (valor, etiqueta), n, e in zip(datos, self.numeros, self.etiquetas):
            n.setText(valor); e.setText(etiqueta)


class PaginaLista(QWidget):
    """Pantalla tipo lista: título + botón principal, buscador, filtros y tabla."""

    cambio_datos = Signal()  # avisa a la ventana para actualizar el número de pendientes

    def __init__(self, titulo: str, subtitulo: str, columnas: list[str],
                 fuente: Callable[[str, dict], tuple[list[list], list]],
                 columna_estado: int | None = None, columna_ancha: int | None = None,
                 boton: str | None = "Registrar",
                 filtros: dict[str, list[str] | Callable[[], list[str]]] | None = None,
                 texto_buscar: str = "Buscar...", texto_vacio: str = "Todavía no hay registros."):
        super().__init__()
        self.fuente = fuente
        self.objetos: list = []   # el objeto (oficio, acta...) de cada fila
        self.texto_vacio = texto_vacio

        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 32, 40, 24)
        lay.setSpacing(18)

        enc, self.boton_principal, _, _ = _encabezado(titulo, subtitulo, boton)
        lay.addLayout(enc)

        self.buscador = QLineEdit(); self.buscador.setObjectName("buscador")
        self.buscador.setPlaceholderText(texto_buscar)
        self.buscador.setClearButtonEnabled(True)
        lay.addWidget(self.buscador)

        # Filtros en una sola línea + contador a la derecha
        fila_f = QHBoxLayout(); fila_f.setSpacing(4)
        self.combos: dict[str, QComboBox] = {}
        self._opciones = filtros or {}
        for nombre in self._opciones:
            c = QComboBox(); c.setCursor(Qt.PointingHandCursor)
            c.currentIndexChanged.connect(lambda _=0: self.recargar())
            self.combos[nombre] = c
            fila_f.addWidget(c)
        fila_f.addStretch()
        self.contador = QLabel(); self.contador.setObjectName("subtituloPagina")
        fila_f.addWidget(self.contador)
        lay.addLayout(fila_f)

        self.modelo = ModeloTabla(columnas)
        self.tabla, self.orden = crear_tabla(self.modelo, columna_estado, columna_ancha)
        lay.addWidget(self.tabla, 1)

        self.vacio = QLabel(); self.vacio.setObjectName("subtituloPagina")
        self.vacio.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.vacio.hide()
        lay.addWidget(self.vacio, 1)

        # Espera un instante después de escribir antes de buscar (no consulta en cada tecla)
        self._espera = QTimer(self); self._espera.setSingleShot(True); self._espera.setInterval(250)
        self._espera.timeout.connect(self.recargar)
        self.buscador.textChanged.connect(lambda _: self._espera.start())

        self._llenar_combos()

    def _llenar_combos(self):
        for nombre, opciones in self._opciones.items():
            c = self.combos[nombre]
            lista = opciones() if callable(opciones) else opciones
            actual = c.currentText()
            c.blockSignals(True)
            c.clear()
            c.addItems([f"{nombre}: Todos"] + lista)
            i = c.findText(actual)
            c.setCurrentIndex(i if i >= 0 else 0)
            c.blockSignals(False)

    def filtros_elegidos(self) -> dict:
        return {nombre: c.currentText() for nombre, c in self.combos.items()}

    def objeto_elegido(self):
        """El oficio/recibido/acta de la fila seleccionada (o None)."""
        sel = self.tabla.selectionModel().selectedRows()
        if not sel:
            return None
        return self.objetos[self.orden.mapToSource(sel[0]).row()]

    def recargar(self):
        self._llenar_combos()
        filas, self.objetos = self.fuente(self.buscador.text(), self.filtros_elegidos())
        self.modelo.cambiar_filas(filas)
        n = len(filas)
        self.contador.setText(f"{n} registro{'s' if n != 1 else ''}")
        hay_busqueda = bool(self.buscador.text().strip()) or any(
            not c.currentText().endswith("Todos") for c in self.combos.values())
        self.tabla.setVisible(n > 0)
        self.vacio.setVisible(n == 0)
        self.vacio.setText("No se encontró nada con esa búsqueda." if hay_busqueda else self.texto_vacio)
