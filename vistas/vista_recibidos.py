"""
vista_recibidos.py
Pantalla de documentos recibidos (RF04, RF05, RF17, RF18).
"""

import os
from datetime import date

import customtkinter as ctk

from modelos.recibido import CATEGORIAS, DocumentoRecibido
from utilidades import ahora, fecha_hora_a_iso, iso_a_fecha_hora
from vistas.componentes import (FUENTE, FUENTE_SUBTITULO, Dialogo, Tabla, campo, confirmar, elegir_escaneado,
                                mostrar_error, mostrar_info, poner_texto, titulo)


class VistaRecibidos(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.ruta_escaneado = None
        titulo(self, "Documentos recibidos",
               "La fecha y hora son las del sello de recibido. "
               "Los papeles de docentes y auxiliares van con su categoría.")
        self._armar_formulario()
        self._armar_lista()
        self.buscar()

    def _armar_formulario(self):
        marco = ctk.CTkFrame(self)
        marco.pack(fill="x", padx=24, pady=(4, 8))

        self.nro = campo(marco, 0, 0, "N.º de oficio")
        self.remitente = campo(marco, 0, 2, "Remitente")
        self.fecha_hora = campo(marco, 1, 0, "Sello (dd/mm/aaaa hh:mm)", valor=ahora())
        ctk.CTkLabel(marco, text="Categoría", font=FUENTE).grid(
            row=1, column=2, sticky="w", padx=(12, 6))
        self.categoria = ctk.CTkComboBox(marco, values=CATEGORIAS, width=260, font=FUENTE,
                                         state="readonly")
        self.categoria.set("Otro")
        self.categoria.grid(row=1, column=3, sticky="w", pady=6)
        self.asunto = campo(marco, 2, 0, "Asunto", ancho=660)
        self.asunto.grid(columnspan=3)
        self.requiere = ctk.CTkCheckBox(
            marco, font=FUENTE,
            text="Requiere respuesta (si es solo de conocimiento, no lo marque)")
        self.requiere.select()
        self.requiere.grid(row=3, column=0, columnspan=4, sticky="w", padx=12, pady=(2, 4))

        pie = ctk.CTkFrame(marco, fg_color="transparent")
        pie.grid(row=4, column=0, columnspan=4, sticky="we", padx=12, pady=(4, 10))
        ctk.CTkButton(pie, text="Elegir escaneado...", fg_color="gray50",
                      command=self.elegir).pack(side="left")
        self.etiqueta_archivo = ctk.CTkLabel(pie, text="Sin escaneado", font=FUENTE)
        self.etiqueta_archivo.pack(side="left", padx=10)
        ctk.CTkButton(pie, text="Limpiar", fg_color="gray60", width=90,
                      command=self.limpiar).pack(side="right", padx=4)
        ctk.CTkButton(pie, text="Registrar", command=self.registrar).pack(side="right", padx=4)
        self.etiqueta_numero = ctk.CTkLabel(pie, text="", font=FUENTE_SUBTITULO)
        self.etiqueta_numero.pack(side="right", padx=16)

    def elegir(self):
        ruta = elegir_escaneado()
        if ruta:
            self.ruta_escaneado = ruta
            self.etiqueta_archivo.configure(text=os.path.basename(ruta))

    def limpiar(self):
        for caja in (self.nro, self.remitente, self.asunto):
            poner_texto(caja, "")
        poner_texto(self.fecha_hora, ahora())
        self.categoria.set("Otro")
        self.requiere.select()
        self.ruta_escaneado = None
        self.etiqueta_archivo.configure(text="Sin escaneado")

    def registrar(self):
        try:
            documento = DocumentoRecibido(
                nro_oficio=self.nro.get(),
                fecha_hora_recepcion=fecha_hora_a_iso(self.fecha_hora.get()),
                remitente=self.remitente.get(), asunto=self.asunto.get(),
                requiere_respuesta=bool(self.requiere.get()),
                categoria=self.categoria.get(),
            )
            if documento.posible_repetido() and not confirmar(
                    "Ya hay un documento con ese número y ese remitente en esta gestión.\n"
                    "¿Registrarlo de todas formas?"):
                return
            documento.registrar()
            if self.ruta_escaneado:
                documento.adjuntar_escaneado(self.ruta_escaneado)
            self.limpiar()
            self.buscar()
            mostrar_info(f"Se registró el documento {documento.nro_oficio} "
                         f"con el número interno {documento.registro_corto}.")
        except Exception as error:
            mostrar_error(error)

    def _armar_lista(self):
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=24, pady=(8, 4))
        ctk.CTkLabel(barra, text="Buscar", font=FUENTE).pack(side="left")
        self.texto_busqueda = ctk.CTkEntry(barra, width=300, font=FUENTE,
                                           placeholder_text="número, remitente o asunto")
        self.texto_busqueda.pack(side="left", padx=6)
        self.texto_busqueda.bind("<Return>", lambda _e: self.buscar())
        ctk.CTkLabel(barra, text="Categoría", font=FUENTE).pack(side="left", padx=(10, 0))
        self.categoria_busqueda = ctk.CTkComboBox(
            barra, values=["Todas"] + CATEGORIAS, width=190, font=FUENTE, state="readonly",
            command=lambda _valor: self.buscar())
        self.categoria_busqueda.set("Todas")
        self.categoria_busqueda.pack(side="left", padx=6)
        ctk.CTkButton(barra, text="Buscar", width=80, command=self.buscar).pack(side="left")

        self.tabla = Tabla(self, [("N.º reg.", 75), ("N.º de oficio", 100), ("Categoría", 120),
                                  ("Remitente", 170), ("Asunto", 270), ("Recibido", 125),
                                  ("Responder", 80), ("Estado", 90), ("Escaneado", 80)],
                           alto=10, al_doble_click=self.abrir)
        self.tabla.pack(fill="both", expand=True, padx=24)

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(fill="x", padx=24, pady=10)
        for texto, accion in (("Cambiar estado", self.cambiar_estado),
                              ("Adjuntar escaneado", self.adjuntar),
                              ("Abrir escaneado", self.abrir)):
            ctk.CTkButton(botones, text=texto, command=accion).pack(side="left", padx=4)

    def buscar(self):
        try:
            categoria = self.categoria_busqueda.get()
            categoria = None if categoria == "Todas" else categoria
            self.tabla.cargar([
                (d.id_recibido, (d.registro_corto, d.nro_oficio, d.categoria, d.remitente,
                                 d.asunto, iso_a_fecha_hora(d.fecha_hora_recepcion),
                                 "Sí" if d.requiere_respuesta else "No", d.estado,
                                 "Sí" if d.archivo_escaneado else "No"), d.estado)
                for d in DocumentoRecibido.buscar(self.texto_busqueda.get(), categoria)
            ])
            self._mostrar_proximo_numero()
        except Exception as error:
            mostrar_error(error)

    def _mostrar_proximo_numero(self):
        gestion = date.today().year
        numero = DocumentoRecibido.proximo_nro_registro(gestion)
        self.etiqueta_numero.configure(text=f"Próximo N.º interno: {numero:02d}/{gestion}")

    def _elegido(self):
        identificador = self.tabla.seleccionado()
        if identificador is None:
            raise ValueError("Primero elija un documento de la lista.")
        return DocumentoRecibido.obtener(identificador)

    def cambiar_estado(self):
        try:
            documento = self._elegido()
            datos = Dialogo.preguntar(self, f"Estado del documento {documento.nro_oficio}", [
                {"clave": "estado", "etiqueta": "Estado", "valor": documento.estado,
                 "opciones": ["pendiente", "en curso", "completado"]},
            ])
            if datos:
                documento.cambiar_estado(datos["estado"])
                self.buscar()
        except Exception as error:
            mostrar_error(error)

    def adjuntar(self):
        try:
            documento = self._elegido()
            ruta = elegir_escaneado()
            if ruta:
                documento.adjuntar_escaneado(ruta)
                self.buscar()
        except Exception as error:
            mostrar_error(error)

    def abrir(self):
        try:
            self._elegido().abrir_archivo()
        except Exception as error:
            mostrar_error(error)
