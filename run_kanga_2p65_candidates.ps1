param(
    [Parameter(Mandatory=$true)]
    [string]$KangarooExe,

    [int]$Bits = 65,

    [int]$Start = 1,
    [int]$End = 806
)

$ErrorActionPreference = "Stop"

$Root = "C:\Users\mitch\Desktop\secp256k1\kanga_2p${Bits}_candidates"
$Files = Get-ChildItem -Path $Root -Filter "candidate_*.txt" |
    Sort-Object Name |
    Select-Object -Index (($Start - 1)..($End - 1))

foreach ($File in $Files) {
    Write-Host "Running $($File.Name)"
    & $KangarooExe $File.FullName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Kangaroo exited 0 on $($File.Name)"
    }
}
