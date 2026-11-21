# Sistema de control de documentación — Dirección de Carrera de Ingeniería en Sistemas (F.IN.I.)

Versión beta. Python + PySide6 (ventanas) + SQLite (base de datos) + python-docx (Word).

## Cómo ejecutarlo (en tu PC)

1. Python 3.13 con el entorno `.venv` (creado con uv).
2. En esta carpeta:
   ```
   uv pip install -r requirements.txt
   .venv\Scripts\python.exe main_qt.py
   ```
   (`main.py` abre la interfaz vieja de CustomTkinter, que queda solo como respaldo.)

## Dónde se guardan los datos (RNF04)

Los datos NO van en la carpeta del programa (una vez instalado, Windows no deja escribir ahí).
Van en **Documentos\Sistema Dirección**:

| Qué | Dónde |
|---|---|
| Base de datos | `direccion.db` |
| Escaneados y Word de los oficios | `archivos\` |
| Plantillas en uso | `plantillas\` (las que vienen con el programa se copian la primera vez) |
| Copias de seguridad hechas "en esta computadora" | `respaldos\` |
| Fecha de la última copia (para el aviso de 7 días) | `ultimo_respaldo.txt` |

La primera vez, si encuentra datos en el lugar viejo (la carpeta del programa), los **copia**
a Documentos sin borrar los originales.

## Pruebas automáticas (fase de Pruebas)

```
.venv\Scripts\python.exe -m unittest pruebas.prueba_sistema -v
```
Son 22 pruebas, cada una dice qué requisito verifica. Usan una copia y una carpeta de datos
temporales: no tocan los datos reales.

## Crear el .exe e instalador

1. **El .exe:** doble clic en `crear_exe.bat`. Instala PyInstaller, corre las pruebas y arma
   `dist\SistemaDireccion\SistemaDireccion.exe` (modo carpeta: abre más rápido que un solo .exe).
   Para probarlo, abre ese .exe directamente.
2. **El instalador:** instala Inno Setup 6 (https://jrsoftware.org/isdl.php), abre `instalador.iss`
   y presiona **Compilar** (Ctrl+F9). Sale `salida_instalador\Instalar_SistemaDireccion.exe`.
3. **En la laptop de la directora:** doble clic en el instalador → Siguiente → Instalar.
   Se instala solo para su usuario (no pide administrador) y deja un acceso directo en el escritorio.
   Si aparece "Windows protegió su PC": **Más información → Ejecutar de todas formas**
   (sale porque el programa no tiene firma digital).
4. Desinstalar no borra los datos de `Documentos\Sistema Dirección`.

Requisito: Windows 10 u 11 de 64 bits (Python 3.13 no funciona en Windows 7 u 8).

## Antes de la demo

- Base limpia: cerrar el programa y borrar `Documentos\Sistema Dirección\direccion.db`
  y `archivos\oficios_generados`. Al abrir se registran solas las plantillas incluidas.
- En "Configuración y respaldo", escribir el último número de oficio usado en papel.

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
| `plantillas/` | Plantilla oficial "Oficio general" (formato real de la dirección) | RF13 |
| `servicios/plantillas.py` | Llena el Word | Secuencia "registrar expedido", pasos 6 a 9 |
| `servicios/respaldo.py` | Copia de seguridad | RF12 |
| `servicios/inicio.py` | Prepara la carpeta de datos y las plantillas la primera vez | RNF04 |
| `vistas_qt/` | Las pantallas (PySide6) | "Pantalla" en los diagramas de secuencia |
| `vistas/` | Pantallas viejas (CustomTkinter), solo respaldo | — |
| `pruebas/` | Pruebas automáticas | Fase de pruebas |

## Cambios del 19 de noviembre de 2026

- Expedidos: casilla "Requiere respuesta". Si no se marca, el oficio queda completado y no sale en pendientes.
- Recibidos: categoría (Docente, Auxiliatura, Invitación, Solicitud de informe, Resolución, Otro) con filtro,
  y número interno que vuelve a 01 cada gestión.
- Actas: número interno por gestión y filtro por modalidad (lista ampliada, por confirmar).
- Colores de estado en las tablas: verde = completado/aprobado, amarillo = en curso/esperando,
  rojo = pendiente/rechazado.
- Si `direccion.db` es de la versión anterior, se actualiza sola al abrir el programa, sin perder datos.
