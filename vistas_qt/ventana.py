"""Ventana principal: menú lateral a la izquierda + pantalla elegida a la derecha."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QStackedWidget, QStyledItemDelegate,
)

from modelos.acta import MODALIDADES
from modelos.expedido import ESTADOS as ESTADOS_EXPEDIDO
from modelos.recibido import CATEGORIAS, ESTADOS as ESTADOS_RECIBIDO

from . import actas as acciones_actas, datos, expedidos as acciones_expedidos, pendientes as acciones_pendientes, recibidos as acciones_recibidos
from .estilo import TEXTO_SUAVE
from .paginas import PaginaInicio, PaginaLista


class DelegadoMenu(QStyledItemDelegate):
    """Dibuja la sección normal y, si tiene, el número a la derecha (ej. Pendientes 2)."""

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        numero = index.data(Qt.UserRole)
        if numero:
            painter.save()
            painter.setPen(QColor(TEXTO_SUAVE))
            painter.drawText(option.rect.adjusted(0, 0, -12, 0), Qt.AlignVCenter | Qt.AlignRight, str(numero))
            painter.restore()


def _mayus(lista):
    return [x.capitalize() for x in lista]


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Documentación — Dirección de Carrera")
        self.setMinimumSize(1100, 640)   # entra en una laptop de 1366×768
        self.resize(1280, 720)

        central = QWidget()
        raiz = QHBoxLayout(central)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        self.paginas = QStackedWidget(); self.paginas.setObjectName("contenido")
        self.secciones = self._crear_paginas()  # [(nombre, pantalla), ...]

        raiz.addWidget(self._crear_menu())
        for _, p in self.secciones:
            self.paginas.addWidget(p)
        raiz.addWidget(self.paginas, 1)

        self.setCentralWidget(central)
        self.lista_menu.setCurrentRow(0)

    # ---- menú lateral ----
    def _crear_menu(self) -> QWidget:
        menu = QWidget(); menu.setObjectName("menu")
        menu.setFixedWidth(240)
        lay = QVBoxLayout(menu)
        lay.setContentsMargins(14, 22, 14, 16)
        lay.setSpacing(2)

        nombre = QLabel("Dirección de Carrera"); nombre.setObjectName("nombreSistema")
        sub = QLabel("Ingeniería en Sistemas · F.IN.I."); sub.setObjectName("subNombre")
        lay.addWidget(nombre); lay.addWidget(sub)
        lay.addSpacing(18)

        self.lista_menu = QListWidget(); self.lista_menu.setObjectName("listaMenu")
        self.lista_menu.setCursor(Qt.PointingHandCursor)
        self.lista_menu.setItemDelegate(DelegadoMenu(self.lista_menu))
        for nombre_seccion, _ in self.secciones:
            QListWidgetItem(nombre_seccion, self.lista_menu)
        self.lista_menu.currentRowChanged.connect(self._ir_a)
        lay.addWidget(self.lista_menu, 1)

        version = QLabel("Versión beta"); version.setObjectName("subNombre")
        lay.addWidget(version)
        return menu

    def _ir_a(self, i: int):
        self.paginas.setCurrentIndex(i)
        pagina = self.paginas.currentWidget()
        if hasattr(pagina, "recargar"):
            pagina.recargar()  # siempre muestra lo último guardado
        self.actualizar_contador_pendientes()

    def actualizar_contador_pendientes(self):
        item = self.lista_menu.item(1)  # "Pendientes"
        item.setData(Qt.UserRole, datos.total_pendientes() or None)

    # ---- pantallas ----
    def _crear_paginas(self):
        inicio = PaginaInicio(datos.numeros_inicio)
        pendientes = PaginaLista(
            "Pendientes", "Recibidos por responder y oficios que esperan respuesta. Doble clic para ver acciones",
            ["Tipo", "Número", "Remitente / destinatario", "Asunto", "Fecha", "Estado"],
            datos.filas_pendientes, columna_estado=5, columna_ancha=3, boton=None,
            texto_buscar="Buscar en pendientes", texto_vacio="No hay nada pendiente. Todo al día.",
        )
        expedidos = PaginaLista(
            "Oficios expedidos", "Doble clic o clic derecho sobre un oficio para ver sus acciones",
            ["Código", "Fecha de envío", "Destinatario", "Asunto", "Estado"],
            datos.filas_expedidos, columna_estado=4, columna_ancha=3, boton="Registrar oficio",
            filtros={"Estado": _mayus(ESTADOS_EXPEDIDO), "Gestión": datos.gestiones_expedidos},
            texto_buscar="Buscar por número, asunto o destinatario",
            texto_vacio="Todavía no hay oficios registrados.",
        )
        recibidos = PaginaLista(
            "Documentos recibidos", "Doble clic o clic derecho sobre un documento para ver sus acciones",
            ["N.º interno", "N.º de oficio", "Recibido", "Remitente", "Asunto", "Categoría", "Estado"],
            datos.filas_recibidos, columna_estado=6, columna_ancha=4, boton="Registrar recibido",
            filtros={"Estado": _mayus(ESTADOS_RECIBIDO), "Categoría": CATEGORIAS},
            texto_buscar="Buscar por número de oficio, remitente o asunto",
            texto_vacio="Todavía no hay documentos recibidos.",
        )
        actas = PaginaLista(
            "Actas de graduación", "Doble clic o clic derecho sobre un acta para abrir o adjuntar su escaneado",
            ["N.º interno", "N.º de acta", "Código CPD", "Carnet", "Nota", "Modalidad"],
            datos.filas_actas, columna_ancha=5, boton="Registrar acta",
            filtros={"Modalidad": MODALIDADES},
            texto_buscar="Buscar por carnet", texto_vacio="Todavía no hay actas registradas.",
        )
        tramites = PaginaLista(
            "Trámites y plantillas", "Plantilla Word de cada trámite frecuente",
            ["Trámite", "Plantilla"], datos.filas_tramites, boton="Agregar trámite",
            texto_buscar="Buscar trámite",
        )
        # POR HACER: pantalla de configuración (número inicial RF16 y copia de seguridad RF12)
        config = PaginaInicio(lambda: [("—", "Pantalla en construcción")],
                              "Configuración y respaldo", "Número inicial de oficio y copias de seguridad")
        acciones_expedidos.conectar(expedidos, self)
        acciones_recibidos.conectar(recibidos, self)
        acciones_pendientes.conectar(pendientes, self)
        acciones_actas.conectar(actas, self)
        return [
            ("Inicio", inicio), ("Pendientes", pendientes), ("Oficios expedidos", expedidos),
            ("Documentos recibidos", recibidos), ("Actas de graduación", actas),
            ("Trámites y plantillas", tramites), ("Configuración y respaldo", config),
        ]
