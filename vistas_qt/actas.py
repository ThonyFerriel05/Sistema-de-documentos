"""Actas de graduación: registrar y acciones sobre un acta
(clic derecho o doble clic en la fila).

RF06 registrar, RF07 aviso si el número o el código ya existen, RF08 buscar por carnet,
RF11 abrir escaneado, RF15 adjuntar escaneado, RF18 número interno, RF19 filtrar por modalidad.
"""
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QIntValidator
from PySide6.QtWidgets import QMenu

from database import CARPETA_SISTEMA, conectar as conectar_base
from modelos.acta import MODALIDADES, Acta

from .formularios import (CampoArchivo, FormularioBase, campo_texto, elegir_escaneado, lista,
                          mostrar_en_carpeta, mostrar_error, mostrar_info)


class FormularioActa(FormularioBase):
    def __init__(self, padre):
        super().__init__(padre, "Registrar acta de graduación",
                         "El número de acta y el código los asigna el CPD. "
                         "El sistema avisa si alguno ya está registrado.",
                         "Registrar")
        self.nro_acta = campo_texto("", "Como figura en el acta")
        self.codigo = campo_texto("", "Código del CPD")
        self.carnet = campo_texto("", "Ej.: 14117756 SC")
        self.nota_acta = campo_texto("", "De 0 a 100")
        self.nota_acta.setValidator(QIntValidator(0, 100, self))
        self.modalidad = lista(MODALIDADES)
        self.archivo = CampoArchivo()

        f = self.campos
        f.addRow("N.º de acta", self.nro_acta)
        f.addRow("Código CPD", self.codigo)
        f.addRow("Carnet", self.carnet)
        f.addRow("Nota", self.nota_acta)
        f.addRow("Modalidad", self.modalidad)
        f.addRow("Escaneado", self.archivo)

        gestion = date.today().year
        with conectar_base() as c:
            numero = Acta.generar_nro_registro(gestion, c)
        self.nota.setText(f"Próximo N.º interno: {numero:02d}/{gestion}")
        self.acta = None

    def guardar(self):
        acta = Acta(self.nro_acta.text(), self.codigo.text(), self.carnet.text(),
                    self.nota_acta.text(), self.modalidad.currentText())
        acta.registrar()  # si se repite el número o el código, avisa y no guarda (RF07)
        if self.archivo.ruta:
            acta.adjuntar_escaneado(self.archivo.ruta)
        self.acta = acta


def registrar(padre, al_cambiar):
    form = FormularioActa(padre)
    if form.exec():
        al_cambiar()
        a = form.acta
        extra = "" if a.archivo_escaneado else "\nRecuerde adjuntar el escaneado del acta."
        mostrar_info(padre, f"Se registró el acta N.º {a.nro_acta} (carnet {a.carnet}) "
                            f"con el número interno {a.registro_corto}.{extra}")


def crear_menu(padre, acta: Acta, al_cambiar) -> QMenu:
    def accion(funcion):
        def envoltura():
            try:
                funcion(Acta.obtener(acta.id_acta))  # datos frescos
            except Exception as error:
                mostrar_error(padre, error)
        return envoltura

    def adjuntar(a):
        ruta = elegir_escaneado(padre)
        if ruta:
            a.adjuntar_escaneado(ruta)
            al_cambiar()
            mostrar_info(padre, f"Escaneado guardado en el acta N.º {a.nro_acta}.")

    m = QMenu(padre)
    tiene = bool(acta.archivo_escaneado)
    a = m.addAction("Abrir escaneado", accion(lambda x: x.abrir_archivo()))
    a.setEnabled(tiene)
    a = m.addAction("Abrir carpeta del escaneado",
                    accion(lambda x: mostrar_en_carpeta(CARPETA_SISTEMA / x.archivo_escaneado)))
    a.setEnabled(tiene)
    m.addSeparator()
    m.addAction("Reemplazar escaneado" if tiene else "Adjuntar escaneado", accion(adjuntar))
    return m


def conectar(pagina, ventana):
    """Le da vida a la pantalla de Actas de graduación."""

    def al_cambiar():
        pagina.recargar()

    def menu(_pos=None):
        a = pagina.objeto_elegido()
        if a is not None:
            crear_menu(pagina, a, al_cambiar).exec(QCursor.pos())

    pagina.boton_principal.clicked.connect(lambda: registrar(pagina, al_cambiar))
    pagina.tabla.setContextMenuPolicy(Qt.CustomContextMenu)
    pagina.tabla.customContextMenuRequested.connect(menu)
    pagina.tabla.doubleClicked.connect(lambda _: menu())
