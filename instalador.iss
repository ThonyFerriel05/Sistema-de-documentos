; ============================================================
;  Instalador del Sistema de Documentación — Dirección de Carrera
;  Se abre con Inno Setup (https://jrsoftware.org/isinfo.php) y se compila con Ctrl+F9.
;  Antes hay que correr crear_exe.bat (necesita dist\SistemaDireccion\).
;  Resultado: salida_instalador\Instalar_SistemaDireccion.exe
; ============================================================

#define Nombre "Sistema de Documentación - Dirección de Carrera"
#define Version "1.0 beta"
#define Exe "SistemaDireccion.exe"

[Setup]
; Este código identifica al programa: NO cambiarlo entre versiones.
AppId={{6F1C2B7A-4E5D-4C3B-9A8E-1D2F3A4B5C6D}
AppName={#Nombre}
AppVersion={#Version}
AppPublisher=Carrera de Ingeniería en Sistemas - F.IN.I. - U.A.G.R.M.
; Se instala solo para el usuario: no pide permisos de administrador.
PrivilegesRequired=lowest
DefaultDirName={autopf}\Sistema Direccion
DefaultGroupName=Sistema Dirección
DisableProgramGroupPage=yes
OutputDir=salida_instalador
OutputBaseFilename=Instalar_SistemaDireccion
SetupIconFile=vistas_qt\iconos\sistema.ico
UninstallDisplayIcon={app}\{#Exe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el escritorio"; Flags: checkedonce

[Files]
Source: "dist\SistemaDireccion\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Sistema Dirección"; Filename: "{app}\{#Exe}"
Name: "{autodesktop}\Sistema Dirección"; Filename: "{app}\{#Exe}"; Tasks: escritorio

[Run]
Filename: "{app}\{#Exe}"; Description: "Abrir el sistema ahora"; Flags: nowait postinstall skipifsilent

; Al desinstalar NO se borran los datos (Documentos\Sistema Dirección):
; la base, los escaneados y las plantillas de la directora quedan a salvo.
