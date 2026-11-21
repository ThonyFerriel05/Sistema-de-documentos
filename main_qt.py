"""Punto de entrada de la nueva interfaz (PySide6).

Uso:  python main_qt.py
"""
import sys
import traceback

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from database import CARPETA_PROGRAMA
from servicios.inicio import preparar_sistema
from vistas_qt.estilo import QSS


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")      # base neutra; encima va nuestro estilo
    app.setStyleSheet(QSS)
    app.setWindowIcon(QIcon(str(CARPETA_PROGRAMA / "vistas_qt" / "iconos" / "sistema.ico")))
    try:
        preparar_sistema()      # crea la base y la plantilla inicial si no existen
        from vistas_qt.ventana import VentanaPrincipal
        ventana = VentanaPrincipal()
        ventana.show()
        QTimer.singleShot(400, ventana.recordar_copia)  # primero se ve la ventana, después el aviso
    except Exception:
        QMessageBox.critical(None, "Error al iniciar", traceback.format_exc())
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
