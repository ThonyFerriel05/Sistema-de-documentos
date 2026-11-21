"""Trámites y plantillas: agregar un trámite con su Word y abrir o reemplazar la plantilla.

RF13 (el oficio se genera desde la plantilla de su trámite) y RF14 (agregar o reemplazar
la plantilla de cada trámite).
"""
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QMenu, QPushButton, QWidget

from modelos.tipo_tramite import CARPETA_PLANTILLAS, TipoTramite
from servicios.inicio import NOMBRE_TRAMITE_BASE
from servicios.plantillas import crear_plantilla_base, marcas_faltantes
from utilidades import abrir_con_programa

from .formularios import (FormularioBase, campo_texto, confirmar, mostrar_en_carpeta,
                          mostrar_error, mostrar_info)

AYUDA_MARCAS = (
    "Escriba estas marcas en el Word donde quiera que el sistema ponga cada dato:\n\n"
    "{{CODIGO}}  →  DIR.CARR.ING.SISTEMAS F.IN.I. OF. No. 112/2026\n"
    "{{FECHA}}  →  21 de noviembre de 2026\n"
    "{{DESTINATARIO_NOMBRE}}  y  {{DESTINATARIO_CARGO}}\n"
    "{{VIA_NOMBRE}}  y  {{VIA_CARGO}}  (si no hay VIA, esas líneas se borran solas)\n"
    "{{ASUNTO}}  →  lo que va en REF.\n"
    "{{GESTION}}  →  2026\n\n"
    "Lo demás (saludo, cuerpo, despedida) se escribe normal y queda igual en todos los oficios."
)


def elegir_word(padre) -> str | None:
    ruta, _ = QFileDialog.getOpenFileName(padre, "Elegir plantilla de Word", "",
                                          "Documento de Word (*.docx)")
    return ruta or None


def avisar_marcas(padre, ruta) -> bool:
    """Si al Word le faltan marcas, avisa y pregunta si se usa igual."""
    faltan = marcas_faltantes(ruta)
    if not faltan:
        return True
    return confirmar(padre, "A este Word le faltan estas marcas:\n  " + "\n  ".join(faltan) +
                     "\n\nLos oficios de este trámite saldrán sin esos datos."
                     "\n¿Usarlo de todas formas?")


def ruta_plantilla_base() -> Path:
    """El Word del 'Oficio general'. Si se borró, se arma uno nuevo aparte."""
    ruta = CARPETA_PLANTILLAS / f"{NOMBRE_TRAMITE_BASE}.docx"
    if ruta.exists():
        return ruta
    temporal = Path(tempfile.mkdtemp()) / "base.docx"
    crear_plantilla_base(temporal)
    return temporal


class CampoWord(QWidget):
    """Por defecto se copia la plantilla base; con el botón se elige un Word propio."""

    TEXTO_BASE = f"Copia del «{NOMBRE_TRAMITE_BASE}» (después escribe la REF. y el cuerpo)"

    def __init__(self):
        super().__init__()
        self.ruta: str | None = None
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(8)
        self.nombre = QLabel(self.TEXTO_BASE); self.nombre.setObjectName("notaFormulario")
        self.nombre.setWordWrap(True)
        elegir = QPushButton("Usar un Word propio…"); elegir.clicked.connect(self._elegir)
        self.quitar = QPushButton("Quitar"); self.quitar.clicked.connect(self._quitar)
        lay.addWidget(self.nombre, 1); lay.addWidget(elegir); lay.addWidget(self.quitar)
        self.quitar.hide()

    def _elegir(self):
        ruta = elegir_word(self)
        if ruta and avisar_marcas(self, ruta):
            self.ruta = ruta
            self.nombre.setText(Path(ruta).name)
            self.quitar.show()

    def _quitar(self):
        self.ruta = None
        self.nombre.setText(self.TEXTO_BASE)
        self.quitar.hide()


class FormularioTramite(FormularioBase):
    def __init__(self, padre):
        super().__init__(padre, "Agregar trámite",
                         "Un trámite es un oficio que se repite (ej.: solicitud de certificación presupuestaria). "
                         "Su plantilla ya trae la REF. y el cuerpo escritos.",
                         "Agregar")
        self.nombre = campo_texto("", "Ej.: Solicitud de certificación presupuestaria")
        self.word = CampoWord()
        self.campos.addRow("Nombre", self.nombre)
        self.campos.addRow("Plantilla", self.word)
        self.tramite = None

    def guardar(self):
        nombre = self.nombre.text().strip()
        if not nombre:
            raise ValueError("Falta completar: nombre.")
        self.tramite = TipoTramite.crear(nombre, self.word.ruta or ruta_plantilla_base())


def agregar(padre, al_cambiar):
    form = FormularioTramite(padre)
    if form.exec():
        al_cambiar()
        t = form.tramite
        if not form.word.ruta and confirmar(
                padre, f"Se agregó el trámite «{t.nombre}».\n\n¿Abrir su plantilla en Word para "
                       f"escribir la REF. y el cuerpo?\n(Guarde con Ctrl+S al terminar.)"):
            abrir_con_programa(t.obtener_plantilla())
        elif form.word.ruta:
            mostrar_info(padre, f"Se agregó el trámite «{t.nombre}». Ya aparece al registrar "
                                f"un oficio.")


def crear_menu(padre, tramite: TipoTramite, al_cambiar) -> QMenu:
    def accion(funcion):
        def envoltura():
            try:
                funcion(TipoTramite.obtener(tramite.id_tipo))  # datos frescos
            except PermissionError:
                mostrar_error(padre, "La plantilla está abierta en Word. Ciérrela y vuelva a intentar.")
            except Exception as error:
                mostrar_error(padre, error)
        return envoltura

    def reemplazar(t):
        ruta = elegir_word(padre)
        if not ruta or not avisar_marcas(padre, ruta):
            return
        if not confirmar(padre, f"La plantilla de «{t.nombre}» se cambiará por:\n{Path(ruta).name}\n\n"
                                f"Los oficios nuevos usarán esta. Los ya generados no cambian. "
                                f"¿Continuar?"):
            return
        t.reemplazar_plantilla(ruta)
        al_cambiar()
        mostrar_info(padre, f"Plantilla de «{t.nombre}» reemplazada.")

    m = QMenu(padre)
    m.addAction("Abrir plantilla en Word", accion(lambda t: abrir_con_programa(t.obtener_plantilla())))
    m.addAction("Abrir carpeta de la plantilla",
                accion(lambda t: mostrar_en_carpeta(t.obtener_plantilla())))
    m.addSeparator()
    m.addAction("Reemplazar plantilla por otro Word…", accion(reemplazar))
    m.addSeparator()
    m.addAction("¿Qué marcas puedo usar?", lambda: mostrar_info(padre, AYUDA_MARCAS))
    return m


def conectar(pagina, ventana):
    """Le da vida a la pantalla de Trámites y plantillas."""

    def menu(_pos=None):
        t = pagina.objeto_elegido()
        if t is not None:
            crear_menu(pagina, t, pagina.recargar).exec(QCursor.pos())

    pagina.boton_principal.clicked.connect(lambda: agregar(pagina, pagina.recargar))
    pagina.tabla.setContextMenuPolicy(Qt.CustomContextMenu)
    pagina.tabla.customContextMenuRequested.connect(menu)
    pagina.tabla.doubleClicked.connect(lambda _: menu())
