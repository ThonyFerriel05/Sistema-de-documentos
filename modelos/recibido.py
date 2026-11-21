"""
recibido.py
Clase DocumentoRecibido: los documentos que llegan a la dirección (RF04, RF05, RF17, RF18).
Los papeles de docentes y auxiliares también son recibidos: se distinguen por la categoría.
"""

from database import conectar
from modelos.documento import Documento
from utilidades import texto_vacio

ESTADOS = ("pendiente", "en curso", "completado")

# Lista fija (RF17). POR CONFIRMAR con la directora.
CATEGORIAS = [
    "Docente",
    "Auxiliatura",
    "Invitación",
    "Solicitud de informe",
    "Resolución",
    "Otro",
]


class DocumentoRecibido(Documento):
    def __init__(self, nro_oficio, fecha_hora_recepcion, remitente, asunto,
                 requiere_respuesta, estado="pendiente", archivo_escaneado=None,
                 id_recibido=None, categoria="Otro", nro_registro=None):
        super().__init__(asunto, archivo_escaneado)
        self.id_recibido = id_recibido
        self.nro_oficio = nro_oficio
        # Fecha y hora del sello de recibido, no la del registro: 2026-09-10 13:05
        self.fecha_hora_recepcion = fecha_hora_recepcion
        self.remitente = remitente
        self.requiere_respuesta = bool(requiere_respuesta)
        self.estado = estado
        self.categoria = categoria
        # Número interno de la dirección (RF18). Lo pone el sistema al registrar.
        self.nro_registro = nro_registro

    @property
    def gestion(self):
        return int(self.fecha_hora_recepcion[:4])

    @property
    def registro_corto(self):
        """05/2026: el quinto documento que llegó en la gestión 2026."""
        if self.nro_registro is None:
            return ""
        return f"{self.nro_registro:02d}/{self.gestion}"

    # ---------- métodos del diagrama ----------

    @staticmethod
    def generar_nro_registro(gestion, conexion):
        """RF18: siguiente número interno de la gestión (vuelve a 1 cada año)."""
        mayor = conexion.execute(
            "SELECT COALESCE(MAX(nro_registro), 0) AS mayor FROM documento_recibido "
            "WHERE gestion = ?", (gestion,),
        ).fetchone()["mayor"]
        return mayor + 1

    @classmethod
    def proximo_nro_registro(cls, gestion):
        """Para mostrar en pantalla qué número interno le tocará al próximo."""
        with conectar() as conexion:
            return cls.generar_nro_registro(gestion, conexion)

    def registrar(self):
        self._validar()
        with conectar() as conexion:
            # BEGIN IMMEDIATE: nadie más escribe mientras se calcula el número.
            conexion.execute("BEGIN IMMEDIATE")
            self.nro_registro = self.generar_nro_registro(self.gestion, conexion)
            cursor = conexion.execute(
                """INSERT INTO documento_recibido
                   (nro_registro, gestion, categoria, nro_oficio, fecha_hora_recepcion,
                    remitente, asunto, archivo_escaneado, requiere_respuesta, estado)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.nro_registro, self.gestion, self.categoria, self.nro_oficio.strip(),
                 self.fecha_hora_recepcion, self.remitente.strip(), self.asunto.strip(),
                 self.archivo_escaneado, int(self.requiere_respuesta), self.estado),
            )
            self.id_recibido = cursor.lastrowid
        return self

    def cambiar_estado(self, estado):
        """RF05: pendiente, en curso o completado."""
        if estado not in ESTADOS:
            raise ValueError("Estado no válido.")
        with conectar() as conexion:
            conexion.execute(
                "UPDATE documento_recibido SET estado = ? WHERE id_recibido = ?",
                (estado, self.id_recibido),
            )
        self.estado = estado

    def adjuntar_escaneado(self, ruta_origen):
        nombre = f"Recibido {self.nro_oficio} {self.remitente}"
        self.archivo_escaneado = self.copiar_escaneado(
            ruta_origen, f"recibidos/{self.gestion}", nombre
        )
        with conectar() as conexion:
            conexion.execute(
                "UPDATE documento_recibido SET archivo_escaneado = ? WHERE id_recibido = ?",
                (self.archivo_escaneado, self.id_recibido),
            )

    def posible_repetido(self):
        """
        Regla POR CONFIRMAR con la directora: el mismo número puede venir de
        remitentes distintos. Por eso no se bloquea: solo se avisa si ya existe
        el mismo número, del mismo remitente, en la misma gestión.
        """
        with conectar() as conexion:
            fila = conexion.execute(
                """SELECT 1 FROM documento_recibido
                   WHERE nro_oficio = ? AND lower(remitente) = lower(?)
                   AND substr(fecha_hora_recepcion, 1, 4) = ?""",
                (self.nro_oficio.strip(), self.remitente.strip(), str(self.gestion)),
            ).fetchone()
        return fila is not None

    # ---------- validación ----------

    def _validar(self):
        obligatorios = {
            "número de oficio": self.nro_oficio,
            "fecha y hora de recepción": self.fecha_hora_recepcion,
            "remitente": self.remitente,
            "asunto": self.asunto,
        }
        faltan = [campo for campo, valor in obligatorios.items() if texto_vacio(valor)]
        if faltan:
            raise ValueError("Falta completar: " + ", ".join(faltan) + ".")
        if self.categoria not in CATEGORIAS:
            raise ValueError("Elija una categoría de la lista.")
        if not self.requiere_respuesta:
            # Un documento solo de conocimiento no queda pendiente.
            self.estado = "completado"

    # ---------- consultas ----------

    @classmethod
    def _desde_fila(cls, f):
        return cls(f["nro_oficio"], f["fecha_hora_recepcion"], f["remitente"], f["asunto"],
                   f["requiere_respuesta"], f["estado"], f["archivo_escaneado"], f["id_recibido"],
                   f["categoria"], f["nro_registro"])

    @classmethod
    def obtener(cls, id_recibido):
        with conectar() as conexion:
            fila = conexion.execute(
                "SELECT * FROM documento_recibido WHERE id_recibido = ?", (id_recibido,)
            ).fetchone()
        if not fila:
            raise ValueError("No se encontró el documento.")
        return cls._desde_fila(fila)

    @classmethod
    def buscar(cls, texto="", categoria=None):
        """RF09 y RF17: busca por número, remitente o asunto, y filtra por categoría."""
        consulta = "SELECT * FROM documento_recibido WHERE 1 = 1"
        parametros = []
        if categoria:
            consulta += " AND categoria = ?"
            parametros.append(categoria)
        texto = (texto or "").strip()
        if texto:
            consulta += " AND (nro_oficio LIKE ? OR remitente LIKE ? OR asunto LIKE ?)"
            parametros += [f"%{texto}%"] * 3
        consulta += " ORDER BY gestion DESC, nro_registro DESC"
        with conectar() as conexion:
            return [cls._desde_fila(f) for f in conexion.execute(consulta, parametros)]

    @classmethod
    def pendientes(cls):
        """RF10: los que hay que responder y todavía no están completados."""
        with conectar() as conexion:
            filas = conexion.execute(
                """SELECT * FROM documento_recibido
                   WHERE requiere_respuesta = 1 AND estado != 'completado'
                   ORDER BY fecha_hora_recepcion"""
            ).fetchall()
        return [cls._desde_fila(f) for f in filas]
