"""
vista_expedidos.py
Pantalla de oficios expedidos: registrar, generar el Word, respuesta, escaneado y reenvío.
"""

import customtkinter as ctk

from modelos.expedido import DocumentoExpedido
from modelos.tipo_tramite import TipoTramite
from utilidades import abrir_con_programa, fecha_a_iso, hoy, iso_a_fecha
from vistas.componentes import (FUENTE, FUENTE_SUBTITULO, Dialogo, Tabla, campo, confirmar,
                                elegir_escaneado, mostrar_error, mostrar_info, poner_texto,
                                titulo)


class VistaExpedidos(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.id_original = None  # se usa cuando es el reenvío de un rechazado
        self.tramites = {t.nombre: t for t in TipoTramite.listar()}

        titulo(self, "Oficios expedidos",
               "El número se asigna solo y el Word se genera con la plantilla del trámite.")
        self._armar_formulario()
        self._armar_lista()
        self.actualizar_proximo_numero()
        self.buscar()

    # ---------- formulario ----------

    def _armar_formulario(self):
        marco = ctk.CTkFrame(self)
        marco.pack(fill="x", padx=24, pady=(4, 8))

        self.fecha = campo(marco, 0, 0, "Fecha de envío", valor=hoy())
        self.fecha.bind("<KeyRelease>", lambda _e: self.actualizar_proximo_numero())
        ctk.CTkLabel(marco, text="Trámite", font=FUENTE).grid(row=0, column=2, sticky="w", padx=(12, 6))
        self.tramite = ctk.CTkComboBox(marco, values=list(self.tramites), width=260,
                                       font=FUENTE, state="readonly")
        if self.tramites:
            self.tramite.set(next(iter(self.tramites)))
        self.tramite.grid(row=0, column=3, sticky="w", pady=6)

        self.a_nombre = campo(marco, 1, 0, "A (nombre)")
        self.a_cargo = campo(marco, 1, 2, "Cargo")
        self.via_nombre = campo(marco, 2, 0, "VIA (opcional)")
        self.via_cargo = campo(marco, 2, 2, "Cargo VIA")
        self.asunto = campo(marco, 3, 0, "Referencia", ancho=660)
        self.asunto.grid(columnspan=3)
        self.requiere = ctk.CTkCheckBox(
            marco, font=FUENTE,
            text="Requiere respuesta (si no se marca, queda completado al enviarlo)")
        self.requiere.select()
        self.requiere.grid(row=4, column=0, columnspan=4, sticky="w", padx=12, pady=(2, 4))

        pie = ctk.CTkFrame(marco, fg_color="transparent")
        pie.grid(row=5, column=0, columnspan=4, sticky="we", padx=12, pady=(4, 10))
        self.etiqueta_numero = ctk.CTkLabel(pie, text="", font=FUENTE_SUBTITULO)
        self.etiqueta_numero.pack(side="left")
        self.etiqueta_reenvio = ctk.CTkLabel(pie, text="", font=FUENTE, text_color="#a35b00")
        self.etiqueta_reenvio.pack(side="left", padx=16)
        ctk.CTkButton(pie, text="Limpiar", fg_color="gray60", width=90,
                      command=self.limpiar).pack(side="right", padx=4)
        ctk.CTkButton(pie, text="Registrar y generar Word",
                      command=self.registrar).pack(side="right", padx=4)

    def actualizar_proximo_numero(self):
        try:
            gestion = int(fecha_a_iso(self.fecha.get())[:4])
            numero = DocumentoExpedido.proximo_numero(gestion)
            self.etiqueta_numero.configure(text=f"Próximo número: {numero:02d}/{gestion}")
        except ValueError:
            self.etiqueta_numero.configure(text="Próximo número: (revise la fecha)")

    def limpiar(self):
        for caja in (self.a_nombre, self.a_cargo, self.via_nombre, self.via_cargo, self.asunto):
            poner_texto(caja, "")
        poner_texto(self.fecha, hoy())
        self.requiere.select()
        self.id_original = None
        self.etiqueta_reenvio.configure(text="")
        self.actualizar_proximo_numero()

    def registrar(self):
        try:
            tramite = self.tramites.get(self.tramite.get())
            if not tramite:
                raise ValueError("Elija un trámite. Si no hay ninguno, créelo en 'Trámites y plantillas'.")
            oficio = DocumentoExpedido(
                fecha_envio=fecha_a_iso(self.fecha.get()),
                destinatario_nombre=self.a_nombre.get(), destinatario_cargo=self.a_cargo.get(),
                via_nombre=self.via_nombre.get().strip(), via_cargo=self.via_cargo.get().strip(),
                asunto=self.asunto.get(), id_tipo=tramite.id_tipo, id_original=self.id_original,
                requiere_respuesta=bool(self.requiere.get()),
            )
            if not confirmar(f"Se registrará el oficio con el número "
                             f"{self.etiqueta_numero.cget('text').split(': ')[-1]}.\n¿Continuar?"):
                return
            oficio.registrar()
            ruta = oficio.generar_con_plantilla()
            self.limpiar()
            self.buscar()
            mostrar_info(f"Se registró el oficio {oficio.numero_corto}.\n"
                         f"Se abrirá el Word para que complete el contenido.")
            abrir_con_programa(ruta)
        except Exception as error:
            mostrar_error(error)

    # ---------- lista ----------

    def _armar_lista(self):
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=24, pady=(8, 4))
        ctk.CTkLabel(barra, text="Buscar", font=FUENTE).pack(side="left")
        self.texto_busqueda = ctk.CTkEntry(barra, width=260, font=FUENTE,
                                           placeholder_text="número, referencia o destinatario")
        self.texto_busqueda.pack(side="left", padx=6)
        self.texto_busqueda.bind("<Return>", lambda _e: self.buscar())
        ctk.CTkLabel(barra, text="Gestión", font=FUENTE).pack(side="left", padx=(10, 0))
        self.gestion_busqueda = ctk.CTkEntry(barra, width=70, font=FUENTE)
        self.gestion_busqueda.pack(side="left", padx=6)
        self.gestion_busqueda.bind("<Return>", lambda _e: self.buscar())
        ctk.CTkButton(barra, text="Buscar", width=80, command=self.buscar).pack(side="left")

        self.tabla = Tabla(self, [("N.º", 80), ("Fecha", 95), ("Destinatario", 220),
                                  ("Referencia", 330), ("Estado", 95), ("Escaneado", 85),
                                  ("Reenvío de", 90)], alto=9, al_doble_click=self.abrir_escaneado)
        self.tabla.pack(fill="both", expand=True, padx=24)

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(fill="x", padx=24, pady=10)
        for texto, accion in (("Registrar respuesta", self.registrar_respuesta),
                              ("Adjuntar escaneado", self.adjuntar),
                              ("Abrir escaneado", self.abrir_escaneado),
                              ("Volver a generar Word", self.regenerar_word),
                              ("Reenviar rechazado", self.reenviar)):
            ctk.CTkButton(botones, text=texto, command=accion).pack(side="left", padx=4)

    def buscar(self):
        try:
            gestion = self.gestion_busqueda.get().strip() or None
            oficios = DocumentoExpedido.buscar(self.texto_busqueda.get(), gestion)
            numeros = {o.id_expedido: o.numero_corto for o in DocumentoExpedido.buscar()}
            self.tabla.cargar([
                (o.id_expedido, (o.numero_corto, iso_a_fecha(o.fecha_envio), o.destinatario_nombre,
                                 o.asunto, o.estado, "Sí" if o.archivo_escaneado else "No",
                                 numeros.get(o.id_original, "")), o.estado)
                for o in oficios
            ])
        except Exception as error:
            mostrar_error(error)

    def _oficio_elegido(self):
        identificador = self.tabla.seleccionado()
        if identificador is None:
            raise ValueError("Primero elija un oficio de la lista.")
        return DocumentoExpedido.obtener(identificador)

    def registrar_respuesta(self):
        try:
            oficio = self._oficio_elegido()
            datos = Dialogo.preguntar(self, f"Respuesta al oficio {oficio.numero_corto}", [
                {"clave": "estado", "etiqueta": "Estado", "valor": oficio.estado,
                 "opciones": ["esperando", "aprobado", "rechazado", "completado"]},
                {"clave": "nro", "etiqueta": "N.º de resolución", "valor": oficio.nro_resolucion},
                {"clave": "fecha", "etiqueta": "Fecha (dd/mm/aaaa)",
                 "valor": iso_a_fecha(oficio.fecha_resolucion) or hoy()},
            ])
            if datos:
                oficio.registrar_respuesta(datos["estado"], datos["nro"], datos["fecha"])
                self.buscar()
        except Exception as error:
            mostrar_error(error)

    def adjuntar(self):
        try:
            oficio = self._oficio_elegido()
            ruta = elegir_escaneado()
            if ruta:
                oficio.adjuntar_escaneado(ruta)
                self.buscar()
                mostrar_info(f"Escaneado guardado en el oficio {oficio.numero_corto}.")
        except Exception as error:
            mostrar_error(error)

    def abrir_escaneado(self):
        try:
            self._oficio_elegido().abrir_archivo()
        except Exception as error:
            mostrar_error(error)

    def regenerar_word(self):
        try:
            abrir_con_programa(self._oficio_elegido().generar_con_plantilla())
        except Exception as error:
            mostrar_error(error)

    def reenviar(self):
        """RF03: llena el formulario con los datos del rechazado."""
        try:
            original = self._oficio_elegido()
            nuevo = original.preparar_reenvio()
            poner_texto(self.a_nombre, nuevo.destinatario_nombre)
            poner_texto(self.a_cargo, nuevo.destinatario_cargo)
            poner_texto(self.via_nombre, nuevo.via_nombre)
            poner_texto(self.via_cargo, nuevo.via_cargo)
            poner_texto(self.asunto, nuevo.asunto)
            poner_texto(self.fecha, hoy())
            self.requiere.select() if nuevo.requiere_respuesta else self.requiere.deselect()
            for nombre, tramite in self.tramites.items():
                if tramite.id_tipo == nuevo.id_tipo:
                    self.tramite.set(nombre)
            self.id_original = original.id_expedido
            self.etiqueta_reenvio.configure(
                text=f"Reenvío del oficio rechazado {original.numero_corto}")
            self.actualizar_proximo_numero()
        except Exception as error:
            mostrar_error(error)
