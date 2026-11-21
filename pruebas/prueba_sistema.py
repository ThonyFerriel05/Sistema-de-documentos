"""
prueba_sistema.py
Pruebas automáticas de las reglas del sistema (fase de Pruebas de la cascada).
Cada prueba dice qué requisito verifica.

Se ejecutan con:   python -m unittest pruebas.prueba_sistema -v
Usan una copia temporal del sistema, así que NO tocan los datos reales.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ_ORIGINAL = Path(__file__).resolve().parent.parent


def preparar_copia():
    """Copia el código a una carpeta temporal y trabaja ahí."""
    temporal = Path(tempfile.mkdtemp())
    ignorar = shutil.ignore_patterns("direccion.db", "archivos", "respaldos", "plantillas",
                                     "__pycache__", "pruebas", ".venv", ".git")
    shutil.copytree(RAIZ_ORIGINAL, temporal / "sistema", ignore=ignorar)
    # Los datos de prueba van a una carpeta temporal, nunca a Documentos.
    os.environ["SISTEMA_DIRECCION_DATOS"] = str(temporal / "datos")
    sys.path.insert(0, str(temporal / "sistema"))
    return temporal


TEMPORAL = preparar_copia()

from docx import Document as WordDocument  # noqa: E402

from modelos.acta import MODALIDADES, Acta  # noqa: E402
from modelos.configuracion import definir_ultimo_numero_previo  # noqa: E402
from modelos.expedido import DocumentoExpedido  # noqa: E402
from modelos.recibido import DocumentoRecibido  # noqa: E402
from modelos.tipo_tramite import TipoTramite  # noqa: E402
from servicios.inicio import preparar_sistema  # noqa: E402
from servicios.respaldo import crear_respaldo  # noqa: E402

preparar_sistema()
TRAMITE = TipoTramite.listar()[0]


def nuevo_oficio(fecha, asunto="Prueba", via=False, original=None):
    return DocumentoExpedido(
        fecha_envio=fecha, destinatario_nombre="M.Sc. Ejemplo Pérez",
        destinatario_cargo="Responsable de caja F.IN.I. - U.A.G.R.M.", asunto=asunto,
        id_tipo=TRAMITE.id_tipo,
        via_nombre="M.Sc. Decano Ejemplo" if via else None,
        via_cargo="DECANO DE LA FACULTAD INTEGRAL DE ICHILO" if via else None,
        id_original=original,
    ).registrar()


class PruebasExpedidos(unittest.TestCase):

    def test_01_numero_inicial_configurado(self):
        """RF16: si la directora va por el 130, el siguiente es 131/2025."""
        definir_ultimo_numero_previo(2025, 130)
        oficio = nuevo_oficio("2025-11-20")
        self.assertEqual(oficio.numero_corto, "131/2025")
        self.assertEqual(nuevo_oficio("2025-11-21").numero_corto, "132/2025")

    def test_02_nueva_gestion_vuelve_a_01(self):
        """RF01: en una gestión nueva el número vuelve a 01."""
        oficio = nuevo_oficio("2030-01-05")
        self.assertEqual(oficio.numero_corto, "01/2030")
        self.assertEqual(
            oficio.codigo_completo, "DIR.CARR.ING.SISTEMAS F.IN.I. OF. No. 01/2030"
        )

    def test_03_no_bajar_numero_inicial(self):
        """RF16: no se puede poner un número menor a uno ya usado."""
        with self.assertRaises(ValueError):
            definir_ultimo_numero_previo(2025, 10)

    def test_04_campos_obligatorios(self):
        """RF01: no se registra un oficio sin destinatario."""
        with self.assertRaises(ValueError):
            DocumentoExpedido("2025-11-22", "", "", "Algo", TRAMITE.id_tipo).registrar()

    def test_05_word_con_via(self):
        """RF13: el Word lleva fecha en letras, código y VIA."""
        oficio = nuevo_oficio("2031-09-21", asunto="Solicitud de certificación", via=True)
        ruta = oficio.generar_con_plantilla()
        self.assertTrue(ruta.exists())
        self.assertTrue(ruta.name.startswith("Oficio No 01 Solicitud"))
        texto = "\n".join(p.text for p in WordDocument(str(ruta)).paragraphs)
        self.assertIn("Yapacaní, 21 de septiembre de 2031", texto)
        self.assertIn("OF. No. 01/2031", texto)
        self.assertIn("DECANO DE LA FACULTAD INTEGRAL DE ICHILO", texto)
        self.assertIn("c.c. Archivo 2031.", texto)
        self.assertNotIn("{{", texto)

    def test_06_word_sin_via(self):
        """RF13: si no hay VIA, esas líneas desaparecen."""
        oficio = nuevo_oficio("2031-09-22", asunto="Remito actas")
        texto = "\n".join(p.text for p in WordDocument(str(oficio.generar_con_plantilla())).paragraphs)
        self.assertNotIn("VIA", texto)
        self.assertNotIn("{{", texto)

    def test_07_respuesta_y_reenvio(self):
        """RF02 y RF03: se rechaza, se reenvía con número nuevo y queda enlazado."""
        original = nuevo_oficio("2032-03-01")
        original.registrar_respuesta("rechazado", "RES-15/2032", "05/03/2032")
        self.assertEqual(DocumentoExpedido.obtener(original.id_expedido).estado, "rechazado")

        nuevo = original.preparar_reenvio()
        nuevo.fecha_envio = "2032-03-06"
        nuevo.registrar()
        self.assertEqual(nuevo.numero_corto, "02/2032")
        self.assertEqual(DocumentoExpedido.obtener(nuevo.id_expedido).id_original,
                         original.id_expedido)

    def test_08_pendientes(self):
        """RF10: un oficio esperando aparece en pendientes; uno aprobado no."""
        esperando = nuevo_oficio("2033-01-10")
        aprobado = nuevo_oficio("2033-01-11")
        aprobado.registrar_respuesta("aprobado", "RES-1", "12/01/2033")
        ids = [o.id_expedido for o in DocumentoExpedido.pendientes()]
        self.assertIn(esperando.id_expedido, ids)
        self.assertNotIn(aprobado.id_expedido, ids)

    def test_09_buscar_por_numero(self):
        """RF09: buscar '01/2034' o 'certificación' encuentra el oficio."""
        oficio = nuevo_oficio("2034-02-02", asunto="Certificación de horas")
        self.assertIn(oficio.id_expedido,
                      [o.id_expedido for o in DocumentoExpedido.buscar("01", gestion=2034)])
        self.assertIn(oficio.id_expedido,
                      [o.id_expedido for o in DocumentoExpedido.buscar("certificación")])


    def test_22_plantilla_oficial_con_tabla(self):
        """RF13: la plantilla oficial (A / DE en tabla, con logos) se llena completa."""
        oficial = RAIZ_ORIGINAL / "plantillas" / "Oficio general.docx"
        tramite = TipoTramite.crear("Prueba plantilla oficial", oficial)
        for con_via in (True, False):
            oficio = DocumentoExpedido(
                fecha_envio="2032-03-10", destinatario_nombre="M.Sc. Ejemplo Pérez",
                destinatario_cargo="Responsable de caja", asunto=f"Prueba via {con_via}",
                id_tipo=tramite.id_tipo,
                via_nombre="M.Sc. Decano Ejemplo" if con_via else None,
                via_cargo="DECANO" if con_via else None,
            ).registrar()
            doc = WordDocument(str(oficio.generar_con_plantilla()))
            etiquetas = [fila.cells[1].text for fila in doc.tables[0].rows]
            texto = "\n".join(p.text for p in doc.paragraphs)
            self.assertEqual(etiquetas, ["A", "DE"])  # la plantilla oficial no lleva VIA
            self.assertIn("Yapacaní, 10 de marzo de 2032", texto)
            self.assertIn("OF. No. ", texto)
            self.assertNotIn("{{", texto + " ".join(c.text for f in doc.tables[0].rows for c in f.cells))


class PruebasRecibidos(unittest.TestCase):

    def test_10_solo_conocimiento_no_queda_pendiente(self):
        """RF04 y RF10: si no requiere respuesta, no aparece en pendientes."""
        r = DocumentoRecibido("15/2026", "2026-09-10 13:05", "Decanatura", "Aviso",
                              requiere_respuesta=False).registrar()
        self.assertEqual(r.estado, "completado")
        self.assertNotIn(r.id_recibido, [x.id_recibido for x in DocumentoRecibido.pendientes()])

    def test_11_cambiar_estado(self):
        """RF05: pendiente -> en curso -> completado."""
        r = DocumentoRecibido("20/2026", "2026-09-11 09:00", "Rectorado", "Solicitud",
                              requiere_respuesta=True).registrar()
        self.assertIn(r.id_recibido, [x.id_recibido for x in DocumentoRecibido.pendientes()])
        r.cambiar_estado("en curso")
        r.cambiar_estado("completado")
        self.assertNotIn(r.id_recibido, [x.id_recibido for x in DocumentoRecibido.pendientes()])

    def test_12_aviso_de_posible_repetido(self):
        """Mismo número y remitente en la misma gestión: avisa. Otro remitente: no."""
        DocumentoRecibido("30/2026", "2026-10-01 10:00", "Rectorado", "A", True).registrar()
        self.assertTrue(DocumentoRecibido("30/2026", "2026-10-02 10:00", "rectorado", "B", True)
                        .posible_repetido())
        self.assertFalse(DocumentoRecibido("30/2026", "2026-10-02 10:00", "Decanatura", "B", True)
                         .posible_repetido())


class PruebasActas(unittest.TestCase):

    def test_13_acta_repetida(self):
        """RF07: el mismo número o el mismo código de acta se rechazan."""
        Acta("9001", "11111-111-1111", "1234567 SC", 79, MODALIDADES[0]).registrar()
        with self.assertRaises(ValueError):
            Acta("9001", "otro-codigo", "7654321 SC", 70, MODALIDADES[1]).registrar()
        with self.assertRaises(ValueError):
            Acta("9002", "11111-111-1111", "7654321 SC", 70, MODALIDADES[1]).registrar()

    def test_14_nota_fuera_de_rango(self):
        """La nota debe ser un entero entre 0 y 100."""
        with self.assertRaises(ValueError):
            Acta("9003", "c-9003", "1111111 SC", 150, MODALIDADES[0]).registrar()
        with self.assertRaises(ValueError):
            Acta("9004", "c-9004", "1111111 SC", "79.5", MODALIDADES[0]).registrar()

    def test_15_buscar_por_carnet(self):
        """RF08: '2222222 S.C' encuentra el acta guardada como '2222222 SC'."""
        acta = Acta("9005", "c-9005", "2222222 SC", 85, MODALIDADES[1]).registrar()
        encontrados = [a.id_acta for a in Acta.buscar_por_carnet("2222222 S.C")]
        self.assertIn(acta.id_acta, encontrados)


class PruebasCambios19Nov(unittest.TestCase):
    """Cambios acordados el 19 de noviembre de 2026."""

    def test_17_expedido_sin_respuesta(self):
        """RF01 y RF10: un oficio que no requiere respuesta queda completado y no es pendiente."""
        oficio = DocumentoExpedido(
            fecha_envio="2035-04-01", destinatario_nombre="Lic. Ejemplo",
            destinatario_cargo="Jefe de archivo", asunto="Remito actas",
            id_tipo=TRAMITE.id_tipo, requiere_respuesta=False,
        ).registrar()
        guardado = DocumentoExpedido.obtener(oficio.id_expedido)
        self.assertEqual(guardado.estado, "completado")
        self.assertFalse(guardado.requiere_respuesta)
        self.assertNotIn(oficio.id_expedido,
                         [o.id_expedido for o in DocumentoExpedido.pendientes()])

    def test_18_numero_interno_recibidos(self):
        """RF18: los recibidos se numeran 01, 02... y vuelven a 01 en la gestión siguiente."""
        a = DocumentoRecibido("1", "2036-02-01 08:00", "DIGA", "A", True).registrar()
        b = DocumentoRecibido("2", "2036-03-01 08:00", "DIGA", "B", True).registrar()
        c = DocumentoRecibido("3", "2037-01-05 08:00", "DIGA", "C", True).registrar()
        self.assertEqual((a.registro_corto, b.registro_corto, c.registro_corto),
                         ("01/2036", "02/2036", "01/2037"))

    def test_19_filtrar_recibidos_por_categoria(self):
        """RF17: el informe final de un docente se encuentra filtrando por 'Docente'."""
        informe = DocumentoRecibido("S/N", "2038-06-30 10:00", "Ing. Docente Ejemplo",
                                    "Informe final de cátedra", False,
                                    categoria="Docente").registrar()
        invitacion = DocumentoRecibido("44/2038", "2038-07-01 10:00", "Decanatura",
                                       "Acto cívico", False, categoria="Invitación").registrar()
        ids = [d.id_recibido for d in DocumentoRecibido.buscar(categoria="Docente")]
        self.assertIn(informe.id_recibido, ids)
        self.assertNotIn(invitacion.id_recibido, ids)
        with self.assertRaises(ValueError):
            DocumentoRecibido("1", "2038-07-02 10:00", "X", "Y", False,
                              categoria="Inventada").registrar()

    def test_20_actas_numero_interno_y_modalidad(self):
        """RF18 y RF19: número interno por gestión y filtro por modalidad."""
        a = Acta("9101", "c-9101", "3333333 SC", 90, "Tesis de grado", gestion=2039).registrar()
        b = Acta("9102", "c-9102", "4444444 SC", 95, MODALIDADES[0], gestion=2039).registrar()
        self.assertEqual((a.registro_corto, b.registro_corto), ("01/2039", "02/2039"))
        ids = [x.id_acta for x in Acta.filtrar_por_modalidad("Tesis de grado")]
        self.assertIn(a.id_acta, ids)
        self.assertNotIn(b.id_acta, ids)
        # Carnet y modalidad juntos
        self.assertEqual([x.id_acta for x in Acta.buscar("3333333", "Tesis de grado")],
                         [a.id_acta])

    def test_21_actualiza_base_vieja(self):
        """Una base de datos de la versión anterior se actualiza sin perder datos."""
        import sqlite3
        import database
        ruta_vieja = TEMPORAL / "vieja.db"
        con = sqlite3.connect(ruta_vieja)
        con.executescript("""
            CREATE TABLE tipo_tramite (id_tipo INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE, ruta_plantilla TEXT NOT NULL);
            CREATE TABLE documento_expedido (id_expedido INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo INTEGER NOT NULL, gestion INTEGER NOT NULL, fecha_envio TEXT NOT NULL,
                destinatario_nombre TEXT NOT NULL, destinatario_cargo TEXT NOT NULL,
                via_nombre TEXT, via_cargo TEXT, asunto TEXT NOT NULL,
                id_tipo INTEGER NOT NULL REFERENCES tipo_tramite(id_tipo),
                archivo_escaneado TEXT,
                estado TEXT NOT NULL DEFAULT 'esperando'
                    CHECK (estado IN ('esperando', 'aprobado', 'rechazado')),
                nro_resolucion TEXT, fecha_resolucion TEXT,
                id_original INTEGER REFERENCES documento_expedido(id_expedido),
                UNIQUE (codigo, gestion));
            CREATE TABLE documento_recibido (id_recibido INTEGER PRIMARY KEY AUTOINCREMENT,
                nro_oficio TEXT NOT NULL, fecha_hora_recepcion TEXT NOT NULL,
                remitente TEXT NOT NULL, asunto TEXT NOT NULL, archivo_escaneado TEXT,
                requiere_respuesta INTEGER NOT NULL, estado TEXT NOT NULL DEFAULT 'pendiente');
            CREATE TABLE acta (id_acta INTEGER PRIMARY KEY AUTOINCREMENT,
                nro_acta TEXT NOT NULL UNIQUE, codigo TEXT NOT NULL UNIQUE,
                carnet TEXT NOT NULL, nota INTEGER NOT NULL, modalidad TEXT NOT NULL,
                archivo_escaneado TEXT);
            CREATE INDEX idx_acta_carnet ON acta(carnet);
            INSERT INTO tipo_tramite VALUES (1, 'Oficio general', 'x.docx');
            INSERT INTO documento_expedido (codigo, gestion, fecha_envio, destinatario_nombre,
                destinatario_cargo, asunto, id_tipo) VALUES (112, 2026, '2026-11-10', 'A', 'B', 'C', 1);
            INSERT INTO documento_recibido (nro_oficio, fecha_hora_recepcion, remitente, asunto,
                requiere_respuesta, estado) VALUES ('7', '2026-11-01 09:00', 'DIGA', 'X', 1, 'pendiente');
            INSERT INTO documento_recibido (nro_oficio, fecha_hora_recepcion, remitente, asunto,
                requiere_respuesta, estado) VALUES ('8', '2026-11-02 09:00', 'DIGA', 'Y', 0, 'completado');
            INSERT INTO acta (nro_acta, codigo, carnet, nota, modalidad)
                VALUES ('500', 'c-500', '1 SC', 80, 'Graduación directa por excelencia');
        """)
        con.close()

        ruta_real = database.RUTA_BD
        database.RUTA_BD = ruta_vieja
        try:
            database.crear_tablas()
            database.crear_tablas()  # una segunda vez no debe cambiar nada
            with database.conectar() as c:
                exp = c.execute("SELECT * FROM documento_expedido").fetchall()
                rec = c.execute("SELECT * FROM documento_recibido ORDER BY id_recibido").fetchall()
                act = c.execute("SELECT * FROM acta").fetchall()
                tablas = [f[0] for f in c.execute("SELECT name FROM sqlite_master")]
        finally:
            database.RUTA_BD = ruta_real
        self.assertEqual((exp[0]["codigo"], exp[0]["requiere_respuesta"]), (112, 1))
        self.assertEqual([(r["nro_registro"], r["gestion"], r["categoria"]) for r in rec],
                         [(1, 2026, "Otro"), (2, 2026, "Otro")])
        self.assertEqual((act[0]["nro_acta"], act[0]["nro_registro"]), ("500", 1))
        self.assertFalse(any(t.endswith("_v1") for t in tablas))
        self.assertIn("idx_acta_carnet", tablas)


class PruebasRespaldo(unittest.TestCase):

    def test_16_respaldo(self):
        """RF12: el respaldo incluye la base de datos y las plantillas."""
        import zipfile
        ruta = crear_respaldo()
        with zipfile.ZipFile(ruta) as z:
            nombres = z.namelist()
        self.assertIn("direccion.db", nombres)
        self.assertTrue(any(n.startswith("plantillas/") for n in nombres))


if __name__ == "__main__":
    unittest.main(verbosity=2)
