"""
vista_configuracion.py
Número inicial de la gestión (RF16) y copia de seguridad (RF12).
"""

from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk

from modelos.configuracion import definir_ultimo_numero_previo, obtener_ultimo_numero_previo
from modelos.expedido import DocumentoExpedido
from servicios.respaldo import CARPETA_RESPALDOS, crear_respaldo
from utilidades import abrir_con_programa
from vistas.componentes import FUENTE, FUENTE_SUBTITULO, mostrar_error, mostrar_info, titulo


class VistaConfiguracion(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.gestion = datetime.now().year
        titulo(self, "Configuración y respaldo")

        # ----- número inicial -----
        marco = ctk.CTkFrame(self)
        marco.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(marco, text=f"Numeración de oficios — gestión {self.gestion}",
                     font=FUENTE_SUBTITULO).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            marco, font=FUENTE, justify="left", text_color="gray30",
            text="Si empieza a usar el sistema a mitad de año, escriba el último número de oficio\n"
                 "que ya se usó en papel. Por ejemplo: 130 hace que el próximo sea 131.",
        ).pack(anchor="w", padx=16)
        fila = ctk.CTkFrame(marco, fg_color="transparent")
        fila.pack(anchor="w", padx=16, pady=12)
        ctk.CTkLabel(fila, text="Último número usado:", font=FUENTE).pack(side="left")
        self.ultimo = ctk.CTkEntry(fila, width=90, font=FUENTE)
        self.ultimo.insert(0, str(obtener_ultimo_numero_previo(self.gestion)))
        self.ultimo.pack(side="left", padx=8)
        ctk.CTkButton(fila, text="Guardar", width=90, command=self.guardar_numero).pack(side="left")
        self.etiqueta_proximo = ctk.CTkLabel(fila, text="", font=FUENTE_SUBTITULO)
        self.etiqueta_proximo.pack(side="left", padx=16)
        self._mostrar_proximo()

        # ----- respaldo -----
        marco2 = ctk.CTkFrame(self)
        marco2.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(marco2, text="Copia de seguridad", font=FUENTE_SUBTITULO).pack(
            anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            marco2, font=FUENTE, justify="left", text_color="gray30",
            text="Guarda en un solo archivo .zip la base de datos, los escaneados y las plantillas.\n"
                 "Se recomienda guardar una copia en una memoria USB al menos una vez por semana.",
        ).pack(anchor="w", padx=16)
        botones = ctk.CTkFrame(marco2, fg_color="transparent")
        botones.pack(anchor="w", padx=16, pady=12)
        ctk.CTkButton(botones, text="Crear copia de seguridad",
                      command=self.respaldar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(botones, text="Guardar copia en otra carpeta (USB)...",
                      command=self.respaldar_en).pack(side="left", padx=6)
        ctk.CTkButton(botones, text="Abrir carpeta de respaldos", fg_color="gray50",
                      command=self.abrir_respaldos).pack(side="left", padx=6)

    def _mostrar_proximo(self):
        numero = DocumentoExpedido.proximo_numero(self.gestion)
        self.etiqueta_proximo.configure(text=f"Próximo oficio: {numero:02d}/{self.gestion}")

    def guardar_numero(self):
        try:
            definir_ultimo_numero_previo(self.gestion, self.ultimo.get().strip() or 0)
            self._mostrar_proximo()
            mostrar_info("Numeración guardada.")
        except ValueError as error:
            mostrar_error(error if "invalid literal" not in str(error) else "Escriba un número entero.")

    def respaldar(self):
        try:
            mostrar_info(f"Copia creada:\n{crear_respaldo()}")
        except Exception as error:
            mostrar_error(error)

    def respaldar_en(self):
        try:
            carpeta = filedialog.askdirectory(title="Elegir carpeta o memoria USB")
            if carpeta:
                mostrar_info(f"Copia creada:\n{crear_respaldo(carpeta)}")
        except Exception as error:
            mostrar_error(error)

    def abrir_respaldos(self):
        try:
            CARPETA_RESPALDOS.mkdir(parents=True, exist_ok=True)
            abrir_con_programa(CARPETA_RESPALDOS)
        except Exception as error:
            mostrar_error(error)
