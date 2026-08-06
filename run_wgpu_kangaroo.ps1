param(
    [int]$Bits = 65,
    [int]$Start = 1,
    [int]$End = 806,
    [int]$TimeoutMin = 1440
)

$Root = "C:\Users\mitch\Desktop\secp256k1"
$KangarooExe = "$Root\kangaroo_wgpu\target\release\kangaroo.exe"
$CandidatesTsv = "$Root\135kanga_2p${Bits}_candidates.tsv"
$OutDir = "$Root\wgpu_kangaroo_results"
$Pubkey = "02145D2611C823A396EF6712CE0F712F09B9B4F3135E3E0AA3230FB9B6D08D1E16"

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

$Candidates = Import-Csv -Path $CandidatesTsv -Delimiter "`t"
$Selected = $Candidates | Where-Object { [int]$_.idx -ge $Start -and [int]$_.idx -le $End }

$Total = $Selected.Count
$Done = 0

foreach ($Row in $Selected) {
    $Done++
    $Idx = $Row.idx
    $Label = $Row.label
    $LoHex = $Row.lo_hex.ToUpper()
    $RangeBits = $Row.width_bits
    $OutFile = "$OutDir\candidate_$( '{0:D4}' -f [int]$Idx )_$Label.txt"

    if (Test-Path $OutFile) {
        $Content = Get-Content $OutFile -Raw
        if ($Content -match "[0-9a-fA-F]{64}" -and $Content -notmatch "TIMEOUT|ERROR") {
            Write-Host "[$Idx/$Total] $Label - already done, skipping"
            continue
        }
    }

    Write-Host ("[$Idx/$Total] $Label : 0x$LoHex, ${RangeBits}bit, " + (Get-Date -Format 'HH:mm:ss'))

    $Timeout = $TimeoutMin * 60
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $KangarooExe
    $psi.Arguments = "--pubkey $Pubkey --start $LoHex --range $RangeBits --output `"$OutFile`" --backend vulkan"
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true

    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
        if (-not $proc.WaitForExit($Timeout * 1000)) {
            $proc.Kill()
            Set-Content -Path $OutFile -Value "TIMEOUT after ${TimeoutMin}min"
            Write-Host "  TIMEOUT"
            continue
        }
        $stdout = $proc.StandardOutput.ReadToEnd()
        $stderr = $proc.StandardError.ReadToEnd()
        Set-Content -Path $OutFile -Value "$stdout`n---STDERR---`n$stderr"

        if ($stdout -match "Key found|Privkey|SOLVED") {
            Write-Host "  *** KEY FOUND! ***"
            Set-Content -Path "$OutDir\SOLVED.txt" -Value $stdout
            return
        }
        Write-Host "  Done (exit $($proc.ExitCode))"
    } catch {
        Set-Content -Path $OutFile -Value "ERROR: $_"
        Write-Host "  ERROR: $_"
    }
}
