$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required but was not found on PATH. Install Git for Windows first."
}

$Python = Get-Command py -ErrorAction SilentlyContinue
if ($Python) {
    $PythonArgs = @("-3")
} else {
    $Python = Get-Command python -ErrorAction SilentlyContinue
    $PythonArgs = @()
}
if (-not $Python) {
    throw "Python 3.9 or newer is required. Alternatively, download git-multiple-windows-x64.zip from GitHub Releases."
}

& $Python.Source @PythonArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.9 or newer is required."
}

& $Python.Source @PythonArgs -m pip install --user $PSScriptRoot
if ($LASTEXITCODE -ne 0) {
    throw "Installation failed."
}

Write-Host "Git Multiple was installed. Run: git-multiple doctor"
Write-Host "If the command is not found, restart the terminal and ensure Python's Scripts directory is on PATH."
