param(
    [int]$ShardCount = 256,
    [int]$Start = 0,
    [int]$End = 0
)
if ($End -lt $Start) { $End = $ShardCount - 1 }
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = (Resolve-Path (Join-Path $root "..\..\..\..")).Path
$py = "python"
$script = Join-Path $repo "search_p71_scaled_mitm.py"
$logDir = Join-Path $root "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
foreach ($id in $Start..$End) {
    $log = Join-Path $logDir ("shard_{0:D4}.log" -f $id)
    Start-Process -FilePath $py -ArgumentList @(
        $script,
        "--shard-id", $id,
        "--shard-count", $ShardCount,
        "--require-idx42",
        "--log-every", "100"
    ) -RedirectStandardOutput $log -RedirectStandardError $log -WindowStyle Hidden
    Write-Host "started shard $id -> $log"
}
