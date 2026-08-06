# Puzzle 71 M=2^30 baby build — hourly status snapshot
$log = 'C:\puzzle71_bsgs\logs\hourly_status.log'
$baby = 'C:\puzzle71_bsgs\baby\baby_h160.bin'
$buildLog = 'C:\puzzle71_bsgs\logs\baby_2p30.log'
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

$proc = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'build_baby_h160' }

$running = if ($proc) { "YES pid=$($proc.ProcessId)" } else { 'NO' }
$gb = if (Test-Path $baby) { [math]::Round((Get-Item $baby).Length / 1GB, 2) } else { 0 }
$cFree = [math]::Round((Get-PSDrive C).Free / 1GB, 1)

$lastLine = ''
if (Test-Path $buildLog) {
    $lastLine = Get-Content $buildLog -Tail 1 -ErrorAction SilentlyContinue
}

$line = "$ts | running=$running | baby_gb=$gb | target_gb=26.8 | c_free_gb=$cFree | $lastLine"
Add-Content -Path $log -Value $line
Write-Output $line
