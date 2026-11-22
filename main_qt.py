"""Punto de entrada de la nueva interfaz (PySide6).

Uso:  python main_qt.py

Al abrir: primero aparece la intro (logo y nombre). Mientras se ve, el programa
prepara la base de datos y arma las pantallas. Después la intro se desvanece y
aparece la ventana principal.
"""
import sys
import time
import traceback

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from database import CARPETA_PROGRAMA
from servicios.inicio import preparar_sistema
from vistas_qt.estilo import QSS
from vistas_qt.intro import Intro

DURACION_MINIMA_INTRO = 1.8   # segundos: lo justo para verla, sin hacer esperar


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")      # base neutra; encima va nuestro estilo
    app.setStyleSheet(QSS)
    app.setWindowIcon(QIcon(str(CARPETA_PROGRAMA / "vistas_qt" / "iconos" / "sistema.ico")))

    intro = Intro()
    inicio = time.monotonic()
    estado = {"ventana": None, "mostrada": False}

    def mostrar_ventana():
        if estado["mostrada"] or estado["ventana"] is None:
            return
        estado["mostrada"] = True
        ventana = estado["ventana"]

        def abrir():
            ventana.show()
            QTimer.singleShot(400, ventana.recordar_copia)  # primero se ve la ventana, después el aviso
        intro.desaparecer(abrir)

    def preparar():
        try:
            preparar_sistema()      # crea la base y la plantilla inicial si no existen
            from vistas_qt.ventana import VentanaPrincipal
            estado["ventana"] = VentanaPrincipal()
        except Exception:
            intro.close()
            QMessageBox.critical(None, "Error al iniciar", traceback.format_exc())
            sys.exit(1)
        falta = DURACION_MINIMA_INTRO - (time.monotonic() - inicio)
        QTimer.singleShot(max(0, int(falta * 1000)), mostrar_ventana)

    intro.saltar.connect(mostrar_ventana)   # un clic en la intro la salta
    intro.aparecer()
    QTimer.singleShot(400, preparar)        # deja que la intro termine de aparecer
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
