"""Ventanas emergentes (formularios) y mensajes.

Los formularios solo juntan los datos y llaman a los métodos de los modelos;
las reglas (número correlativo, validaciones) siguen estando en modelos/.
"""
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QDate, QDateTime, Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox, QCheckBox,
    QPushButton, QDateEdit, QDateTimeEdit, QMessageBox, QFileDialog, QWidget,
)

# Un escaneado más pesado que esto llena rápido la copia de seguridad.
LIMITE_ESCANEADO_MB = 10


# ---------- mensajes ----------

def _aviso(padre, icono, titulo, texto, botones) -> QMessageBox:
    """Aviso con los botones en español (RNF03): Qt los trae en inglés."""
    caja = QMessageBox(icono, titulo, texto, QMessageBox.NoButton, padre)
    for boton, nombre in botones:
        caja.addButton(boton).setText(nombre)
    return caja


def mostrar_error(padre, error):
    _aviso(padre, QMessageBox.Warning, "No se pudo completar", str(error),
           [(QMessageBox.Ok, "Aceptar")]).exec()


def mostrar_info(padre, texto):
    _aviso(padre, QMessageBox.Information, "Listo", texto, [(QMessageBox.Ok, "Aceptar")]).exec()


def confirmar(padre, texto) -> bool:
    caja = _aviso(padre, QMessageBox.Question, "Confirmar", texto,
                  [(QMessageBox.Yes, "Sí"), (QMessageBox.No, "No")])
    caja.setDefaultButton(QMessageBox.Yes)
    return caja.exec() == QMessageBox.Yes


def elegir_escaneado(padre) -> str | None:
    ruta, _ = QFileDialog.getOpenFileName(
        padre, "Elegir archivo escaneado", "",
        "Escaneados (*.pdf *.jpg *.jpeg *.png);;Todos los archivos (*.*)")
    return ruta or None


