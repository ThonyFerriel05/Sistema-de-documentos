"""Configuración y respaldo.

RF16: último número de oficio usado en papel antes de empezar con el sistema.
RF12: copia de seguridad con un botón (a una memoria USB u otra carpeta),
      y recordatorio si pasaron más de 7 días desde la última.
"""
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

from database import conectar
from modelos.configuracion import definir_ultimo_numero_previo, obtener_ultimo_numero_previo
from modelos.expedido import DocumentoExpedido
from servicios.respaldo import (CARPETA_RESPALDOS, DIAS_RECORDATORIO, crear_respaldo,
                                dias_sin_respaldo, fecha_ultimo_respaldo)

from .formularios import campo_texto, confirmar, lista, mostrar_en_carpeta, mostrar_error, mostrar_info
from .paginas import _encabezado


def _titulo(texto):
    t = QLabel(texto); t.setObjectName("tituloFormulario")
    return t


def _nota(texto=""):
    n = QLabel(texto); n.setObjectName("subtituloPagina"); n.setWordWrap(True)
    return n


class PaginaConfiguracion(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 32, 40, 32)
        lay.setSpacing(10)
        enc, _, _, _ = _encabezado("Configuración y respaldo",
                                   "Número inicial de oficio y copias de seguridad")
        lay.addLayout(enc)
        lay.addSpacing(26)

        # ---- RF16: número de oficio ----
        lay.addWidget(_titulo("Número de oficio"))
        lay.addWidget(_nota("Si empezó a usar el sistema a mitad de año, escriba el último número "
                            "de oficio que usó en papel. El sistema seguirá desde el siguiente. "
                            "En la gestión que viene empieza solo en 01."))
        fila = QHBoxLayout(); fila.setSpacing(10)
        fila.addWidget(QLabel("Gestión"))
        anio = date.today().year
        self.gestion = lista([str(g) for g in range(anio + 1, 2019, -1)], str(anio))
        self.gestion.setStyleSheet("min-width: 70px; max-width: 70px;")
        self.gestion.currentIndexChanged.connect(lambda _: self._mostrar_numero())
        fila.addWidget(self.gestion)
        fila.addSpacing(16)
        fila.addWidget(QLabel("Último número usado en papel"))
        self.ultimo = campo_texto("", "Ej.: 111")
        self.ultimo.setValidator(QIntValidator(0, 9999, self))
        self.ultimo.setStyleSheet("min-width: 90px; max-width: 90px;")  # el QSS general lo estira
        fila.addWidget(self.ultimo)
        guardar = QPushButton("Guardar"); guardar.clicked.connect(self._guardar_numero)
        fila.addWidget(guardar)
        fila.addStretch()
        lay.addLayout(fila)
        self.proximo = _nota()
        lay.addWidget(self.proximo)
        lay.addSpacing(30)

        # ---- RF12: copia de seguridad ----
        lay.addWidget(_titulo("Copia de seguridad"))
        lay.addWidget(_nota("Guarda en un solo archivo .zip la base de datos, los escaneados, "
                            "los Word generados y las plantillas. Conviene guardarla en una "
                            "memoria USB, fuera de esta computadora."))
        self.estado_copia = QLabel(); self.estado_copia.setObjectName("estadoCopia")
        lay.addWidget(self.estado_copia)
        botones = QHBoxLayout(); botones.setSpacing(10)
        usb = QPushButton("Guardar copia en otra carpeta (USB)")
        usb.setObjectName("botonPrincipal"); usb.setCursor(Qt.PointingHandCursor)
        usb.clicked.connect(self._copia_usb)
        aqui = QPushButton("Guardar copia en esta computadora"); aqui.clicked.connect(self._copia_aqui)
        ver = QPushButton("Ver copias guardadas aquí"); ver.clicked.connect(self._ver_copias)
        botones.addWidget(usb); botones.addWidget(aqui); botones.addWidget(ver); botones.addStretch()
        lay.addLayout(botones)
        lay.addStretch()

    # ---- número ----
    def _mostrar_numero(self):
        g = int(self.gestion.currentText())
        previo = obtener_ultimo_numero_previo(g)
        self.ultimo.setText(str(previo) if previo else "")
        self.proximo.setText(f"Próximo oficio de {g}: {DocumentoExpedido.proximo_numero(g):02d}/{g}")

    def _guardar_numero(self):
        g, texto = int(self.gestion.currentText()), self.ultimo.text().strip()
        try:
            if not texto:
                raise ValueError("Escriba el último número usado (o 0 si no usó ninguno).")
            if not confirmar(self, f"El próximo oficio de {g} será el "
                                   f"{int(texto) + 1:02d}/{g}.\n¿Es correcto?"):
                return
            definir_ultimo_numero_previo(g, texto)
        except Exception as error:
            mostrar_error(self, error)
        self._mostrar_numero()

    # ---- copia ----
    def _mostrar_estado_copia(self):
        ultima, dias = fecha_ultimo_respaldo(), dias_sin_respaldo()
        if ultima is None:
            texto, color = "Todavía no se hizo ninguna copia.", "rojo"
        else:
            cuando = "hoy" if dias == 0 else ("ayer" if dias == 1 else f"hace {dias} días")
            texto = f"Última copia: {cuando} ({ultima.strftime('%d/%m/%Y %H:%M')})."
            color = "rojo" if dias > DIAS_RECORDATORIO else "verde"
        self.estado_copia.setText(texto)
        self.estado_copia.setProperty("color", color)
        self.estado_copia.style().unpolish(self.estado_copia)
        self.estado_copia.style().polish(self.estado_copia)

    def _hacer_copia(self, carpeta=None):
        try:
            self.setCursor(Qt.WaitCursor)
            ruta = crear_respaldo(carpeta)
        except Exception as error:
            self.unsetCursor()
            mostrar_error(self, f"No se pudo guardar la copia.\n{error}")
            return
        self.unsetCursor()
        self._mostrar_estado_copia()
        if confirmar(self, f"Copia guardada:\n{ruta}\n\n¿Abrir la carpeta para verla?"):
            mostrar_en_carpeta(ruta)

    def _copia_usb(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Elegir la memoria USB o carpeta destino")
        if carpeta:
            self._hacer_copia(carpeta)

    def _copia_aqui(self):
        self._hacer_copia()

    def _ver_copias(self):
        CARPETA_RESPALDOS.mkdir(parents=True, exist_ok=True)
        copias = sorted(CARPETA_RESPALDOS.glob("respaldo_*.zip"))
        try:
            mostrar_en_carpeta(copias[-1] if copias else CARPETA_RESPALDOS)
        except Exception as error:
            mostrar_error(self, error)

    def recargar(self):
        self._mostrar_numero()
        self._mostrar_estado_copia()


def hay_datos() -> bool:
    with conectar() as c:
        return any(c.execute(f"SELECT 1 FROM {t} LIMIT 1").fetchone()
                   for t in ("documento_expedido", "documento_recibido", "acta"))


def recordar_copia(ventana, ir_a_configuracion):
    """Al abrir el programa: si pasaron más de 7 días (o nunca hubo copia y ya hay datos)."""
    dias = dias_sin_respaldo()
    if dias is None and not hay_datos():
        return
    if dias is not None and dias <= DIAS_RECORDATORIO:
        return
    texto = ("Todavía no se hizo ninguna copia de seguridad." if dias is None
             else f"Pasaron {dias} días desde la última copia de seguridad.")
    if confirmar(ventana, texto + "\n\n¿Ir a hacer una ahora?"):
        ir_a_configuracion()
