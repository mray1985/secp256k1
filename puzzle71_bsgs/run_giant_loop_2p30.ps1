param(
  [int]$StartJ = 0,
  [int]$MaxJ = -1
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = Join-Path $scriptDir "run_giant_2p30.bat"

if (-not (Test-Path $bat)) {
  throw "Missing: $bat"
}

function Run-OneShard([int]$j) {
  Write-Host ("=== GIANT_SHARD_START j={0} {1} ===" -f $j, (Get-Date).ToString("s"))
  $p = Start-Process -FilePath $bat -ArgumentList @("$j") -NoNewWindow -PassThru -Wait
  Write-Host ("=== GIANT_SHARD_DONE  j={0} exit={1} {2} ===" -f $j, $p.ExitCode, (Get-Date).ToString("s"))
  if ($p.ExitCode -ne 0) {
    throw "Shard j=$j failed with exit code $($p.ExitCode)"
  }
}

$j = $StartJ
while ($true) {
  if ($MaxJ -ge 0 -and $j -gt $MaxJ) {
    Write-Host ("Reached MaxJ={0}. Stopping." -f $MaxJ)
    break
  }

  Run-OneShard -j $j
  $j++
}