def mostrar_en_carpeta(ruta):
    """Abre el Explorador de Windows con el archivo ya marcado."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo:\n{ruta}")
    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer", "/select,", str(ruta)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(ruta)])
    else:
        subprocess.Popen(["xdg-open", str(ruta.parent)])


# ---------- piezas de formulario ----------

def campo_texto(valor: str = "", ayuda: str = "") -> QLineEdit:
    c = QLineEdit(valor or ""); c.setObjectName("campo"); c.setPlaceholderText(ayuda)
    return c


def _ajustar_calendario(c):
    """Calendario desplegable con tamaño fijo, la semana desde el lunes y sin cuadrícula."""
    cal = c.calendarWidget()
    cal.setMinimumSize(320, 250)
    cal.setGridVisible(False)
    cal.setFirstDayOfWeek(Qt.Monday)
    cal.setVerticalHeaderFormat(cal.VerticalHeaderFormat.NoVerticalHeader)
    cal.setHorizontalHeaderFormat(cal.HorizontalHeaderFormat.ShortDayNames)


def campo_fecha(iso: str | None = None) -> QDateEdit:
    """Fecha con calendario desplegable; se muestra dd/mm/aaaa."""
    c = QDateEdit(); c.setObjectName("campo")
    c.setCalendarPopup(True); c.setDisplayFormat("dd/MM/yyyy")
    _ajustar_calendario(c)
    c.setDate(QDate.fromString(iso, "yyyy-MM-dd") if iso else QDate.currentDate())
    return c


def fecha_iso(campo: QDateEdit) -> str:
    return campo.date().toString("yyyy-MM-dd")


def campo_fecha_hora(iso: str | None = None) -> QDateTimeEdit:
    """Fecha y hora (ej. sello de recibido). Viene con la hora actual, pero se puede cambiar."""
    c = QDateTimeEdit(); c.setObjectName("campo")
    c.setCalendarPopup(True); c.setDisplayFormat("dd/MM/yyyy HH:mm")
    _ajustar_calendario(c)
    c.setDateTime(QDateTime.fromString(iso, "yyyy-MM-dd HH:mm") if iso else QDateTime.currentDateTime())
    return c


def fecha_hora_iso(campo: QDateTimeEdit) -> str:
    return campo.dateTime().toString("yyyy-MM-dd HH:mm")


def lista(opciones: list[str], actual: str | None = None) -> QComboBox:
    c = QComboBox(); c.setObjectName("campo"); c.addItems(opciones)
    if actual and actual in opciones:
        c.setCurrentText(actual)
    return c


class CampoArchivo(QWidget):
    """Escaneado opcional dentro de un formulario: botón Elegir, nombre del archivo y Quitar.

    Solo recuerda la ruta (self.ruta); el modelo copia el archivo al guardar.
    """

    def __init__(self):
        super().__init__()
        self.ruta: str | None = None
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(8)
        self.elegir = QPushButton("Elegir archivo…"); self.elegir.clicked.connect(self._elegir)
        self.quitar = QPushButton("Quitar"); self.quitar.clicked.connect(self._quitar)
        self.nombre = QLabel("Sin archivo (se puede adjuntar después)")
        self.nombre.setObjectName("notaFormulario")
        lay.addWidget(self.elegir); lay.addWidget(self.nombre, 1); lay.addWidget(self.quitar)
        self.quitar.hide()

    def _elegir(self):
        ruta = elegir_escaneado(self)
        if not ruta:
            return
        megas = os.path.getsize(ruta) / (1024 * 1024)
        if megas > LIMITE_ESCANEADO_MB and not confirmar(
                self, f"El archivo pesa {megas:.0f} MB. Conviene escanear en blanco y negro "
                      f"para que ocupe menos.\n¿Usarlo de todas formas?"):
            return
        self.ruta = ruta
        self.nombre.setText(Path(ruta).name)
        self.quitar.show()

    def _quitar(self):
        self.ruta = None
        self.nombre.setText("Sin archivo (se puede adjuntar después)")
        self.quitar.hide()


class FormularioBase(QDialog):
    """Título arriba, campos en el medio y botones Cancelar / Aceptar abajo."""

    def __init__(self, padre, titulo: str, subtitulo: str = "", texto_aceptar: str = "Guardar"):
        super().__init__(padre)
        self.setObjectName("formulario")
        self.setWindowTitle(titulo)
        self.setMinimumWidth(560)

        self.raiz = QVBoxLayout(self)
        self.raiz.setContentsMargins(28, 24, 28, 20)
        self.raiz.setSpacing(14)
        t = QLabel(titulo); t.setObjectName("tituloFormulario")
        self.raiz.addWidget(t)
        if subtitulo:
            s = QLabel(subtitulo); s.setObjectName("subtituloPagina"); s.setWordWrap(True)
            self.raiz.addWidget(s)

        self.campos = QFormLayout()
        self.campos.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.campos.setHorizontalSpacing(16); self.campos.setVerticalSpacing(10)
        self.raiz.addLayout(self.campos)

        self.pie = QHBoxLayout()
        self.nota = QLabel(); self.nota.setObjectName("notaFormulario")
        self.pie.addWidget(self.nota)
        self.pie.addStretch()
        cancelar = QPushButton("Cancelar"); cancelar.clicked.connect(self.reject)
        self.aceptar = QPushButton(texto_aceptar); self.aceptar.setObjectName("botonPrincipal")
        self.aceptar.setDefault(True)
        self.aceptar.clicked.connect(self._intentar)
        self.pie.addWidget(cancelar); self.pie.addWidget(self.aceptar)
        self.raiz.addSpacing(6)
        self.raiz.addLayout(self.pie)

    def _intentar(self):
        """Si hay un error (falta un dato, etc.) se avisa y el formulario NO se cierra."""
        try:
            if self.guardar() is not False:
                self.accept()
        except Exception as error:
            mostrar_error(self, error)

    def guardar(self):  # cada formulario lo implementa
        raise NotImplementedError
