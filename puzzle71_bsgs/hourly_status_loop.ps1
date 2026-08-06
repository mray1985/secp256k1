# Hourly wake for agent — do not run manually unless testing
$script = 'C:\Users\mitch\Desktop\secp256k1\puzzle71_bsgs\status_baby_2p30.ps1'
while ($true) {
    Start-Sleep -Seconds 3600
    & $script | Out-Null
    Write-Output 'AGENT_LOOP_TICK_BABY2P30 {"prompt":"Check Puzzle 71 M=2^30 baby build status: run status_baby_2p30.ps1, read C:\puzzle71_bsgs\logs\hourly_status.log tail and baby_2p30.log tail. Give user a brief hourly status update (progress %, GB, ETA, running yes/no). If build finished or crashed, say so and stop recommending hourly checks."}'
}
