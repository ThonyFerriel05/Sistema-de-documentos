"""Tabla reutilizable para todas las listas (expedidos, recibidos, actas...).

- ModeloTabla: le dice a Qt qué datos mostrar (columnas y filas).
- DelegadoEstado: dibuja el puntito de color + el texto del estado.
- crear_tabla(): arma la tabla ya con el estilo limpio (sin cuadrícula, filas altas).
"""
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QRectF
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QTableView, QStyledItemDelegate, QHeaderView, QAbstractItemView, QStyle

from .estilo import ESTADO_COLOR, TEXTO

ROL_ORDEN = Qt.UserRole + 1  # dato que se usa para ordenar la columna


class ModeloTabla(QAbstractTableModel):
    """Cada celda puede ser un texto o una pareja (texto, clave_para_ordenar)."""

    def __init__(self, columnas: list[str], filas: list[list] | None = None, parent=None):
        super().__init__(parent)
        self.columnas = columnas
        self.filas = filas or []

    def rowCount(self, parent=QModelIndex()):
        return len(self.filas)

    def columnCount(self, parent=QModelIndex()):
        return len(self.columnas)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        celda = self.filas[index.row()][index.column()]
        if role == Qt.DisplayRole:
            return str(celda[0] if isinstance(celda, tuple) else celda)
        if role == ROL_ORDEN:
            return celda[1] if isinstance(celda, tuple) else str(celda).lower()
        if role == Qt.ToolTipRole:  # texto completo al dejar el mouse encima
            return str(celda[0] if isinstance(celda, tuple) else celda)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columnas[section].upper()
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignLeft | Qt.AlignVCenter)
        return None

    def cambiar_filas(self, filas: list[list]):
        self.beginResetModel()
        self.filas = filas
        self.endResetModel()


class DelegadoEstado(QStyledItemDelegate):
    """Pinta '● Esperando' con el color que corresponde al estado."""

    def sizeHint(self, option, index):
        tam = super().sizeHint(option, index)
        tam.setWidth(tam.width() + 24)  # lugar para el punto de color
        return tam

    def paint(self, painter: QPainter, option, index):
        opt = option
        self.initStyleOption(opt, index)
        texto = opt.text
        opt.text = ""
        opt.widget.style().drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)

        color = QColor(ESTADO_COLOR.get(texto.lower(), "#9CA3AF"))
        r = option.rect
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(QRectF(r.left() + 10, r.center().y() - 4, 8, 8))
        painter.setPen(QColor(TEXTO))
        painter.drawText(r.adjusted(26, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, texto.capitalize())
        painter.restore()


def crear_tabla(modelo: ModeloTabla, columna_estado: int | None = None,
                columna_ancha: int | None = None) -> tuple[QTableView, QSortFilterProxyModel]:
    """Devuelve la tabla y el 'intermediario' que permite ordenar por columna."""
    orden = QSortFilterProxyModel()
    orden.setSourceModel(modelo)
    orden.setSortRole(ROL_ORDEN)

    tabla = QTableView()
    tabla.setModel(orden)
    tabla.setShowGrid(False)
    tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabla.setSelectionMode(QAbstractItemView.SingleSelection)
    tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tabla.setMouseTracking(True)  # para que la fila se aclare al pasar el mouse
    tabla.verticalHeader().setVisible(False)
    tabla.verticalHeader().setDefaultSectionSize(44)  # filas altas, más aire
    tabla.setWordWrap(False)        # una sola línea por fila; lo largo termina en "..."
    tabla.setTextElideMode(Qt.ElideRight)
    tabla.setFocusPolicy(Qt.NoFocus)

    cab = tabla.horizontalHeader()
    cab.setHighlightSections(False)
    cab.setMinimumSectionSize(90)
    cab.setResizeContentsPrecision(50)  # mide solo 50 filas: rápido aunque haya miles
    cab.setSectionResizeMode(QHeaderView.ResizeToContents)
    if columna_ancha is not None:
        cab.setSectionResizeMode(columna_ancha, QHeaderView.Stretch)  # el asunto ocupa el espacio libre
    else:
        cab.setStretchLastSection(True)
    # Sin orden inicial: se respeta el de la base (lo más nuevo primero).
    cab.setSortIndicator(-1, Qt.AscendingOrder)
    tabla.setSortingEnabled(True)

    if columna_estado is not None:
        tabla.setItemDelegateForColumn(columna_estado, DelegadoEstado(tabla))
    return tabla, orden
