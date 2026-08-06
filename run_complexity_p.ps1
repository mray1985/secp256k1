<#
.SYNOPSIS
    Executes Python code from Complexity_Simplified_p.txt and prints to screen
.DESCRIPTION
    Reads Complexity_Simplified_p.txt from 02_Research\notes\, 
    extracts Python code, executes it, and prints output to console.
.USAGE
    .\run_complexity_p.ps1
#>

$inputFile = "$PSScriptRoot\02_Research\notes\Complexity_Simplified_p.txt"

if (-not (Test-Path $inputFile)) {
    Write-Host "ERROR: File not found: $inputFile" -ForegroundColor Red
    exit 1
}

Write-Host "Reading: $inputFile" -ForegroundColor Cyan

# Read and filter out non-code lines (.LOG, timestamps, empty)
$pythonCode = Get-Content $inputFile | Where-Object {
    $_ -match '\S' -and 
    $_ -notmatch '^\.LOG' -and 
    $_ -notmatch '^[0-9:]+[ ]+[AP]M'
}

if (-not $pythonCode) {
    Write-Host "ERROR: No Python code found in file" -ForegroundColor Red
    exit 1
}

# Save to temp file
$tempPyFile = "$env:TEMP\temp_complexity_p_$pid.py"
$pythonCode | Out-File -FilePath $tempPyFile -Encoding UTF8

Write-Host "Executing Python code..." -ForegroundColor Cyan

# Find python
$pythonExe = Get-Command python3 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $pythonExe) {
    $pythonExe = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
}

if (-not $pythonExe) {
    Write-Host "ERROR: Python not found. Install Python 3." -ForegroundColor Red
    exit 1
}

# Run and print output in real-time
try {
    $process = Start-Process -FilePath $pythonExe -ArgumentList $tempPyFile -NoNewWindow -PassThru -RedirectStandardOutput "$tempPyFile.out" -RedirectStandardError "$tempPyFile.err"
    $process.WaitForExit()
    
    if ($process.ExitCode -eq 0) {
        Get-Content "$tempPyFile.out" -Raw
    } else {
        Write-Host "Error (exit code $($process.ExitCode)):" -ForegroundColor Yellow
        Get-Content "$tempPyFile.err" -Raw
    }
} finally {
    # Cleanup
    if (Test-Path $tempPyFile) { Remove-Item $tempPyFile -Force }
    if (Test-Path "$tempPyFile.out") { Remove-Item "$tempPyFile.out" -Force }
    if (Test-Path "$tempPyFile.err") { Remove-Item "$tempPyFile.err" -Force }
}

Write-Host "Done." -ForegroundColor Green
