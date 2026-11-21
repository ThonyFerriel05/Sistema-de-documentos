"""
acta.py
Clase Acta: actas de graduación (RF06, RF07, RF08, RF18, RF19).
El número de acta y el código los asigna el CPD; el sistema solo los registra.
"""

from datetime import date

from database import conectar
from modelos.documento import Documento
from utilidades import texto_vacio

# Lista fija. Las dos primeras salen de un oficio real de la dirección;
# las demás, de la entrevista a la directora (septiembre de 2026).
# POR CONFIRMAR con la directora.
MODALIDADES = [
    "Graduación directa por excelencia",
    "Graduación directa por buen desempeño",
    "Graduación directa por buen rendimiento",
    "Tesis de grado",
    "Trabajo dirigido",
    "Examen de grado",
    "Proyecto de grado",
    "Diplomado (titulación vía continua)",
]


class Acta:
    def __init__(self, nro_acta, codigo, carnet, nota, modalidad,
                 archivo_escaneado=None, id_acta=None, nro_registro=None, gestion=None):
        self.id_acta = id_acta
        # Número interno de la dirección (RF18): cuántas actas se registraron en el año.
        self.nro_registro = nro_registro
        self.gestion = gestion
        self.nro_acta = str(nro_acta).strip()
        self.codigo = str(codigo).strip()
        self.carnet = str(carnet).strip()
        self.nota = nota
        self.modalidad = modalidad
        self.archivo_escaneado = archivo_escaneado

    @property
    def registro_corto(self):
        if self.nro_registro is None:
            return ""
        return f"{self.nro_registro:02d}/{self.gestion}"

    # ---------- métodos del diagrama ----------

    @staticmethod
    def generar_nro_registro(gestion, conexion):
        """RF18: siguiente número interno de la gestión (vuelve a 1 cada año)."""
        mayor = conexion.execute(
            "SELECT COALESCE(MAX(nro_registro), 0) AS mayor FROM acta WHERE gestion = ?",
            (gestion,),
        ).fetchone()["mayor"]
        return mayor + 1

    def verificar_repetido(self):
        """RF07: devuelve un mensaje si el número o el código ya existen."""
        with conectar() as conexion:
            por_numero = conexion.execute(
                "SELECT carnet FROM acta WHERE nro_acta = ?", (self.nro_acta,)
            ).fetchone()
            por_codigo = conexion.execute(
                "SELECT nro_acta FROM acta WHERE codigo = ?", (self.codigo,)
            ).fetchone()
        if por_numero:
            return f"Ya existe el acta N.º {self.nro_acta} (carnet {por_numero['carnet']})."
        if por_codigo:
            return f"El código {self.codigo} ya está registrado en el acta N.º {por_codigo['nro_acta']}."
        return None

    @classmethod
    def buscar(cls, carnet="", modalidad=None):
        """
        RF08 y RF19: busca por carnet y/o filtra por modalidad.
        El carnet es lo que el graduado recuerda.
        """
        consulta = "SELECT * FROM acta WHERE 1 = 1"
        parametros = []
        carnet = (carnet or "").strip()
        if carnet:
            # Compara sin espacios ni puntos: '14117756 S.C' encuentra '14117756 SC'.
            consulta += " AND replace(replace(upper(carnet), ' ', ''), '.', '') LIKE ?"
            parametros.append(carnet.upper().replace(" ", "").replace(".", "") + "%")
        if modalidad:
            consulta += " AND modalidad = ?"
            parametros.append(modalidad)
        consulta += " ORDER BY gestion DESC, nro_registro DESC"
        with conectar() as conexion:
            return [cls._desde_fila(f) for f in conexion.execute(consulta, parametros)]

    @classmethod
    def buscar_por_carnet(cls, carnet):
        """RF08 (método del diagrama de secuencia 'buscar acta por carnet')."""
        return cls.buscar(carnet=carnet)

    @classmethod
    def filtrar_por_modalidad(cls, modalidad):
        """RF19: por ejemplo, todas las de 'Graduación directa por excelencia'."""
        return cls.buscar(modalidad=modalidad)

    # ---------- guardar ----------

    def registrar(self):
        self._validar()
        mensaje = self.verificar_repetido()
        if mensaje:
            raise ValueError(mensaje)
        # El acta no tiene fecha propia: cuenta para la gestión en que se registra.
        self.gestion = self.gestion or date.today().year
        with conectar() as conexion:
            conexion.execute("BEGIN IMMEDIATE")
            self.nro_registro = self.generar_nro_registro(self.gestion, conexion)
            cursor = conexion.execute(
                """INSERT INTO acta (nro_registro, gestion, nro_acta, codigo, carnet, nota,
                                     modalidad, archivo_escaneado)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.nro_registro, self.gestion, self.nro_acta, self.codigo, self.carnet,
                 self.nota, self.modalidad, self.archivo_escaneado),
            )
            self.id_acta = cursor.lastrowid
        return self

    def adjuntar_escaneado(self, ruta_origen):
        self.archivo_escaneado = Documento.copiar_escaneado(
            ruta_origen, "actas", f"Acta {self.nro_acta} - CI {self.carnet}"
        )
        with conectar() as conexion:
            conexion.execute(
                "UPDATE acta SET archivo_escaneado = ? WHERE id_acta = ?",
                (self.archivo_escaneado, self.id_acta),
            )

    def abrir_archivo(self):
        if not self.archivo_escaneado:
            raise ValueError("Esta acta todavía no tiene un archivo escaneado.")
        from database import CARPETA_SISTEMA
        from utilidades import abrir_con_programa
        abrir_con_programa(CARPETA_SISTEMA / self.archivo_escaneado)

    def _validar(self):
        obligatorios = {
            "número de acta": self.nro_acta, "código": self.codigo,
            "carnet": self.carnet, "nota": self.nota, "modalidad": self.modalidad,
        }
        faltan = [campo for campo, valor in obligatorios.items() if texto_vacio(valor)]
        if faltan:
            raise ValueError("Falta completar: " + ", ".join(faltan) + ".")
        try:
            self.nota = int(str(self.nota).strip())
        except ValueError:
            raise ValueError("La nota debe ser un número entero.")
        if not 0 <= self.nota <= 100:
            raise ValueError("La nota debe estar entre 0 y 100.")
        if self.modalidad not in MODALIDADES:
            raise ValueError("Elija una modalidad de la lista.")

    # ---------- consultas ----------

    @classmethod
    def _desde_fila(cls, f):
        return cls(f["nro_acta"], f["codigo"], f["carnet"], f["nota"], f["modalidad"],
                   f["archivo_escaneado"], f["id_acta"], f["nro_registro"], f["gestion"])

    @classmethod
    def obtener(cls, id_acta):
        with conectar() as conexion:
            fila = conexion.execute("SELECT * FROM acta WHERE id_acta = ?", (id_acta,)).fetchone()
        if not fila:
            raise ValueError("No se encontró el acta.")
        return cls._desde_fila(fila)

    @classmethod
    def listar(cls):
        with conectar() as conexion:
            filas = conexion.execute(
                "SELECT * FROM acta ORDER BY gestion DESC, nro_registro DESC").fetchall()
        return [cls._desde_fila(f) for f in filas]
