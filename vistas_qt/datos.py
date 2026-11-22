"""Puente entre las pantallas nuevas y los modelos.

Aquí NO hay lógica nueva: solo se llama a los métodos de los modelos
(buscar, pendientes, listar) y se convierte cada objeto en una fila para la tabla.

Cada celda puede ser un texto o una pareja (texto, clave_para_ordenar).
La clave sirve para que '112/2026' quede después de '99/2026' al ordenar,
y para que las fechas se ordenen por fecha y no como texto.
"""
from datetime import date

from database import conectar
from modelos.acta import Acta
from modelos.expedido import DocumentoExpedido
from modelos.recibido import DocumentoRecibido
from modelos.tipo_tramite import TipoTramite
from utilidades import iso_a_fecha, iso_a_fecha_hora


def _todos(valor):
    """El primer elemento de cada filtro es 'Todos': eso significa sin filtro."""
    return None if not valor or valor.endswith("Todos") else valor


# ---------- Oficios expedidos ----------

def filas_expedidos(texto: str, filtros: dict):
    estado = _todos(filtros.get("Estado"))
    gestion = _todos(filtros.get("Gestión"))
    oficios = DocumentoExpedido.buscar(texto, gestion)
    if estado:
        oficios = [o for o in oficios if o.estado == estado.lower()]
    filas = []
    for o in oficios:
        destinatario = o.destinatario_nombre + (f" — {o.destinatario_cargo}" if o.destinatario_cargo else "")
        filas.append([
            (o.numero_corto, o.gestion * 10000 + o.codigo),
            (iso_a_fecha(o.fecha_envio), o.fecha_envio),
            destinatario,
            o.asunto,
            o.estado,
        ])
    return filas, oficios


def gestiones_expedidos():
    with conectar() as c:
        return [str(f["gestion"]) for f in c.execute(
            "SELECT DISTINCT gestion FROM documento_expedido ORDER BY gestion DESC")]


# ---------- Documentos recibidos ----------

def filas_recibidos(texto: str, filtros: dict):
    estado = _todos(filtros.get("Estado"))
    categoria = _todos(filtros.get("Categoría"))
    docs = DocumentoRecibido.buscar(texto, categoria)
    if estado:
        docs = [d for d in docs if d.estado == estado.lower()]
    filas = [[
        (d.registro_corto, d.gestion * 10000 + (d.nro_registro or 0)),
        d.nro_oficio,
        (iso_a_fecha_hora(d.fecha_hora_recepcion), d.fecha_hora_recepcion),
        d.remitente,
        d.asunto,
        d.categoria,
        d.estado,
    ] for d in docs]
    return filas, docs


# ---------- Actas ----------

def filas_actas(texto: str, filtros: dict):
    actas = Acta.buscar(texto, _todos(filtros.get("Modalidad")))
    filas = [[
        (a.registro_corto, (a.gestion or 0) * 10000 + (a.nro_registro or 0)),
        a.nro_acta,
        a.codigo,
        a.carnet,
        (str(a.nota), a.nota),
        a.modalidad,
    ] for a in actas]
    return filas, actas


# ---------- Pendientes (RF10) ----------

def filas_pendientes(texto: str, filtros: dict):
    texto = (texto or "").lower()
    filas, objetos = [], []
    for d in DocumentoRecibido.pendientes():
        filas.append(["Recibido", d.nro_oficio, d.remitente, d.asunto,
                      (iso_a_fecha_hora(d.fecha_hora_recepcion)[:10], d.fecha_hora_recepcion[:10]), d.estado])
        objetos.append(d)
    for o in DocumentoExpedido.pendientes():
        filas.append(["Expedido", o.numero_corto, o.destinatario_nombre, o.asunto,
                      (iso_a_fecha(o.fecha_envio), o.fecha_envio), o.estado])
        objetos.append(o)
    if texto:
        pares = [(f, o) for f, o in zip(filas, objetos)
                 if texto in " ".join(str(c[0] if isinstance(c, tuple) else c) for c in f).lower()]
        filas = [p[0] for p in pares]
        objetos = [p[1] for p in pares]
    return filas, objetos


def total_pendientes() -> int:
    return len(DocumentoRecibido.pendientes()) + len(DocumentoExpedido.pendientes())


# ---------- Trámites ----------

def filas_tramites(texto: str, filtros: dict):
    tramites = TipoTramite.listar()
    if texto:
        tramites = [t for t in tramites if texto.lower() in t.nombre.lower()]
    filas = []
    for t in tramites:
        archivo = t.ruta_plantilla.split("/")[-1]
        try:
            t.obtener_plantilla()
        except FileNotFoundError:
            archivo += "  (no se encuentra el archivo)"
        filas.append([t.nombre, archivo])
    return filas, tramites


# ---------- Inicio ----------

def _dias_desde(iso: str) -> int:
    """Días desde una fecha guardada como '2026-09-21' o '2026-09-21 13:05'."""
    return (date.today() - date.fromisoformat(iso[:10])).days


def resumen_inicio():
    """Todo lo que muestra la pantalla de Inicio, en un solo lugar."""
    from servicios.respaldo import dias_sin_respaldo

    anio = date.today().year
    with conectar() as c:
        recibidos_anio = c.execute(
            "SELECT COUNT(*) FROM documento_recibido WHERE gestion = ?", (anio,)).fetchone()[0]
        actas_anio = c.execute("SELECT COUNT(*) FROM acta WHERE gestion = ?", (anio,)).fetchone()[0]
        hay_datos = any(c.execute(f"SELECT 1 FROM {t} LIMIT 1").fetchone()
                        for t in ("documento_expedido", "documento_recibido", "acta"))
    recibidos = DocumentoRecibido.pendientes()
    oficios = DocumentoExpedido.pendientes()

    # Lo más urgente: lo que lleva más días esperando va primero (RF10)
    urgentes = [{
        "tipo": "Recibido", "numero": d.nro_oficio, "quien": d.remitente, "asunto": d.asunto,
        "estado": d.estado, "dias": _dias_desde(d.fecha_hora_recepcion),
    } for d in recibidos] + [{
        "tipo": "Oficio", "numero": o.numero_corto, "quien": o.destinatario_nombre, "asunto": o.asunto,
        "estado": o.estado, "dias": _dias_desde(o.fecha_envio),
    } for o in oficios]
    urgentes.sort(key=lambda u: -u["dias"])

    return {
        "numeros": [
            {"valor": len(recibidos), "etiqueta": "Recibidos por responder",
             "seccion": "Pendientes", "color": "pendiente"},
            {"valor": len(oficios), "etiqueta": "Oficios esperando respuesta",
             "seccion": "Pendientes", "color": "esperando"},
            {"valor": recibidos_anio, "etiqueta": f"Recibidos en {anio}",
             "seccion": "Documentos recibidos"},
            {"valor": actas_anio, "etiqueta": f"Actas registradas en {anio}",
             "seccion": "Actas de graduación"},
        ],
        "urgentes": urgentes,
        "total_pendientes": len(urgentes),
        "dias_copia": dias_sin_respaldo(),
        "hay_datos": hay_datos,
    }
