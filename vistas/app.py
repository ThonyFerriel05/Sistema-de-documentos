"""
app.py
Ventana principal: menú a la izquierda y la pantalla elegida a la derecha.
"""

import customtkinter as ctk

from vistas.componentes import configurar_estilo_tablas
from vistas.vista_actas import VistaActas
from vistas.vista_configuracion import VistaConfiguracion
from vistas.vista_expedidos import VistaExpedidos
from vistas.vista_pendientes import VistaPendientes
from vistas.vista_recibidos import VistaRecibidos
from vistas.vista_tramites import VistaTramites

MENU = [
    ("Pendientes", VistaPendientes),
    ("Oficios expedidos", VistaExpedidos),
    ("Documentos recibidos", VistaRecibidos),
    ("Actas de graduación", VistaActas),
    ("Trámites y plantillas", VistaTramites),
    ("Configuración y respaldo", VistaConfiguracion),
]


class Aplicacion(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        configurar_estilo_tablas()

        self.title("Dirección de Carrera de Ingeniería en Sistemas — Control de documentación")
        self.geometry("1280x780")
        self.minsize(1100, 680)

        menu = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color="#1f3b5c")
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)
        ctk.CTkLabel(menu, text="Dirección de\nCarrera", font=("Segoe UI", 20, "bold"),
                     text_color="white", justify="left").pack(anchor="w", padx=20, pady=(28, 4))
        ctk.CTkLabel(menu, text="Ing. en Sistemas — F.IN.I.", font=("Segoe UI", 12),
                     text_color="#c9d6e6").pack(anchor="w", padx=20, pady=(0, 24))

        self.botones = {}
        for nombre, _vista in MENU:
            boton = ctk.CTkButton(menu, text=nombre, anchor="w", height=40, corner_radius=6,
                                  font=("Segoe UI", 14), fg_color="transparent",
                                  hover_color="#2d527d", text_color="white",
                                  command=lambda n=nombre: self.mostrar(n))
            boton.pack(fill="x", padx=12, pady=3)
            self.botones[nombre] = boton

        ctk.CTkLabel(menu, text="Versión beta", font=("Segoe UI", 11),
                     text_color="#c9d6e6").pack(side="bottom", pady=16)

        self.contenedor = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="#f4f6f9")
        self.contenedor.pack(side="left", fill="both", expand=True)
        self.vista_actual = None
        self.mostrar("Pendientes")

    def mostrar(self, nombre):
        """Cada vez que se entra a una pantalla se vuelve a crear, así los datos están al día."""
        if self.vista_actual is not None:
            self.vista_actual.destroy()
        clase = dict(MENU)[nombre]
        self.vista_actual = clase(self.contenedor, self)
        self.vista_actual.pack(fill="both", expand=True)
        for clave, boton in self.botones.items():
            boton.configure(fg_color="#2f6fb5" if clave == nombre else "transparent")
