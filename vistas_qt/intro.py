"""Intro al abrir el programa: logo de la carrera y nombre del sistema.

Aparece mientras el programa prepara la base de datos y arma las pantallas,
así la directora no mira una pantalla vacía. Dura poco (unos 2 segundos)
y se salta con un clic.
"""
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, QPoint
from PySide6.QtGui import QPixmap, QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect

from database import CARPETA_PROGRAMA

from .estilo import ACENTO, TEXTO, TEXTO_SUAVE

LOGO = CARPETA_PROGRAMA / "vistas_qt" / "iconos" / "logo_carrera.png"
ANCHO, ALTO, MARGEN = 520, 360, 24   # MARGEN: espacio para la sombra


class Panel(QWidget):
    """El rectángulo blanco con esquinas redondeadas."""

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        camino = QPainterPath()
        camino.addRoundedRect(self.rect(), 18, 18)
        p.fillPath(camino, QColor("white"))


class Intro(QWidget):
    saltar = Signal()   # clic: no esperar el tiempo mínimo

    def __init__(self):
        super().__init__(None, Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(ANCHO + 2 * MARGEN, ALTO + 2 * MARGEN)
        self.setCursor(Qt.PointingHandCursor)

        panel = Panel(self)
        panel.setGeometry(MARGEN, MARGEN, ANCHO, ALTO)
        sombra = QGraphicsDropShadowEffect(blurRadius=40, xOffset=0, yOffset=8)
        sombra.setColor(QColor(0, 0, 0, 45))
        panel.setGraphicsEffect(sombra)

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(40, 44, 40, 30)
        lay.setSpacing(0)

        self.logo = QLabel(); self.logo.setAlignment(Qt.AlignHCenter)
        imagen = QPixmap(str(LOGO))
        if not imagen.isNull():
            self.logo.setPixmap(imagen.scaledToHeight(112, Qt.SmoothTransformation))
        lay.addWidget(self.logo)
        lay.addSpacing(22)

        titulo = QLabel("Sistema de Documentación")
        titulo.setAlignment(Qt.AlignHCenter)
        titulo.setStyleSheet(f"font-size: 26px; font-weight: 600; color: {TEXTO};")
        sub = QLabel("Dirección de Carrera · Ingeniería en Sistemas")
        sub.setAlignment(Qt.AlignHCenter)
        sub.setStyleSheet(f"font-size: 15px; color: {TEXTO_SUAVE};")
        lay.addWidget(titulo); lay.addSpacing(6); lay.addWidget(sub)
        lay.addStretch()

        self.estado = QLabel("Preparando…")
        self.estado.setAlignment(Qt.AlignHCenter)
        self.estado.setStyleSheet(f"font-size: 12px; color: {ACENTO};")
        pie = QLabel("F.IN.I. – U.A.G.R.M.  ·  Versión beta")
        pie.setAlignment(Qt.AlignHCenter)
        pie.setStyleSheet(f"font-size: 11px; color: {TEXTO_SUAVE};")
        lay.addWidget(self.estado); lay.addSpacing(4); lay.addWidget(pie)

        self._animaciones = []   # se guardan para que Python no las borre a mitad

    # ---------- animaciones ----------

    def aparecer(self):
        """Se centra en la pantalla, aparece suave y el logo sube un poco."""
        pantalla = self.screen().availableGeometry()
        self.move(pantalla.center() - self.rect().center())
        self.setWindowOpacity(0.0)
        self.show()
        self.logo.parentWidget().layout().activate()   # para saber dónde queda el logo
        self._animar(self, b"windowOpacity", 0.0, 1.0, 350)
        destino = self.logo.pos()
        self._animar(self.logo, b"pos", destino + QPoint(0, 14), destino, 600, QEasingCurve.OutCubic)

    def desaparecer(self, al_terminar):
        self.estado.setText("Listo")
        a = self._animar(self, b"windowOpacity", 1.0, 0.0, 280)
        a.finished.connect(al_terminar)
        a.finished.connect(self.close)

    def _animar(self, objeto, propiedad, desde, hasta, ms, curva=QEasingCurve.InOutQuad):
        a = QPropertyAnimation(objeto, propiedad, self)
        a.setStartValue(desde); a.setEndValue(hasta)
        a.setDuration(ms); a.setEasingCurve(curva)
        a.start()
        self._animaciones.append(a)
        return a

    def mouseReleaseEvent(self, evento):
        self.saltar.emit()
        super().mouseReleaseEvent(evento)
