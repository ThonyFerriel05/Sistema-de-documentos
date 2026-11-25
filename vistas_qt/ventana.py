"""Ventana principal: menú lateral a la izquierda + pantalla elegida a la derecha."""
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QStackedWidget, QStyledItemDelegate, QPushButton, QApplication,
)

from modelos.acta import MODALIDADES
from modelos.expedido import ESTADOS as ESTADOS_EXPEDIDO
from modelos.recibido import CATEGORIAS, ESTADOS as ESTADOS_RECIBIDO

from . import actas as acciones_actas, configuracion as pantalla_configuracion, datos, expedidos as acciones_expedidos, pendientes as acciones_pendientes, recibidos as acciones_recibidos, tramites as acciones_tramites
from .estilo import TEXTO_SUAVE
from .inicio import PaginaInicio
from .paginas import PaginaLista


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

        # Historial para el botón Atrás: secciones visitadas antes de la actual.
        self.historial: list[int] = []
        self._actual = 0
        self._volviendo = False

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

        # Volver atrás también con el teclado (Alt + flecha izquierda)
        # y con el botón "atrás" lateral del mouse.
        QShortcut(QKeySequence("Alt+Left"), self, activated=self.atras)
        QShortcut(QKeySequence(QKeySequence.Back), self, activated=self.atras)
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, objeto, evento):
        if (evento.type() == QEvent.MouseButtonRelease and evento.button() == Qt.BackButton
                and self.isActiveWindow()):
            self.atras()
            return True
        return super().eventFilter(objeto, evento)

    def atras(self):
        """Vuelve a la sección anterior (como el botón Atrás de un navegador)."""
        if not self.historial:
            return
        self._volviendo = True
        self.lista_menu.setCurrentRow(self.historial.pop())
        self._volviendo = False

    def recordar_copia(self):
        """Se llama una vez, ya con la ventana abierta (RF12: aviso cada 7 días)."""
        ultima = self.lista_menu.count() - 1   # "Configuración y respaldo"
        pantalla_configuracion.recordar_copia(self, lambda: self.lista_menu.setCurrentRow(ultima))

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
        lay.addSpacing(10)

        self.boton_atras = QPushButton("←  Atrás"); self.boton_atras.setObjectName("botonAtras")
        self.boton_atras.setCursor(Qt.PointingHandCursor)
        self.boton_atras.setToolTip("Volver a la sección anterior (Alt + ←)")
        self.boton_atras.clicked.connect(self.atras)
        self.boton_atras.setEnabled(False)
        lay.addWidget(self.boton_atras, alignment=Qt.AlignLeft)
        lay.addSpacing(8)

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
        if i < 0:
            return
        if not self._volviendo and i != self._actual:
            self.historial.append(self._actual)
            del self.historial[:-30]          # no hace falta recordar más
        self._actual = i
        if hasattr(self, "boton_atras"):
            self.boton_atras.setEnabled(bool(self.historial))
        self.paginas.setCurrentIndex(i)
        pagina = self.paginas.currentWidget()
        if hasattr(pagina, "recargar"):
            pagina.recargar()  # siempre muestra lo último guardado
        self.actualizar_contador_pendientes()

    def ir_a_seccion(self, nombre: str):
        """Desde Inicio: cambia a la sección con ese nombre."""
        for i, (n, _) in enumerate(self.secciones):
            if n == nombre:
                self.lista_menu.setCurrentRow(i)
                return

    def _registrar_desde_inicio(self, que: str):
        """Los accesos '+ Oficio', '+ Recibido', '+ Acta' de Inicio abren el mismo formulario
        que el botón de su sección y, al guardar, actualizan Inicio y su lista."""
        modulo, seccion = {
            "oficio": (acciones_expedidos, "Oficios expedidos"),
            "recibido": (acciones_recibidos, "Documentos recibidos"),
            "acta": (acciones_actas, "Actas de graduación"),
        }[que]
        pagina = dict(self.secciones)[seccion]

        def al_cambiar():
            pagina.recargar()
            self.paginas.currentWidget().recargar()
            self.actualizar_contador_pendientes()
        modulo.registrar(self, al_cambiar)

    def actualizar_contador_pendientes(self):
        item = self.lista_menu.item(1)  # "Pendientes"
        item.setData(Qt.UserRole, datos.total_pendientes() or None)

    # ---- pantallas ----
    def _crear_paginas(self):
        inicio = PaginaInicio(datos.resumen_inicio, self.ir_a_seccion, self._registrar_desde_inicio)
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
            "Trámites y plantillas", "Doble clic o clic derecho sobre un trámite para abrir o reemplazar su plantilla",
            ["Trámite", "Plantilla"], datos.filas_tramites, boton="Agregar trámite",
            texto_buscar="Buscar trámite",
        )
        config = pantalla_configuracion.PaginaConfiguracion()
        acciones_expedidos.conectar(expedidos, self)
        acciones_recibidos.conectar(recibidos, self)
        acciones_pendientes.conectar(pendientes, self)
        acciones_actas.conectar(actas, self)
        acciones_tramites.conectar(tramites, self)
        return [
            ("Inicio", inicio), ("Pendientes", pendientes), ("Oficios expedidos", expedidos),
            ("Documentos recibidos", recibidos), ("Actas de graduación", actas),
            ("Trámites y plantillas", tramites), ("Configuración y respaldo", config),
        ]
