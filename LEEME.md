# Sistema de control de documentación — Dirección de Carrera de Ingeniería en Sistemas (F.IN.I.)

Versión beta. Python + CustomTkinter + SQLite.

## Cómo ejecutarlo (en tu PC)

1. Instala Python 3.11 o superior (en Windows, marca "Add Python to PATH").
2. En esta carpeta abre una terminal y ejecuta:
   ```
   pip install -r requirements.txt
   python main.py
   ```
   La primera vez se crean solos `direccion.db`, la carpeta `plantillas/` con el "Oficio general"
   y la carpeta `archivos/`.

## Pruebas automáticas (fase de Pruebas)

```
python -m unittest pruebas.prueba_sistema -v
```
Son 21 pruebas, cada una dice qué requisito verifica. Usan una copia temporal: no tocan los datos reales.

## Crear el .exe para la directora

```
pip install pyinstaller
pyinstaller --noconsole --onefile --name SistemaDireccion --collect-all customtkinter main.py
```
El .exe queda en `dist/`. Cópialo a una carpeta propia (por ejemplo `C:\SistemaDireccion\`):
la base de datos, los escaneados y las plantillas se crean al lado del .exe.

## Antes de entregarlo

- Abre `plantillas/Oficio general.docx` y agrega los dos logos del encabezado (UAGRM y carrera).
  No borres las marcas `{{...}}`.
- En "Configuración y respaldo", escribe el último número de oficio que ya se usó en papel en 2026.

## Cómo está organizado (coincide con el diseño)

| Carpeta / archivo | Qué es | Diseño |
|---|---|---|
| `database.py` | Crea las tablas | Diagrama entidad-relación |
| `modelos/documento.py` | Clase abstracta Documento | Diagrama de clases (herencia) |
| `modelos/expedido.py` | DocumentoExpedido | RF01, RF02, RF03, RF13, RF15, RF16 (con "requiere respuesta") |
| `modelos/recibido.py` | DocumentoRecibido | RF04, RF05, RF17 (categoría), RF18 (número interno) |
| `modelos/acta.py` | Acta | RF06, RF07, RF08, RF18 (número interno), RF19 (filtro por modalidad) |
| `modelos/tipo_tramite.py` | TipoTramite | RF13, RF14 |
| `modelos/configuracion.py` | Número inicial de la gestión | RF16 |
| `servicios/plantillas.py` | Llena el Word | Secuencia "registrar expedido", pasos 6 a 9 |
| `servicios/respaldo.py` | Copia de seguridad | RF12 |
| `vistas/` | Las pantallas | "Pantalla" en los diagramas de secuencia |
| `pruebas/` | Pruebas automáticas | Fase de pruebas |

## Cambios del 19 de noviembre de 2026

- Expedidos: casilla "Requiere respuesta". Si no se marca, el oficio queda completado y no sale en pendientes.
- Recibidos: categoría (Docente, Auxiliatura, Invitación, Solicitud de informe, Resolución, Otro) con filtro,
  y número interno que vuelve a 01 cada gestión.
- Actas: número interno por gestión y filtro por modalidad (lista ampliada, por confirmar).
- Colores de estado en las tablas: verde = completado/aprobado, amarillo = en curso/esperando,
  rojo = pendiente/rechazado.
- Si `direccion.db` es de la versión anterior, se actualiza sola al abrir el programa, sin perder datos.
