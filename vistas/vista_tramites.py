"""
vista_tramites.py
Trámites frecuentes y sus plantillas Word (RF14).
"""

from tkinter import filedialog

import customtkinter as ctk

from modelos.tipo_tramite import TipoTramite
from servicios.inicio import NOMBRE_TRAMITE_BASE
from utilidades import abrir_con_programa
from vistas.componentes import (FUENTE, Dialogo, Tabla, confirmar, mostrar_error,
                                mostrar_info, titulo)

AYUDA = (
    "Cada trámite tiene su Word con la referencia y el cuerpo ya escritos. "
    "Al generar un oficio, el sistema reemplaza estas marcas:\n"
    "{{FECHA}}  {{CODIGO}}  {{DESTINATARIO_NOMBRE}}  {{DESTINATARIO_CARGO}}  "
    "{{VIA_NOMBRE}}  {{VIA_CARGO}}  {{ASUNTO}}  {{GESTION}}\n"
    "Si el oficio no tiene VIA, las líneas con las marcas de VIA se borran solas."
)


class VistaTramites(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        titulo(self, "Trámites y plantillas")
        ctk.CTkLabel(self, text=AYUDA, font=FUENTE, justify="left", wraplength=900,
                     text_color="gray30").pack(anchor="w", padx=24, pady=(0, 10))

        self.tabla = Tabla(self, [("Trámite", 320), ("Archivo de plantilla", 500)], alto=12,
                           al_doble_click=self.abrir)
        self.tabla.pack(fill="both", expand=True, padx=24)

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(fill="x", padx=24, pady=10)
        for texto, accion in (("Nuevo trámite", self.nuevo),
                              ("Abrir plantilla para editar", self.abrir),
                              ("Reemplazar plantilla", self.reemplazar)):
            ctk.CTkButton(botones, text=texto, command=accion).pack(side="left", padx=4)
        self.cargar()

    def cargar(self):
        self.tabla.cargar([(t.id_tipo, (t.nombre, t.ruta_plantilla)) for t in TipoTramite.listar()])

    def _elegido(self):
        identificador = self.tabla.seleccionado()
        if identificador is None:
            raise ValueError("Primero elija un trámite de la lista.")
        return TipoTramite.obtener(identificador)

    def nuevo(self):
        try:
            datos = Dialogo.preguntar(self, "Nuevo trámite", [
                {"clave": "nombre", "etiqueta": "Nombre del trámite"},
            ])
            if not datos or not datos["nombre"]:
                return
            if confirmar("¿Empezar desde la plantilla base de oficio?\n"
                         "(Si elige 'No', podrá elegir un Word que ya tenga.)"):
                base = next(t for t in TipoTramite.listar() if t.nombre == NOMBRE_TRAMITE_BASE)
                origen = base.obtener_plantilla()
            else:
                origen = filedialog.askopenfilename(title="Elegir Word",
                                                    filetypes=[("Word", "*.docx")])
                if not origen:
                    return
            tramite = TipoTramite.crear(datos["nombre"], origen)
            self.cargar()
            mostrar_info(f"Se creó el trámite '{tramite.nombre}'.\n"
                         f"Se abrirá su plantilla: escriba la referencia y el cuerpo que se repiten, "
                         f"guarde y cierre Word.")
            abrir_con_programa(tramite.obtener_plantilla())
        except StopIteration:
            mostrar_error("No se encontró la plantilla base.")
        except Exception as error:
            mostrar_error(error)

    def abrir(self):
        try:
            abrir_con_programa(self._elegido().obtener_plantilla())
        except Exception as error:
            mostrar_error(error)

    def reemplazar(self):
        try:
            tramite = self._elegido()
            ruta = filedialog.askopenfilename(title="Elegir el nuevo Word",
                                              filetypes=[("Word", "*.docx")])
            if ruta:
                tramite.reemplazar_plantilla(ruta)
                self.cargar()
                mostrar_info(f"Se reemplazó la plantilla de '{tramite.nombre}'.")
        except Exception as error:
            mostrar_error(error)
