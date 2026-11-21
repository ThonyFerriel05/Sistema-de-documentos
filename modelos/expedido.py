"""
expedido.py
Clase DocumentoExpedido: los oficios que salen de la dirección (RF01, RF02, RF03, RF13, RF15, RF16).
Un oficio puede no requerir respuesta: entonces queda "completado" desde que se registra.
"""

from database import CARPETA_SISTEMA, conectar
from modelos.configuracion import obtener_ultimo_numero_previo
from modelos.documento import CARPETA_ARCHIVOS, Documento
from modelos.tipo_tramite import TipoTramite
from servicios.plantillas import llenar_plantilla
from utilidades import fecha_a_iso, fecha_en_letras, nombre_archivo_seguro, texto_vacio

PREFIJO_CODIGO = "DIR.CARR.ING.SISTEMAS F.IN.I. OF. No."
ESTADOS = ("esperando", "aprobado", "rechazado", "completado")


class DocumentoExpedido(Documento):
    def __init__(self, fecha_envio, destinatario_nombre, destinatario_cargo, asunto,
                 id_tipo, via_nombre=None, via_cargo=None, id_original=None,
                 requiere_respuesta=True, codigo=None, gestion=None, estado="esperando", nro_resolucion=None,
                 fecha_resolucion=None, archivo_escaneado=None, id_expedido=None):
        super().__init__(asunto, archivo_escaneado)
        self.id_expedido = id_expedido
        self.fecha_envio = fecha_envio            # formato de la base: 2026-09-21
        self.destinatario_nombre = destinatario_nombre
        self.destinatario_cargo = destinatario_cargo
        self.via_nombre = via_nombre or None
        self.via_cargo = via_cargo or None
        self.id_tipo = id_tipo
        self.id_original = id_original
        self.requiere_respuesta = bool(requiere_respuesta)
        self.codigo = codigo
        self.gestion = gestion
        self.estado = estado
        self.nro_resolucion = nro_resolucion
        self.fecha_resolucion = fecha_resolucion

    # ---------- cómo se ve el código ----------

    @property
    def numero_corto(self):
        """112/2026 (dos cifras como mínimo: 01/2027)."""
        return f"{self.codigo:02d}/{self.gestion}"

    @property
    def codigo_completo(self):
        return f"{PREFIJO_CODIGO} {self.numero_corto}"

    # ---------- métodos del diagrama ----------

    @staticmethod
    def generar_codigo(gestion, conexion):
        """
        Siguiente número de la gestión. Toma el mayor entre:
        - el último oficio guardado en el sistema, y
        - el último número que la directora indicó que usó en papel (RF16).
        En una gestión nueva los dos son 0, así que empieza en 1.
        """
        mayor = conexion.execute(
            "SELECT COALESCE(MAX(codigo), 0) AS mayor FROM documento_expedido WHERE gestion = ?",
            (gestion,),
        ).fetchone()["mayor"]
        previo = obtener_ultimo_numero_previo(gestion, conexion)
        return max(mayor, previo) + 1

    @classmethod
    def proximo_numero(cls, gestion):
        """Para mostrar en pantalla qué número le va a tocar al próximo oficio."""
        with conectar() as conexion:
            return cls.generar_codigo(gestion, conexion)

    def registrar(self):
        self._validar()
        self.gestion = int(self.fecha_envio[:4])
        # Si no se espera respuesta, el trámite termina al enviarlo.
        self.estado = "esperando" if self.requiere_respuesta else "completado"
        with conectar() as conexion:
            # BEGIN IMMEDIATE: nadie más escribe mientras se calcula el número.
            conexion.execute("BEGIN IMMEDIATE")
            self.codigo = self.generar_codigo(self.gestion, conexion)
            cursor = conexion.execute(
                """INSERT INTO documento_expedido
                   (codigo, gestion, fecha_envio, destinatario_nombre, destinatario_cargo,
                    via_nombre, via_cargo, asunto, id_tipo, archivo_escaneado,
                    requiere_respuesta, estado, id_original)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.codigo, self.gestion, self.fecha_envio, self.destinatario_nombre.strip(),
                 self.destinatario_cargo.strip(), self.via_nombre, self.via_cargo,
                 self.asunto.strip(), self.id_tipo, self.archivo_escaneado,
                 int(self.requiere_respuesta), self.estado, self.id_original),
            )
            self.id_expedido = cursor.lastrowid
        return self

    def generar_con_plantilla(self):
        """Crea el Word del oficio con los datos ya puestos y devuelve su ruta."""
        tramite = TipoTramite.obtener(self.id_tipo)
        datos = {
            "{{FECHA}}": fecha_en_letras(self.fecha_envio),
            "{{CODIGO}}": self.codigo_completo,
            "{{DESTINATARIO_NOMBRE}}": self.destinatario_nombre,
            "{{DESTINATARIO_CARGO}}": self.destinatario_cargo,
            "{{VIA_NOMBRE}}": self.via_nombre or "",
            "{{VIA_CARGO}}": self.via_cargo or "",
            "{{ASUNTO}}": self.asunto,
            "{{GESTION}}": str(self.gestion),
        }
        # Mismo estilo de nombre que usa la directora: "Oficio No 112 ..."
        nombre = nombre_archivo_seguro(f"Oficio No {self.codigo:02d} {self.asunto}")
        salida = CARPETA_ARCHIVOS / "oficios_generados" / str(self.gestion) / f"{nombre}.docx"
        return llenar_plantilla(tramite.obtener_plantilla(), datos, salida)

    def registrar_respuesta(self, estado, nro_resolucion=None, fecha_resolucion=None):
        """RF02: aprobado, rechazado o completado, con su resolución si la hay."""
        if estado not in ESTADOS:
            raise ValueError("Estado no válido.")
        fecha_iso = fecha_a_iso(fecha_resolucion) if not texto_vacio(fecha_resolucion) else None
        with conectar() as conexion:
            conexion.execute(
                """UPDATE documento_expedido
                   SET estado = ?, nro_resolucion = ?, fecha_resolucion = ?
                   WHERE id_expedido = ?""",
                (estado, nro_resolucion or None, fecha_iso, self.id_expedido),
            )
        self.estado, self.nro_resolucion, self.fecha_resolucion = estado, nro_resolucion, fecha_iso

    def adjuntar_escaneado(self, ruta_origen):
        """RF15: el escaneado del oficio firmado se adjunta después."""
        nombre = f"Oficio No {self.codigo:02d} de {self.gestion}"
        self.archivo_escaneado = self.copiar_escaneado(
            ruta_origen, f"expedidos/{self.gestion}", nombre
        )
        with conectar() as conexion:
            conexion.execute(
                "UPDATE documento_expedido SET archivo_escaneado = ? WHERE id_expedido = ?",
                (self.archivo_escaneado, self.id_expedido),
            )

    def preparar_reenvio(self):
        """
        RF03: copia los datos de un oficio rechazado para enviar uno nuevo.
        El nuevo tendrá su propio número y quedará enlazado a este.
        """
        if self.estado != "rechazado":
            raise ValueError("Solo se puede reenviar un oficio rechazado.")
        return DocumentoExpedido(
            fecha_envio=None, destinatario_nombre=self.destinatario_nombre,
            destinatario_cargo=self.destinatario_cargo, asunto=self.asunto,
            id_tipo=self.id_tipo, via_nombre=self.via_nombre, via_cargo=self.via_cargo,
            id_original=self.id_expedido, requiere_respuesta=self.requiere_respuesta,
        )

    # ---------- validación ----------

    def _validar(self):
        obligatorios = {
            "fecha de envío": self.fecha_envio,
            "nombre del destinatario": self.destinatario_nombre,
            "cargo del destinatario": self.destinatario_cargo,
            "referencia (asunto)": self.asunto,
            "trámite": self.id_tipo,
        }
        faltan = [campo for campo, valor in obligatorios.items() if texto_vacio(valor)]
        if faltan:
            raise ValueError("Falta completar: " + ", ".join(faltan) + ".")
        if bool(self.via_nombre) != bool(self.via_cargo):
            raise ValueError("Si hay VIA, complete el nombre y el cargo.")

    # ---------- consultas ----------

    @classmethod
    def _desde_fila(cls, f):
        return cls(
            fecha_envio=f["fecha_envio"], destinatario_nombre=f["destinatario_nombre"],
            destinatario_cargo=f["destinatario_cargo"], asunto=f["asunto"], id_tipo=f["id_tipo"],
            via_nombre=f["via_nombre"], via_cargo=f["via_cargo"], id_original=f["id_original"],
            requiere_respuesta=f["requiere_respuesta"], codigo=f["codigo"], gestion=f["gestion"], estado=f["estado"],
            nro_resolucion=f["nro_resolucion"], fecha_resolucion=f["fecha_resolucion"],
            archivo_escaneado=f["archivo_escaneado"], id_expedido=f["id_expedido"],
        )

    @classmethod
    def obtener(cls, id_expedido):
        with conectar() as conexion:
            fila = conexion.execute(
                "SELECT * FROM documento_expedido WHERE id_expedido = ?", (id_expedido,)
            ).fetchone()
        if not fila:
            raise ValueError("No se encontró el oficio.")
        return cls._desde_fila(fila)

    @classmethod
    def buscar(cls, texto="", gestion=None):
        """RF09: busca por número, referencia, destinatario o vía."""
        consulta = "SELECT * FROM documento_expedido WHERE 1 = 1"
        parametros = []
        if gestion:
            consulta += " AND gestion = ?"
            parametros.append(int(gestion))
        texto = (texto or "").strip()
        if texto:
            numero = texto.split("/")[0]
            consulta += """ AND (asunto LIKE ? OR destinatario_nombre LIKE ?
                           OR destinatario_cargo LIKE ? OR via_nombre LIKE ?
                           OR CAST(codigo AS TEXT) = ?)"""
            like = f"%{texto}%"
            parametros += [like, like, like, like, numero.lstrip("0") or "0"]
        consulta += " ORDER BY gestion DESC, codigo DESC"
        with conectar() as conexion:
            return [cls._desde_fila(f) for f in conexion.execute(consulta, parametros)]

    @classmethod
    def pendientes(cls):
        """RF10: oficios que requieren respuesta y siguen esperándola."""
        with conectar() as conexion:
            filas = conexion.execute(
                """SELECT * FROM documento_expedido
                   WHERE requiere_respuesta = 1 AND estado = 'esperando'
                   ORDER BY fecha_envio"""
            ).fetchall()
        return [cls._desde_fila(f) for f in filas]

    @classmethod
    def sin_escaneado(cls):
        with conectar() as conexion:
            filas = conexion.execute(
                """SELECT * FROM documento_expedido WHERE archivo_escaneado IS NULL
                   ORDER BY fecha_envio"""
            ).fetchall()
        return [cls._desde_fila(f) for f in filas]

    @classmethod
    def ruta_completa(cls, ruta_relativa):
        return CARPETA_SISTEMA / ruta_relativa
