"""
componentes.py
Piezas que usan todas las pantallas: tabla, campos, mensajes y ventanitas.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

FUENTE = ("Segoe UI", 13)
FUENTE_TITULO = ("Segoe UI", 22, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 15, "bold")

TIPOS_ESCANEADO = [("Escaneados", "*.pdf *.jpg *.jpeg *.png"), ("Todos los archivos", "*.*")]

# Colores de estado (RNF05): verde = terminado, amarillo = en camino, rojo = falta hacer algo.
# (fondo de la fila, color de la letra)
COLORES_ESTADO = {
    "completado": ("#dcf3e3", "#1d6b35"),
    "aprobado": ("#dcf3e3", "#1d6b35"),
    "en curso": ("#fff3c4", "#7a5a00"),
    "esperando": ("#fff3c4", "#7a5a00"),
    "pendiente": ("#fbdada", "#9b1c1c"),
    "rechazado": ("#fbdada", "#9b1c1c"),
}


def configurar_estilo_tablas():
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure("Treeview", rowheight=28, font=("Segoe UI", 11),
                     background="#ffffff", fieldbackground="#ffffff")
    estilo.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"),
                     background="#e8eef6", relief="flat")
    estilo.map("Treeview", background=[("selected", "#2f6fb5")],
               foreground=[("selected", "#ffffff")])


# ---------- mensajes ----------

def mostrar_error(error):
    messagebox.showerror("No se pudo completar", str(error))


def mostrar_info(mensaje):
    messagebox.showinfo("Listo", mensaje)


def confirmar(mensaje):
    return messagebox.askyesno("Confirmar", mensaje)


def elegir_escaneado():
    return filedialog.askopenfilename(title="Elegir archivo escaneado", filetypes=TIPOS_ESCANEADO)


# ---------- títulos y campos ----------

def titulo(master, texto, subtitulo=None):
    marco = ctk.CTkFrame(master, fg_color="transparent")
    marco.pack(fill="x", padx=24, pady=(20, 8))
    ctk.CTkLabel(marco, text=texto, font=FUENTE_TITULO).pack(anchor="w")
    if subtitulo:
        ctk.CTkLabel(marco, text=subtitulo, font=FUENTE, text_color="gray40").pack(anchor="w")
    return marco


def campo(marco, fila, columna, etiqueta, ancho=260, valor=""):
    """Etiqueta + caja de texto en una grilla. Devuelve la caja."""
    ctk.CTkLabel(marco, text=etiqueta, font=FUENTE).grid(
        row=fila, column=columna, sticky="w", padx=(12, 6), pady=6)
    caja = ctk.CTkEntry(marco, width=ancho, font=FUENTE)
    caja.grid(row=fila, column=columna + 1, sticky="w", padx=(0, 12), pady=6)
    if valor:
        caja.insert(0, valor)
    return caja


def poner_texto(caja, texto):
    caja.delete(0, "end")
    if texto:
        caja.insert(0, texto)


# ---------- tabla ----------

class Tabla(ctk.CTkFrame):
    """
    columnas: lista de (titulo, ancho).
    Cada fila se carga con un id (el de la base de datos) y sus valores.
    """

    def __init__(self, master, columnas, alto=10, al_doble_click=None):
        super().__init__(master, fg_color="transparent")
        nombres = [f"c{i}" for i in range(len(columnas))]
        self.arbol = ttk.Treeview(self, columns=nombres, show="headings",
                                  height=alto, selectmode="browse")
        for nombre, (texto, ancho) in zip(nombres, columnas):
            self.arbol.heading(nombre, text=texto, anchor="w")
            self.arbol.column(nombre, width=ancho, anchor="w", stretch=True)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=barra.set)
        self.arbol.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        if al_doble_click:
            self.arbol.bind("<Double-1>", lambda _evento: al_doble_click())
        for estado, (fondo, letra) in COLORES_ESTADO.items():
            self.arbol.tag_configure(estado, background=fondo, foreground=letra)

    def cargar(self, filas):
        """
        Cada fila es (id, valores) o (id, valores, estado).
        Si viene el estado, la fila se pinta con su color.
        """
        self.arbol.delete(*self.arbol.get_children())
        for fila in filas:
            identificador, valores = fila[0], fila[1]
            estado = fila[2] if len(fila) > 2 else None
            self.arbol.insert("", "end", iid=str(identificador),
                              values=["" if v is None else v for v in valores],
                              tags=(estado,) if estado in COLORES_ESTADO else ())

    def seleccionado(self):
        seleccion = self.arbol.selection()
        return int(seleccion[0]) if seleccion else None


# ---------- ventanita de formulario ----------

class Dialogo(ctk.CTkToplevel):
    """
    Ventana con algunos campos. campos: lista de diccionarios
      {"clave": ..., "etiqueta": ..., "valor": ..., "opciones": [...]}  (opciones es opcional)
    Después de cerrarla, .resultado tiene un diccionario o None si se canceló.
    """

    def __init__(self, master, titulo_ventana, campos):
        super().__init__(master)
        self.title(titulo_ventana)
        self.resizable(False, False)
        self.resultado = None
        self._cajas = {}

        marco = ctk.CTkFrame(self, fg_color="transparent")
        marco.pack(padx=20, pady=20)
        for fila, datos in enumerate(campos):
            ctk.CTkLabel(marco, text=datos["etiqueta"], font=FUENTE).grid(
                row=fila, column=0, sticky="w", padx=6, pady=6)
            if "opciones" in datos:
                caja = ctk.CTkComboBox(marco, values=datos["opciones"], width=260,
                                       font=FUENTE, state="readonly")
                caja.set(datos.get("valor") or datos["opciones"][0])
            else:
                caja = ctk.CTkEntry(marco, width=260, font=FUENTE)
                if datos.get("valor"):
                    caja.insert(0, datos["valor"])
            caja.grid(row=fila, column=1, padx=6, pady=6)
            self._cajas[datos["clave"]] = caja

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(pady=(0, 16))
        ctk.CTkButton(botones, text="Aceptar", command=self._aceptar).pack(side="left", padx=6)
        ctk.CTkButton(botones, text="Cancelar", fg_color="gray60",
                      command=self.destroy).pack(side="left", padx=6)

        self.transient(master)
        self.after(150, self._enfocar)

    def _enfocar(self):
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    def _aceptar(self):
        self.resultado = {clave: caja.get().strip() for clave, caja in self._cajas.items()}
        self.destroy()

    @classmethod
    def preguntar(cls, master, titulo_ventana, campos):
        dialogo = cls(master, titulo_ventana, campos)
        master.wait_window(dialogo)
        return dialogo.resultado
