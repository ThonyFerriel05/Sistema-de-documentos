"""Pendientes (RF10): las mismas acciones que en cada lista, sin tener que ir a buscarlas."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from modelos.expedido import DocumentoExpedido

from . import expedidos, recibidos


def conectar(pagina, ventana):
    def al_cambiar():
        pagina.recargar()
        ventana.actualizar_contador_pendientes()

    def menu(_pos=None):
        obj = pagina.objeto_elegido()
        if obj is None:
            return
        modulo = expedidos if isinstance(obj, DocumentoExpedido) else recibidos
        modulo.crear_menu(pagina, obj, al_cambiar).exec(QCursor.pos())

    pagina.tabla.setContextMenuPolicy(Qt.CustomContextMenu)
    pagina.tabla.customContextMenuRequested.connect(menu)
    pagina.tabla.doubleClicked.connect(lambda _: menu())
