"""
vista_pendientes.py
Pantalla de inicio: lo que falta responder (RF10).
"""

from datetime import datetime

import customtkinter as ctk

from modelos.expedido import DocumentoExpedido
from modelos.recibido import DocumentoRecibido
from utilidades import iso_a_fecha, iso_a_fecha_hora
from vistas.componentes import FUENTE, FUENTE_SUBTITULO, Tabla, titulo


def dias_desde(fecha_iso):
    return (datetime.now() - datetime.strptime(fecha_iso[:10], "%Y-%m-%d")).days


class VistaPendientes(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        titulo(self, "Pendientes", "Lo que todavía espera una respuesta.")

        recibidos = DocumentoRecibido.pendientes()
        expedidos = DocumentoExpedido.pendientes()
        sin_escaneado = DocumentoExpedido.sin_escaneado()

        # Recibidos por responder
        ctk.CTkLabel(self, text=f"Documentos recibidos por responder ({len(recibidos)})",
                     font=FUENTE_SUBTITULO).pack(anchor="w", padx=24, pady=(8, 4))
        tabla_recibidos = Tabla(self, [("N.º de oficio", 120), ("Remitente", 220),
                                       ("Asunto", 380), ("Recibido", 140),
                                       ("Estado", 100), ("Días", 60)], alto=7)
        tabla_recibidos.pack(fill="x", padx=24)
        tabla_recibidos.cargar([
            (r.id_recibido, (r.nro_oficio, r.remitente, r.asunto,
                             iso_a_fecha_hora(r.fecha_hora_recepcion), r.estado,
                             dias_desde(r.fecha_hora_recepcion)), r.estado)
            for r in recibidos
        ])

        # Expedidos sin respuesta
        ctk.CTkLabel(self, text=f"Oficios enviados esperando respuesta ({len(expedidos)})",
                     font=FUENTE_SUBTITULO).pack(anchor="w", padx=24, pady=(18, 4))
        tabla_expedidos = Tabla(self, [("N.º", 90), ("Destinatario", 250), ("Referencia", 400),
                                       ("Enviado", 110), ("Días", 60)], alto=7)
        tabla_expedidos.pack(fill="x", padx=24)
        tabla_expedidos.cargar([
            (e.id_expedido, (e.numero_corto, e.destinatario_nombre, e.asunto,
                             iso_a_fecha(e.fecha_envio), dias_desde(e.fecha_envio)), e.estado)
            for e in expedidos
        ])

        if sin_escaneado:
            ctk.CTkLabel(
                self, font=FUENTE, text_color="#a35b00",
                text=f"Hay {len(sin_escaneado)} oficio(s) enviados sin el escaneado firmado. "
                     f"Adjúntelos en 'Oficios expedidos'.",
            ).pack(anchor="w", padx=24, pady=(14, 0))
