; Instalador do Coletor TCG Live (Inno Setup 6). Não rode direto: use  python instalador/montar.py
; Recebe /DVersao=... e /DOrigem=<pasta build/ColetorTCG>.

#ifndef Versao
  #define Versao "0"
#endif
#ifndef Origem
  #define Origem "..\build\ColetorTCG"
#endif

[Setup]
AppId={{6B1E2B5C-4C5E-4E0A-9C8E-2F7A1D3C9B41}
AppName=Coletor TCG Live
AppVersion={#Versao}
AppPublisher=Coletor TCG Live (projeto pessoal, sem ligação com a Pokémon)
DefaultDirName={localappdata}\Programs\ColetorTCG
DefaultGroupName=Coletor TCG Live
DisableProgramGroupPage=yes
; instala só para a pessoa, sem pedir senha de administrador (e o atualizador consegue trocar os arquivos)
PrivilegesRequired=lowest
OutputBaseFilename=ColetorTCG-Instalador-{#Versao}
SetupIconFile={#Origem}\web\icone.ico
UninstallDisplayIcon={app}\web\icone.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; fecha o Coletor aberto antes de trocar os arquivos
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "areadetrabalho"; Description: "Criar o atalho na Área de Trabalho"; GroupDescription: "Atalhos:"
Name: "inicializar"; Description: "Abrir o Coletor sozinho quando o Windows ligar"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "{#Origem}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; dados/ (partidas, decks, configurações) nunca é apagado pelo desinstalador
Name: "{app}\dados"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\Coletor TCG Live"; Filename: "{app}\python\pythonw.exe"; Parameters: "app.py"; WorkingDir: "{app}"; IconFilename: "{app}\web\icone.ico"
Name: "{userdesktop}\Coletor TCG Live"; Filename: "{app}\python\pythonw.exe"; Parameters: "app.py"; WorkingDir: "{app}"; IconFilename: "{app}\web\icone.ico"; Tasks: areadetrabalho
Name: "{userstartup}\Coletor TCG Live"; Filename: "{app}\python\pythonw.exe"; Parameters: "app.py --sem-navegador"; WorkingDir: "{app}"; IconFilename: "{app}\web\icone.ico"; Tasks: inicializar

[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: "app.py"; WorkingDir: "{app}"; Description: "Abrir o Coletor agora"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; fecha só o Coletor DESTA instalação (o Python dela fica em {app}\python), em qualquer porta;
; um Coletor de outra pasta continua aberto. Usa a lista de processos do Windows (CIM): o desinstalador é de
; 32 bits e abre o PowerShell de 32 bits, que não enxerga o caminho de programas de 64 bits com Get-Process.
; No Inno, só a chave de abrir é dobrada ({{); a de fechar fica simples.
Filename: "powershell.exe"; Parameters: "-NoProfile -Command ""Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -like '{app}\python\*' } | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }"""; Flags: runhidden; RunOnceId: "FecharColetor"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\tracker\__pycache__"
