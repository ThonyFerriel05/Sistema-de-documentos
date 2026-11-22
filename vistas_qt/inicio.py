"""Pantalla de Inicio: lo que necesita atención hoy, de un vistazo.

Sin tarjetas ni líneas: saludo con la fecha, números grandes que llevan a su
sección, la lista de lo más urgente (RF10) y el estado de la copia (RF12).
Todo sale de datos.resumen_inicio(); aquí solo se dibuja.
"""
from datetime import datetime
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout

from utilidades import MESES

from .estilo import ACENTO, ESTADO_COLOR, TEXTO_SUAVE

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MAX_URGENTES = 5


def saludo(ahora: datetime) -> str:
    if ahora.hour < 12:
        return "Buenos días"
    if ahora.hour < 19:
        return "Buenas tardes"
    return "Buenas noches"


def fecha_larga(ahora: datetime) -> str:
    return f"{DIAS[ahora.weekday()].capitalize()} {ahora.day} de {MESES[ahora.month - 1]} de {ahora.year}"


def hace(dias: int) -> str:
    if dias <= 0:
        return "hoy"
    if dias == 1:
        return "ayer"
    return f"hace {dias} días"


class Clicable(QWidget):
    """Un bloque (número + etiqueta, o una fila) que responde al clic sin parecer botón."""
    clic = Signal()

    def __init__(self):
        super().__init__()
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.resaltar: list[QLabel] = []   # textos que se ponen azules al pasar el mouse

    def enterEvent(self, evento):
        for l in self.resaltar:
            l.setStyleSheet(f"color: {ACENTO};")
        super().enterEvent(evento)

    def leaveEvent(self, evento):
        for l in self.resaltar:
            l.setStyleSheet("")
        super().leaveEvent(evento)

    def mouseReleaseEvent(self, evento):
        if evento.button() == Qt.LeftButton and self.rect().contains(evento.position().toPoint()):
            self.clic.emit()
        super().mouseReleaseEvent(evento)


