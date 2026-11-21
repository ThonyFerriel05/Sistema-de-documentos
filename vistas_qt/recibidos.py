"""Documentos recibidos: registrar y acciones sobre un documento
(clic derecho o doble clic en la fila).

RF04 registrar, RF05 cambiar estado, RF11 abrir escaneado, RF15 adjuntar escaneado,
RF17 categoría, RF18 número interno por gestión.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QActionGroup, QCursor
from PySide6.QtWidgets import QCheckBox, QMenu

from database import CARPETA_SISTEMA
from modelos.recibido import CATEGORIAS, ESTADOS, DocumentoRecibido

from .formularios import (CampoArchivo, FormularioBase, campo_fecha_hora, campo_texto, confirmar,
                          elegir_escaneado, fecha_hora_iso, lista, mostrar_en_carpeta,
                          mostrar_error, mostrar_info)


class FormularioRecibido(FormularioBase):
    def __init__(self, padre):
        super().__init__(padre, "Registrar documento recibido",
                         "La fecha y hora son las del sello de recibido. El número interno se asigna solo.",
                         "Registrar")
        self.nro = campo_texto("", "Ej.: OF. 233/2026")
        self.fecha_hora = campo_fecha_hora()
        self.remitente = campo_texto("", "Quién lo envía")
        self.asunto = campo_texto("", "De qué trata")
        self.categoria = lista(CATEGORIAS, "Otro")
        self.requiere = QCheckBox("Requiere respuesta")
        self.requiere.setToolTip("Si es solo de conocimiento, no lo marque: queda completado "
                                 "y no aparece en pendientes.")
        self.requiere.setChecked(True)
        self.archivo = CampoArchivo()

        f = self.campos
        f.addRow("N.º de oficio", self.nro)
        f.addRow("Sello de recibido", self.fecha_hora)
        f.addRow("Remitente", self.remitente)
        f.addRow("Asunto", self.asunto)
        f.addRow("Categoría", self.categoria)
        f.addRow("", self.requiere)
        f.addRow("Escaneado", self.archivo)

        self.fecha_hora.dateTimeChanged.connect(lambda _: self._mostrar_numero())
        self._mostrar_numero()
        self.documento = None

    def _mostrar_numero(self):
        gestion = self.fecha_hora.date().year()
        numero = DocumentoRecibido.proximo_nro_registro(gestion)
        self.nota.setText(f"Próximo N.º interno: {numero:02d}/{gestion}")

    def guardar(self):
        doc = DocumentoRecibido(
            nro_oficio=self.nro.text(), fecha_hora_recepcion=fecha_hora_iso(self.fecha_hora),
            remitente=self.remitente.text(), asunto=self.asunto.text(),
            requiere_respuesta=self.requiere.isChecked(), categoria=self.categoria.currentText(),
        )
        # Regla por confirmar: no se bloquea, solo se avisa.
        if doc.nro_oficio.strip() and doc.remitente.strip() and doc.posible_repetido():
            if not confirmar(self, "Ya hay un documento con ese número y ese remitente en esta "
                                   "gestión.\n¿Registrarlo de todas formas?"):
                return False
        doc.registrar()
        if self.archivo.ruta:
            doc.adjuntar_escaneado(self.archivo.ruta)
        self.documento = doc


def registrar(padre, al_cambiar):
    form = FormularioRecibido(padre)
    if form.exec():
        al_cambiar()
        d = form.documento
        mostrar_info(padre, f"Se registró el documento {d.nro_oficio} con el número interno "
                            f"{d.registro_corto}.")


def crear_menu(padre, documento: DocumentoRecibido, al_cambiar) -> QMenu:
    def accion(funcion):
        def envoltura():
            try:
                funcion(DocumentoRecibido.obtener(documento.id_recibido))  # datos frescos
            except Exception as error:
                mostrar_error(padre, error)
        return envoltura

    def cambiar(estado):
        def hacer(d):
            d.cambiar_estado(estado)
            al_cambiar()
        return hacer

    def adjuntar(d):
        ruta = elegir_escaneado(padre)
        if ruta:
            d.adjuntar_escaneado(ruta)
            al_cambiar()
            mostrar_info(padre, f"Escaneado guardado en el documento {d.nro_oficio}.")

    m = QMenu(padre)
    sub = m.addMenu("Cambiar estado")
    grupo = QActionGroup(sub)
    for estado in ESTADOS:
        a = sub.addAction(estado.capitalize(), accion(cambiar(estado)))
        a.setCheckable(True); a.setChecked(estado == documento.estado)
        grupo.addAction(a)
    m.addSeparator()
    m.addAction("Adjuntar escaneado", accion(adjuntar))
    tiene = bool(documento.archivo_escaneado)
    a = m.addAction("Abrir escaneado", accion(lambda d: d.abrir_archivo()))
    a.setEnabled(tiene)
    a = m.addAction("Abrir carpeta del escaneado",
                    accion(lambda d: mostrar_en_carpeta(CARPETA_SISTEMA / d.archivo_escaneado)))
    a.setEnabled(tiene)
    return m


def conectar(pagina, ventana):
    """Le da vida a la pantalla de Documentos recibidos."""

    def al_cambiar():
        pagina.recargar()
        ventana.actualizar_contador_pendientes()

    def menu(_pos=None):
        d = pagina.objeto_elegido()
        if d is not None:
            crear_menu(pagina, d, al_cambiar).exec(QCursor.pos())

    pagina.boton_principal.clicked.connect(lambda: registrar(pagina, al_cambiar))
    pagina.tabla.setContextMenuPolicy(Qt.CustomContextMenu)
    pagina.tabla.customContextMenuRequested.connect(menu)
    pagina.tabla.doubleClicked.connect(lambda _: menu())
