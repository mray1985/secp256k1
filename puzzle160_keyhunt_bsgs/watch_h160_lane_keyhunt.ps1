# Monitor KeyHunt h160 lane: log status every 15 min; restart search if bloom done but process died.
$ErrorActionPreference = "SilentlyContinue"

$Kh = "Z:\root\keyhunt-main\keyhunt-win-main\MinGW\keyhunt.exe"
$Wd = "Z:\root\keyhunt-main\keyhunt-win-main\MinGW"
$Pub = "C:\Users\mitch\Desktop\secp256k1\puzzle160_keyhunt_bsgs\P160_compressed.pub"
$Range = "e84818e1bf7f699aa6e28ef9edfb482100000000:e84818e1bf7f699aa6e28ef9edfb582100000000"
$Log = "C:\Users\mitch\Desktop\secp256k1\ARCHIVE\h160_lane_keyhunt_status.txt"
$TermLog = "C:\Users\mitch\.cursor\projects\C-Users-mitch\terminals\839250.txt"
$Bloom = Join-Path $Wd "keyhunt_bsgs_4_2147483648.blm"
$Interval = 900

function Write-Status([string]$Msg) {
    $line = "[{0:yyyy-MM-dd HH:mm:ss}] {1}" -f (Get-Date), $Msg
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Output $line
}

function Get-KeyhuntProc {
    Get-Process -Name "keyhunt" -ErrorAction SilentlyContinue | Select-Object -First 1
}

function Get-TailContext([string]$Path, [int]$Chars = 12000) {
    if (-not (Test-Path $Path)) { return "(no log yet)" }
    $raw = Get-Content -Path $Path -Raw -ErrorAction SilentlyContinue
    if (-not $raw) { return "(empty log)" }
    if ($raw.Length -le $Chars) { return $raw }
    return $raw.Substring($raw.Length - $Chars)
}

function Parse-Phase([string]$Tail) {
    if ($Tail -match "Private Key Found|KEY FOUND") { return "FOUND" }
    if ($Tail -match "\[\+\] Total time") { return "FINISHED" }
    if ($Tail -match "processing \d+/2147483648 bP points : (\d+)%") { return "BLOOM $($Matches[1])%" }
    if ($Tail -match "\[\+\] \d+ keys checked") { return "SEARCHING" }
    if (Test-Path $Bloom) {
        $sz = (Get-Item $Bloom).Length
        if ($sz -ge 7000000000) { return "BLOOM_READY" }
        return ("BLOOM_FILE {0:N1}GB" -f ($sz / 1GB))
    }
    return "UNKNOWN"
}

function Start-Keyhunt([bool]$BuildBloom) {
    $khArgs = "-m bsgs -f `"$Pub`" -r $Range -k 512 -t 4 -s 10 -q"
    if ($BuildBloom) { $khArgs += " -S" }
    Write-Status "Starting KeyHunt build_bloom=$BuildBloom"
    Start-Process -FilePath $Kh -ArgumentList $khArgs -WorkingDirectory $Wd -WindowStyle Minimized
}

New-Item -ItemType Directory -Force -Path (Split-Path $Log) | Out-Null
Write-Status "h160 lane monitor started interval=${Interval}s"
Write-Status "Range: $Range"

if (-not (Get-KeyhuntProc)) {
    $bloomOk = (Test-Path $Bloom) -and ((Get-Item $Bloom).Length -ge 7000000000)
    Start-Keyhunt (-not $bloomOk)
    Start-Sleep -Seconds 5
}

while ($true) {
    $proc = Get-KeyhuntProc
    $tail = Get-TailContext $TermLog
    $phase = Parse-Phase $tail
    $bloomSz = if (Test-Path $Bloom) { "{0:N2}GB" -f ((Get-Item $Bloom).Length / 1GB) } else { "missing" }
    if ($proc) {
        $pidStr = "PID $($proc.Id) CPU=$([int]$proc.CPU)s WS=$([math]::Round($proc.WorkingSet64/1GB,2))GB"
    } else {
        $pidStr = "not running"
    }
    Write-Status "phase=$phase | $pidStr | bloom=$bloomSz"

    if ($phase -eq "FOUND") {
        Write-Status "KEY FOUND - check KeyHunt output"
        break
    }

    if (-not $proc) {
        $bloomOk = (Test-Path $Bloom) -and ((Get-Item $Bloom).Length -ge 7000000000)
        if ($bloomOk -and $phase -ne "FINISHED") {
            Write-Status "Bloom ready, restarting search without -S"
            Start-Keyhunt $false
        } elseif (-not $bloomOk) {
            Write-Status "Bloom incomplete, restarting with -S"
            Start-Keyhunt $true
        } else {
            Write-Status "Search finished with no hit"
            break
        }
    }

    Start-Sleep -Seconds $Interval
}
