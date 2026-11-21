"""Oficios expedidos: registrar + generar Word, y acciones sobre un oficio
(clic derecho o doble clic en la fila).

RF01 registrar, RF02 respuesta, RF03 reenvío de rechazado, RF11 abrir escaneado,
RF13 generar Word con plantilla, RF15 adjuntar escaneado.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QCheckBox, QMenu

from modelos.expedido import ESTADOS, DocumentoExpedido
from modelos.tipo_tramite import TipoTramite
from modelos.documento import CARPETA_ARCHIVOS
from utilidades import abrir_con_programa, iso_a_fecha, nombre_archivo_seguro

from .formularios import (FormularioBase, campo_fecha, campo_texto, confirmar, elegir_escaneado,
                          fecha_iso, lista, mostrar_en_carpeta, mostrar_error, mostrar_info)


def ruta_word(o: DocumentoExpedido):
    """Dónde quedó el Word de este oficio (mismo nombre que usa generar_con_plantilla)."""
    nombre = nombre_archivo_seguro(f"Oficio No {o.codigo:02d} {o.asunto}")
    return CARPETA_ARCHIVOS / "oficios_generados" / str(o.gestion) / f"{nombre}.docx"


def abrir_word(o: DocumentoExpedido):
    """Abre el Word que ya existe (con lo que la directora escribió). Si no existe, lo crea."""
    ruta = ruta_word(o)
    abrir_con_programa(ruta if ruta.exists() else o.generar_con_plantilla())


class FormularioOficio(FormularioBase):
    def __init__(self, padre, original: DocumentoExpedido | None = None):
        subt = (f"Reenvío del oficio rechazado {original.numero_corto}. Tendrá un número nuevo."
                if original else "El número se asigna solo. Al guardar se abre el Word para completar el cuerpo.")
        super().__init__(padre, "Registrar oficio", subt, "Registrar y abrir Word")
        self.original = original
        base = original.preparar_reenvio() if original else None

        self.tramites = {t.nombre: t for t in TipoTramite.listar()}
        self.fecha = campo_fecha()
        self.tramite = lista(list(self.tramites))
        self.a_nombre = campo_texto(base.destinatario_nombre if base else "", "Ej.: Ing. Juan Pérez")
        self.a_cargo = campo_texto(base.destinatario_cargo if base else "", "Ej.: Decano F.IN.I.")
        self.via_nombre = campo_texto(base.via_nombre if base else "", "Opcional")
        self.via_cargo = campo_texto(base.via_cargo if base else "", "Opcional")
        self.asunto = campo_texto(base.asunto if base else "", "Lo que va en REF.")
        self.requiere = QCheckBox("Requiere respuesta")
        self.requiere.setToolTip("Si no se marca, el oficio queda completado al enviarlo y no aparece en pendientes.")
        self.requiere.setChecked(base.requiere_respuesta if base else True)
        if base:
            for nombre, t in self.tramites.items():
                if t.id_tipo == base.id_tipo:
                    self.tramite.setCurrentText(nombre)

        f = self.campos
        f.addRow("Fecha de envío", self.fecha)
        f.addRow("Trámite", self.tramite)
        f.addRow("A (nombre)", self.a_nombre)
        f.addRow("Cargo", self.a_cargo)
        f.addRow("VIA (nombre)", self.via_nombre)
        f.addRow("Cargo VIA", self.via_cargo)
        f.addRow("Referencia", self.asunto)
        f.addRow("", self.requiere)

        self.fecha.dateChanged.connect(lambda _: self._mostrar_numero())
        self._mostrar_numero()
        self.oficio = None
        self.ruta_word = None

    def _mostrar_numero(self):
        gestion = self.fecha.date().year()
        numero = DocumentoExpedido.proximo_numero(gestion)
        self.nota.setText(f"Próximo número: {numero:02d}/{gestion}")

    def guardar(self):
        tramite = self.tramites.get(self.tramite.currentText())
        if not tramite:
            raise ValueError("Elija un trámite. Si no hay ninguno, créelo en 'Trámites y plantillas'.")
        oficio = DocumentoExpedido(
            fecha_envio=fecha_iso(self.fecha),
            destinatario_nombre=self.a_nombre.text(), destinatario_cargo=self.a_cargo.text(),
            via_nombre=self.via_nombre.text().strip(), via_cargo=self.via_cargo.text().strip(),
            asunto=self.asunto.text(), id_tipo=tramite.id_tipo,
            id_original=self.original.id_expedido if self.original else None,
            requiere_respuesta=self.requiere.isChecked(),
        )
        oficio.registrar()                       # RF01: guarda y asigna el número
        self.ruta_word = oficio.generar_con_plantilla()  # RF13: crea el Word
        self.oficio = oficio


class FormularioRespuesta(FormularioBase):
    """RF02: aprobado, rechazado o completado, con número y fecha de resolución."""

    def __init__(self, padre, oficio: DocumentoExpedido):
        super().__init__(padre, f"Respuesta al oficio {oficio.numero_corto}", oficio.asunto)
        self.oficio = oficio
        self.estado = lista([e.capitalize() for e in ESTADOS], oficio.estado.capitalize())
        self.nro = campo_texto(oficio.nro_resolucion or "", "Ej.: RCC 45/2026")
        self.fecha = campo_fecha(oficio.fecha_resolucion)
        self.campos.addRow("Estado", self.estado)
        self.campos.addRow("N.º de resolución", self.nro)
        self.campos.addRow("Fecha de resolución", self.fecha)

    def guardar(self):
        # registrar_respuesta espera la fecha como dd/mm/aaaa
        self.oficio.registrar_respuesta(self.estado.currentText().lower(), self.nro.text().strip(),
                                        iso_a_fecha(fecha_iso(self.fecha)))


def registrar(padre, al_cambiar, original: DocumentoExpedido | None = None):
    form = FormularioOficio(padre, original)
    if form.exec():
        al_cambiar()
        try:
            abrir_con_programa(form.ruta_word)
        except Exception as error:
            mostrar_error(padre, error)


def crear_menu(padre, oficio: DocumentoExpedido, al_cambiar) -> QMenu:
    """Menú de acciones de un oficio. al_cambiar(): recarga las listas después de un cambio."""

    def accion(funcion):
        def envoltura():
            try:
                funcion(DocumentoExpedido.obtener(oficio.id_expedido))  # datos frescos
            except Exception as error:
                mostrar_error(padre, error)
        return envoltura

    def responder(o):
        if FormularioRespuesta(padre, o).exec():
            al_cambiar()

    def adjuntar(o):
        ruta = elegir_escaneado(padre)
        if ruta:
            o.adjuntar_escaneado(ruta)
            al_cambiar()
            mostrar_info(padre, f"Escaneado guardado en el oficio {o.numero_corto}.")

    def regenerar(o):
        if ruta_word(o).exists() and not confirmar(
                padre, f"Se reemplazará el Word del oficio {o.numero_corto} por uno nuevo desde la "
                       f"plantilla.\nSe perderá lo que se haya escrito en el cuerpo. ¿Continuar?"):
            return
        abrir_con_programa(o.generar_con_plantilla())

    def carpeta(o):
        ruta = ruta_word(o)
        if not ruta.exists():
            o.generar_con_plantilla()
        mostrar_en_carpeta(ruta)

    m = QMenu(padre)
    m.addAction("Abrir Word del oficio", accion(abrir_word))
    m.addAction("Abrir carpeta del oficio", accion(carpeta))
    m.addAction("Registrar respuesta", accion(responder))
    m.addSeparator()
    m.addAction("Adjuntar escaneado firmado", accion(adjuntar))
    a = m.addAction("Abrir escaneado", accion(lambda o: o.abrir_archivo()))
    a.setEnabled(bool(oficio.archivo_escaneado))
    if oficio.estado == "rechazado":
        m.addSeparator()
        m.addAction("Reenviar (oficio nuevo enlazado)",
                    accion(lambda o: registrar(padre, al_cambiar, original=o)))
    m.addSeparator()
    m.addAction("Volver a generar Word desde la plantilla…", accion(regenerar))
    return m


def conectar(pagina, ventana):
    """Le da vida a la pantalla de Oficios expedidos."""

    def al_cambiar():
        pagina.recargar()
        ventana.actualizar_contador_pendientes()

    def menu(_pos=None):
        o = pagina.objeto_elegido()
        if o is not None:
            crear_menu(pagina, o, al_cambiar).exec(QCursor.pos())

    pagina.boton_principal.clicked.connect(lambda: registrar(pagina, al_cambiar))
    pagina.tabla.setContextMenuPolicy(Qt.CustomContextMenu)
    pagina.tabla.customContextMenuRequested.connect(menu)
    pagina.tabla.doubleClicked.connect(lambda _: menu())
