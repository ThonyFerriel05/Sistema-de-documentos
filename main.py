"""
main.py
Punto de entrada: prepara la base de datos y abre la ventana principal.
"""

import traceback
from tkinter import messagebox

from servicios.inicio import preparar_sistema


def main():
    try:
        preparar_sistema()
        from vistas.app import Aplicacion
        Aplicacion().mainloop()
    except Exception:
        messagebox.showerror("Error al iniciar", traceback.format_exc())


if __name__ == "__main__":
    main()
