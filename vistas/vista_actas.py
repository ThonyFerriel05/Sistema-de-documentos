"""
vista_actas.py
Pantalla de actas de graduación (RF06, RF07, RF08, RF18, RF19).
"""

import os

import customtkinter as ctk

from modelos.acta import MODALIDADES, Acta
from vistas.componentes import (FUENTE, Tabla, campo, elegir_escaneado, mostrar_error,
                                mostrar_info, poner_texto, titulo)


class VistaActas(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.ruta_escaneado = None
        titulo(self, "Actas de graduación",
               "El número y el código del acta los asigna el CPD. "
               "Se busca por carnet y se filtra por modalidad.")
        self._armar_formulario()
        self._armar_lista()
        self.buscar()

    def _armar_formulario(self):
        marco = ctk.CTkFrame(self)
        marco.pack(fill="x", padx=24, pady=(4, 8))

        self.nro = campo(marco, 0, 0, "N.º de acta")
        self.codigo = campo(marco, 0, 2, "Código (CPD)")
        self.carnet = campo(marco, 1, 0, "Carnet")
        self.nota = campo(marco, 1, 2, "Nota (0 a 100)", ancho=80)
        ctk.CTkLabel(marco, text="Modalidad", font=FUENTE).grid(row=2, column=0, sticky="w", padx=(12, 6))
        self.modalidad = ctk.CTkComboBox(marco, values=MODALIDADES, width=360, font=FUENTE,
                                         state="readonly")
        self.modalidad.set(MODALIDADES[0])
        self.modalidad.grid(row=2, column=1, columnspan=3, sticky="w", pady=6)

        pie = ctk.CTkFrame(marco, fg_color="transparent")
        pie.grid(row=3, column=0, columnspan=4, sticky="we", padx=12, pady=(4, 10))
        ctk.CTkButton(pie, text="Elegir escaneado...", fg_color="gray50",
                      command=self.elegir).pack(side="left")
        self.etiqueta_archivo = ctk.CTkLabel(pie, text="Sin escaneado", font=FUENTE)
        self.etiqueta_archivo.pack(side="left", padx=10)
        ctk.CTkButton(pie, text="Limpiar", fg_color="gray60", width=90,
                      command=self.limpiar).pack(side="right", padx=4)
        ctk.CTkButton(pie, text="Registrar acta", command=self.registrar).pack(side="right", padx=4)

    def elegir(self):
        ruta = elegir_escaneado()
        if ruta:
            self.ruta_escaneado = ruta
            self.etiqueta_archivo.configure(text=os.path.basename(ruta))

    def limpiar(self):
        for caja in (self.nro, self.codigo, self.carnet, self.nota):
            poner_texto(caja, "")
        self.modalidad.set(MODALIDADES[0])
        self.ruta_escaneado = None
        self.etiqueta_archivo.configure(text="Sin escaneado")

    def registrar(self):
        try:
            acta = Acta(self.nro.get(), self.codigo.get(), self.carnet.get(),
                        self.nota.get(), self.modalidad.get())
            acta.registrar()  # verifica que no se repita (RF07)
            if self.ruta_escaneado:
                acta.adjuntar_escaneado(self.ruta_escaneado)
            self.limpiar()
            self.buscar()
            mostrar_info(f"Se registró el acta N.º {acta.nro_acta} "
                         f"(registro interno {acta.registro_corto}).")
        except Exception as error:
            mostrar_error(error)

    def _armar_lista(self):
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=24, pady=(8, 4))
        ctk.CTkLabel(barra, text="Buscar por carnet", font=FUENTE).pack(side="left")
        self.carnet_busqueda = ctk.CTkEntry(barra, width=220, font=FUENTE)
        self.carnet_busqueda.pack(side="left", padx=6)
        self.carnet_busqueda.bind("<Return>", lambda _e: self.buscar())
        ctk.CTkLabel(barra, text="Modalidad", font=FUENTE).pack(side="left", padx=(10, 0))
        self.modalidad_busqueda = ctk.CTkComboBox(
            barra, values=["Todas"] + MODALIDADES, width=300, font=FUENTE, state="readonly",
            command=lambda _valor: self.buscar())
        self.modalidad_busqueda.set("Todas")
        self.modalidad_busqueda.pack(side="left", padx=6)
        ctk.CTkButton(barra, text="Buscar", width=80, command=self.buscar).pack(side="left")
        self.etiqueta_resultado = ctk.CTkLabel(barra, text="", font=FUENTE)
        self.etiqueta_resultado.pack(side="left", padx=12)

        self.tabla = Tabla(self, [("N.º reg.", 75), ("N.º de acta", 95), ("Código", 150),
                                  ("Carnet", 130), ("Nota", 55), ("Modalidad", 290),
                                  ("Escaneado", 85)],
                           alto=10, al_doble_click=self.abrir)
        self.tabla.pack(fill="both", expand=True, padx=24)

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(fill="x", padx=24, pady=10)
        ctk.CTkButton(botones, text="Adjuntar escaneado", command=self.adjuntar).pack(side="left", padx=4)
        ctk.CTkButton(botones, text="Abrir escaneado", command=self.abrir).pack(side="left", padx=4)

    def buscar(self):
        """Secuencia 'buscar acta por carnet': pantalla -> Acta -> base de datos."""
        try:
            carnet = self.carnet_busqueda.get().strip()
            modalidad = self.modalidad_busqueda.get()
            modalidad = None if modalidad == "Todas" else modalidad
            actas = Acta.buscar(carnet, modalidad)
            self.tabla.cargar([
                (a.id_acta, (a.registro_corto, a.nro_acta, a.codigo, a.carnet, a.nota, a.modalidad,
                             "Sí" if a.archivo_escaneado else "No"))
                for a in actas
            ])
            if (carnet or modalidad) and not actas:
                self.etiqueta_resultado.configure(
                    text="No se encontró ninguna acta con esos datos.", text_color="#b00020")
            else:
                self.etiqueta_resultado.configure(text=f"{len(actas)} acta(s)",
                                                  text_color="gray40")
        except Exception as error:
            mostrar_error(error)

    def _elegida(self):
        identificador = self.tabla.seleccionado()
        if identificador is None:
            raise ValueError("Primero elija un acta de la lista.")
        return Acta.obtener(identificador)

    def adjuntar(self):
        try:
            acta = self._elegida()
            ruta = elegir_escaneado()
            if ruta:
                acta.adjuntar_escaneado(ruta)
                self.buscar()
        except Exception as error:
            mostrar_error(error)

    def abrir(self):
        try:
            self._elegida().abrir_archivo()
        except Exception as error:
            mostrar_error(error)