class PaginaInicio(QWidget):
    """
    fuente(): devuelve el resumen (ver datos.resumen_inicio).
    ir_a(nombre): cambia de sección ("Pendientes", "Oficios expedidos", ...).
    registrar(nombre): abre el formulario ("oficio", "recibido", "acta").
    """

    def __init__(self, fuente: Callable[[], dict], ir_a: Callable[[str], None],
                 registrar: Callable[[str], None]):
        super().__init__()
        self.fuente = fuente
        self.ir_a = ir_a

        afuera = QHBoxLayout(self)
        afuera.setContentsMargins(0, 0, 0, 0)
        cuerpo = QWidget(); cuerpo.setMaximumWidth(1080)   # en pantallas grandes no se estira:
        afuera.addWidget(cuerpo, 1, Qt.AlignHCenter)          # queda centrado
        lay = QVBoxLayout(cuerpo)
        lay.setContentsMargins(56, 48, 56, 32)
        lay.setSpacing(0)

        # ---- saludo + accesos para registrar ----
        arriba = QHBoxLayout()
        textos = QVBoxLayout(); textos.setSpacing(4)
        self.lbl_saludo = QLabel(); self.lbl_saludo.setObjectName("saludoInicio")
        self.lbl_fecha = QLabel(); self.lbl_fecha.setObjectName("fechaInicio")
        textos.addWidget(self.lbl_saludo); textos.addWidget(self.lbl_fecha)
        arriba.addLayout(textos); arriba.addStretch()
        for texto, clave in (("+ Oficio", "oficio"), ("+ Recibido", "recibido"), ("+ Acta", "acta")):
            b = QPushButton(texto); b.setObjectName("accesoInicio"); b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(f"Registrar {clave}")
            b.clicked.connect(lambda _=False, c=clave: registrar(c))
            arriba.addWidget(b, alignment=Qt.AlignVCenter)
        lay.addLayout(arriba)
        lay.addSpacing(48)

        # ---- números grandes ----
        self.grilla = QHBoxLayout(); self.grilla.setSpacing(72)
        self.bloques: list[tuple[Clicable, QLabel, QLabel]] = []
        self.secciones_bloques = [""] * 4
        for i in range(4):
            b = Clicable(); b.setObjectName("bloqueNumero")
            b.clic.connect(lambda i=i: self.ir_a(self.secciones_bloques[i]))
            v = QVBoxLayout(b); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
            n = QLabel(); n.setObjectName("numeroGrande")
            e = QLabel(); e.setObjectName("etiquetaNumero")
            v.addWidget(n); v.addWidget(e)
            b.resaltar.append(e)
            self.grilla.addWidget(b)
            self.bloques.append((b, n, e))
        self.grilla.addStretch()
        lay.addLayout(self.grilla)
        lay.addSpacing(56)

        # ---- lo más urgente ----
        fila_t = QHBoxLayout()
        t = QLabel("Para atender"); t.setObjectName("seccionInicio")
        self.ver_todo = QPushButton("Ver todos los pendientes  →"); self.ver_todo.setObjectName("enlaceInicio")
        self.ver_todo.setCursor(Qt.PointingHandCursor)
        self.ver_todo.clicked.connect(lambda: ir_a("Pendientes"))
        fila_t.addWidget(t); fila_t.addStretch(); fila_t.addWidget(self.ver_todo)
        lay.addLayout(fila_t)
        lay.addSpacing(10)
        self.lista = QVBoxLayout(); self.lista.setSpacing(2)
        lay.addLayout(self.lista)

        lay.addStretch(1)

        # ---- copia de seguridad, abajo y discreta ----
        self.copia = Clicable(); self.copia.setObjectName("filaCopia")
        h = QHBoxLayout(self.copia); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(8)
        self.punto_copia = QLabel("●"); self.punto_copia.setObjectName("puntoEstado")
        self.texto_copia = QLabel(); self.texto_copia.setObjectName("textoCopia")
        h.addWidget(self.punto_copia); h.addWidget(self.texto_copia); h.addStretch()
        self.copia.resaltar.append(self.texto_copia)
        self.copia.clic.connect(lambda: ir_a("Configuración y respaldo"))
        lay.addWidget(self.copia)

    # ---------- llenar con los datos ----------

    def recargar(self):
        r = self.fuente()
        ahora = datetime.now()
        self.lbl_saludo.setText(saludo(ahora))
        self.lbl_fecha.setText(f"{fecha_larga(ahora)}  ·  Gestión {ahora.year}")

        for i, ((_, n, e), dato) in enumerate(zip(self.bloques, r["numeros"])):
            n.setText(str(dato["valor"]))
            e.setText(dato["etiqueta"] + "  →")
            color = dato.get("color") if dato["valor"] else None
            n.setStyleSheet(f"color: {ESTADO_COLOR[color]};" if color else "")
            self.secciones_bloques[i] = dato["seccion"]

        self._llenar_urgentes(r["urgentes"], r["total_pendientes"])
        self._mostrar_copia(r["dias_copia"], r["hay_datos"])

    def _llenar_urgentes(self, urgentes, total):
        while self.lista.count():
            w = self.lista.takeAt(0).widget()
            if w:
                w.deleteLater()
        if not urgentes:
            vacio = QLabel("Nada pendiente. Todo al día.")
            vacio.setObjectName("vacioInicio")
            self.lista.addWidget(vacio)
            self.ver_todo.hide()
            return
        self.ver_todo.setText(f"Ver los {total} pendientes  →" if total > MAX_URGENTES
                              else "Ver pendientes  →")
        self.ver_todo.show()
        for u in urgentes[:MAX_URGENTES]:
            fila = Clicable(); fila.setObjectName("filaUrgente")
            h = QHBoxLayout(fila); h.setContentsMargins(12, 10, 12, 10); h.setSpacing(14)
            punto = QLabel("●"); punto.setObjectName("puntoEstado")
            punto.setStyleSheet(f"color: {ESTADO_COLOR.get(u['estado'], TEXTO_SUAVE)};")
            tipo = QLabel(u["tipo"]); tipo.setObjectName("tipoUrgente"); tipo.setFixedWidth(72)
            numero = QLabel(u["numero"]); numero.setObjectName("numeroUrgente"); numero.setFixedWidth(120)
            asunto = QLabel(u["asunto"]); asunto.setObjectName("asuntoUrgente")
            asunto.setToolTip(u["asunto"])
            asunto.setMinimumWidth(80)
            quien = QLabel(u["quien"]); quien.setObjectName("quienUrgente")
            tiempo = QLabel(hace(u["dias"])); tiempo.setObjectName("tiempoUrgente")
            tiempo.setAlignment(Qt.AlignRight | Qt.AlignVCenter); tiempo.setFixedWidth(110)
            if u["dias"] >= 7:
                tiempo.setStyleSheet(f"color: {ESTADO_COLOR['pendiente']}; font-weight: 600;")
            for w in (punto, tipo, numero):
                h.addWidget(w)
            h.addWidget(asunto, 1)
            h.addWidget(quien)
            h.addWidget(tiempo)
            fila.resaltar.append(asunto)
            fila.clic.connect(lambda: self.ir_a("Pendientes"))
            self.lista.addWidget(fila)

    def _mostrar_copia(self, dias, hay_datos):
        if dias is None:
            texto = ("Todavía no se hizo ninguna copia de seguridad — hacer una ahora"
                     if hay_datos else "Sin copias de seguridad todavía")
            color = "pendiente" if hay_datos else None
        elif dias > 7:
            texto, color = f"Última copia de seguridad {hace(dias)} — conviene hacer otra", "pendiente"
        else:
            texto, color = f"Última copia de seguridad: {hace(dias)}", "completado"
        self.texto_copia.setText(texto)
        self.punto_copia.setStyleSheet(f"color: {ESTADO_COLOR[color] if color else TEXTO_SUAVE};")
