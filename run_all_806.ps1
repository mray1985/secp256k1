param(
    [int]$Start = 1,
    [int]$End = 806,
    [int]$HoursPerCandidate = 12
)

$Root = "C:\Users\mitch\Desktop\secp256k1"
$Exe = "$Root\kangaroo_wgpu\target\release\kangaroo.exe"
$Tsv = "$Root\135kanga_2p65_candidates.tsv"
$OutDir = "$Root\wgpu_kangaroo_results"
$Pubkey = "02145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16"
$LogFile = "$OutDir\runner_log.txt"

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

$Candidates = Import-Csv -Path $Tsv -Delimiter "`t"
$Total = $Candidates.Count

function Write-Log {
    param($Msg)
    $Line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Msg"
    Add-Content -Path $LogFile -Value $Line
    Write-Host $Line
}

for ($i = $Start; $i -le $End -and $i -le $Total; $i++) {
    $Row = $Candidates[$i - 1]
    $Idx = $Row.idx
    $Label = $Row.label
    $LoHex = $Row.lo_hex.ToUpper()
    $RangeBits = $Row.width_bits
    $OutFile = "$OutDir\candidate_$( '{0:D4}' -f [int]$Idx )_$Label.txt"
    $Name = "candidate_$( '{0:D4}' -f [int]$Idx )_$Label"

    if (Test-Path $OutFile) {
        $Content = Get-Content $OutFile -Raw -ErrorAction SilentlyContinue
        if ($Content -match "[0-9a-fA-F]{64}" -and $Content -notmatch "ERROR|TIMEOUT|GPU") {
            Write-Log "[$i/$Total] $Name - already done, skip"
            continue
        }
    }

    Write-Log "[$i/$Total] $Name - launching 0x$LoHex ${RangeBits}bit"

    $TimeoutSec = $HoursPerCandidate * 3600
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = "--pubkey $Pubkey --start $LoHex --range $RangeBits --output `"$OutFile`" --backend vulkan"
    $psi.UseShellExecute = $true
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden

    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
        $pid = $proc.Id
        Write-Log "  PID=$pid"

        $elapsed = 0
        $poll = 120
        $done = $false

        while ($elapsed -lt $TimeoutSec -and -not $done) {
            Start-Sleep -Seconds $poll
            $elapsed += $poll

            $alive = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if (-not $alive) {
                Write-Log "  PID=$pid exited"
                $done = $true
            }

            if (Test-Path $OutFile) {
                $c = Get-Content $OutFile -Raw -ErrorAction SilentlyContinue
                if ($c -match "SOLVED|Key found|Privkey") {
                    Write-Log "  *** KEY FOUND! ***"
                    Copy-Item $OutFile "$OutDir\SOLVED.txt" -Force
                    return
                }
                if ($c -match "Error|failed|timed out") {
                    Write-Log "  Error in output, candidate failed"
                    $done = $true
                }
            }
        }

        if (-not $done) {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Add-Content -Path $OutFile -Value "`nTIMEOUT"
            Write-Log "  TIMEOUT killed PID=$pid"
        }
    } catch {
        Write-Log "  ERROR: $_"
    }
}

Write-Log "=== All $Start..$End done ==="
Write-Host "`nDONE. Check $OutDir for results"
