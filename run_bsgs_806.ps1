param(
    [int]$Start = 1,
    [int]$End = 806,
    [string]$Keyhunt = "",
    [string]$PubDir = "",
    [string]$WorkDir = "",
    [int]$KFactor = 512,
    [int]$Stats = 10
)

$Root = "C:\Users\mitch\Desktop\secp256k1"
$Tsv = "$Root\135kanga_2p65_candidates.tsv"
$OutDir = "$Root\bsgs_results"
$LogFile = "$OutDir\runner_log.txt"

if (-not $Keyhunt) { $Keyhunt = "Z:\root\keyhunt-main\keyhunt-win-main\MinGW\keyhunt.exe" }
if (-not $PubDir)  { $PubDir = "$Root\puzzle135_keyhunt_bsgs\" }
if (-not $WorkDir) { $WorkDir = "Z:\root\keyhunt-main\keyhunt-win-main\MinGW" }

$PubFile = "$PubDir\P135_compressed.pub"
$Threads = $env:NUMBER_OF_PROCESSORS

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

$Candidates = Import-Csv -Path $Tsv -Delimiter "`t"
$Total = $Candidates.Count
if ($End -gt $Total) { $End = $Total }

function Write-Log {
    param($Msg)
    $Line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Msg"
    Add-Content -Path $LogFile -Value $Line
    Write-Host $Line
}

Write-Log "=== BSGS Runner ==="
Write-Log "Keyhunt: $Keyhunt"
Write-Log "PubFile: $PubFile"
Write-Log "WorkDir: $WorkDir"
Write-Log "Threads: $Threads  KFactor: $KFactor"
Write-Log "Candidates: $Start..$End of $Total"

for ($i = $Start; $i -le $End; $i++) {
    $Row = $Candidates[$i - 1]
    $Idx = $Row.idx
    $Label = $Row.label
    $LoHex = $Row.lo_hex
    $HiHex = $Row.hi_hex
    $WidthBits = $Row.width_bits
    $OutFile = "$OutDir\candidate_$( '{0:D4}' -f [int]$Idx )_$Label.txt"
    $Name = "candidate_$( '{0:D4}' -f [int]$Idx )_$Label"

    if (Test-Path $OutFile) {
        $c = Get-Content $OutFile -Raw -ErrorAction SilentlyContinue
        if ($c -match "Key found|Privkey|SOLVED") {
            Write-Log "[$i/$Total] $Name - already SOLVED, skip"
            continue
        }
        if ($c -match "BYE|Total.*keys" -and $c -notmatch "Error|ERROR|fail") {
            Write-Log "[$i/$Total] $Name - already done (no hit), skip"
            continue
        }
    }

    $Range = "${LoHex}:${HiHex}"
    $Args = "-m bsgs -f `"$PubFile`" -r $Range -k $KFactor -S -t $Threads -s $Stats -q"

    Write-Log "[$i/$Total] $Name - range ${WidthBits}bit  k=$KFactor  t=$Threads  -S"

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Keyhunt
    $psi.Arguments = $Args
    $psi.WorkingDirectory = $WorkDir
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
        $stdout = $proc.StandardOutput.ReadToEnd()
        $stderr = $proc.StandardError.ReadToEnd()
        $proc.WaitForExit()

        $out = "$stdout`n--- STDERR ---`n$stderr"
        Set-Content -Path $OutFile -Value $out

        if ($stdout -match "Key found|Privkey|SOLVED") {
            Write-Log "  *** KEY FOUND in $Name ***"
            Copy-Item $OutFile "$OutDir\SOLVED.txt" -Force
            Set-Content -Path "$OutDir\SOLVED_$Name.txt" -Value $out
            Write-Log "  Verify: $Label  d=0x$LoHex + offset"
        }

        Write-Log "  exit=$($proc.ExitCode)  $((Get-Item $OutFile).Length) bytes"
    } catch {
        Set-Content -Path $OutFile -Value "ERROR: $_"
        Write-Log "  ERROR: $_"
    }
}

Write-Log "=== BSGS Runner $Start..$End complete ==="
Write-Host "`nDone. Check $OutDir"
