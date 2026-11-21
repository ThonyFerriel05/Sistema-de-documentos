"""Colores y estilo (QSS) de todo el programa.

QSS es la forma de darle estilo a las ventanas de Qt; se parece mucho a CSS.
Si quieres cambiar un color, cámbialo aquí y se aplica en todo el sistema.
"""

from pathlib import Path

# Ícono de flecha para las listas desplegables (Qt pide la ruta con barras /)
FLECHA = (Path(__file__).resolve().parent / "iconos" / "flecha.svg").as_posix()

# Paleta
FONDO = "#FFFFFF"          # fondo principal
FONDO_MENU = "#F5F6F8"     # menú lateral: apenas distinto, sin línea
TEXTO = "#1F2328"
TEXTO_SUAVE = "#6B7280"
ACENTO = "#2F5BD3"         # color del botón principal y la sección marcada
ACENTO_SUAVE = "#E8EEFC"
FILA_HOVER = "#F7F8FA"
FILA_ELEGIDA = "#EEF2FD"

# Colores de estado (RNF05)
ESTADO_COLOR = {
    "completado": "#2E9E5B", "aprobado": "#2E9E5B",
    "en curso": "#D9A21B", "esperando": "#D9A21B",
    "pendiente": "#D64545", "rechazado": "#D64545",
}

QSS = f"""
* {{
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 14px;
    color: {TEXTO};
}}
QMainWindow, #contenido {{ background: {FONDO}; }}

/* ---- Menú lateral ---- */
#menu {{ background: {FONDO_MENU}; border: none; }}
#nombreSistema {{ font-size: 15px; font-weight: 600; padding: 4px 8px; }}
#subNombre {{ color: {TEXTO_SUAVE}; font-size: 12px; padding: 0 8px; }}
QListWidget#listaMenu {{ background: transparent; border: none; outline: none; }}
QListWidget#listaMenu::item {{
    padding: 9px 10px; border-radius: 8px; margin: 1px 0;
    color: {TEXTO};
}}
QListWidget#listaMenu::item:hover {{ background: #ECEEF2; }}
QListWidget#listaMenu::item:selected {{
    background: {ACENTO_SUAVE}; color: {ACENTO}; font-weight: 600;
}}

/* ---- Títulos ---- */
#tituloPagina {{ font-size: 26px; font-weight: 600; }}
#subtituloPagina {{ color: {TEXTO_SUAVE}; font-size: 14px; }}

/* ---- Inicio: números sueltos, sin tarjetas ---- */
#numeroGrande {{ font-size: 44px; font-weight: 600; }}
#etiquetaNumero {{ color: {TEXTO_SUAVE}; font-size: 14px; }}

/* ---- Botones ---- */
QPushButton {{
    background: transparent; border: none; border-radius: 8px;
    padding: 8px 14px; color: {TEXTO_SUAVE};
}}
QPushButton:hover {{ background: #F0F1F4; color: {TEXTO}; }}
QPushButton#botonPrincipal {{
    background: {ACENTO}; color: white; font-weight: 600; padding: 9px 18px;
}}
QPushButton#botonPrincipal:hover {{ background: #264BB0; }}

/* ---- Buscador y filtros ---- */
QLineEdit#buscador {{
    background: {FONDO_MENU}; border: 1px solid transparent; border-radius: 10px;
    padding: 10px 14px; font-size: 15px;
}}
QLineEdit#buscador:focus {{ border: 1px solid {ACENTO}; background: white; }}
QComboBox {{
    background: transparent; border: none; border-radius: 8px;
    padding: 6px 10px; color: {TEXTO_SUAVE};
}}
QComboBox:hover {{ background: #F0F1F4; }}
QComboBox QAbstractItemView {{
    background: white; border: 1px solid #E5E7EB; selection-background-color: {ACENTO_SUAVE};
    selection-color: {TEXTO}; outline: none;
}}

/* ---- Tabla: sin bordes, sin cuadrícula ---- */
QTableView {{
    background: {FONDO}; border: none; gridline-color: transparent;
    selection-background-color: {FILA_ELEGIDA}; selection-color: {TEXTO};
    outline: none;
}}
QTableView::item {{ padding: 0 10px; border: none; }}
QTableView::item:hover {{ background: {FILA_HOVER}; }}
QHeaderView::section {{
    background: {FONDO}; border: none; color: {TEXTO_SUAVE};
    font-size: 12px; font-weight: 600; padding: 8px 10px;
}}
/* ---- Formularios ---- */
QDialog#formulario {{ background: {FONDO}; }}
#tituloFormulario {{ font-size: 20px; font-weight: 600; }}
#notaFormulario {{ color: {ACENTO}; font-weight: 600; }}
QLineEdit#campo, QDateEdit#campo, QDateTimeEdit#campo, QComboBox#campo {{
    background: white; border: 1px solid #DADDE3; border-radius: 8px;
    padding: 7px 10px; color: {TEXTO}; min-width: 320px;
}}
QLineEdit#campo:focus, QDateEdit#campo:focus, QDateTimeEdit#campo:focus, QComboBox#campo:focus {{ border: 1px solid {ACENTO}; }}
QComboBox#campo::drop-down, QDateEdit#campo::drop-down, QDateTimeEdit#campo::drop-down {{
    border: none; width: 28px; subcontrol-origin: padding; subcontrol-position: center right;
}}
QComboBox::down-arrow, QDateEdit#campo::down-arrow, QDateTimeEdit#campo::down-arrow {{ image: url("{FLECHA}"); width: 12px; height: 12px; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QFormLayout QLabel, QDialog#formulario QLabel {{ min-height: 34px; }}
QCheckBox {{ spacing: 8px; }}
QPushButton#botonSecundario {{ border: 1px solid #DADDE3; color: {TEXTO}; }}

/* ---- Menú de acciones (clic derecho) ---- */
QMenu {{ background: white; border: 1px solid #E5E7EB; border-radius: 10px; padding: 6px; }}
QMenu::item {{ padding: 8px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {ACENTO_SUAVE}; color: {TEXTO}; }}
QMenu::item:disabled {{ color: #B0B5BD; }}
QMenu::separator {{ height: 6px; background: transparent; }}

QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: #D9DCE1; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
"""
