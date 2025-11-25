param(
    [Parameter(Mandatory=$true)]
    [string]$original,

    [Parameter(Mandatory=$false)]
    [string]$folder = ".",

    [switch]$RenameDirs
)

# Use the project venv Python if available else default python
$workspaceRoot = Resolve-Path ..\ -Relative | ForEach-Object { (Get-Location).ProviderPath }
$venvPython = Join-Path -Path (Get-Location) -ChildPath ".\.venv\Scripts\python.exe"
if (-Not (Test-Path $venvPython)) {
    $pythonExe = "python"
} else {
    $pythonExe = $venvPython
}

$scriptPath = Resolve-Path .\src\rename_with_dirs.py

# Build the command line using cmd /c and quote the empty string as "" to pass it to script
$cmdParts = @()
$cmdParts += "`"$pythonExe`""
$cmdParts += "`"$scriptPath`""
$cmdParts += "`"$original`""
$cmdParts += '""'  # This is the actual double-quoted empty string argument
$cmdParts += "`"$folder`""
if ($RenameDirs) {
    $cmdParts += "--rename-dirs"
}

$cmdString = [string]::Join(' ', $cmdParts)
Write-Host "Running command via cmd: $cmdString"

# Execute
cmd /c $cmdString
