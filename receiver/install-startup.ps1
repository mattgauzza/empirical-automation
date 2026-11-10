# Run ONCE. Registers a Windows task that starts the receiver + tunnel at every sign-in, restarts it
# if it stops, and starts it right now. After this you never run start.ps1 by hand.
#   powershell -ExecutionPolicy Bypass -File install-startup.ps1
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$name = "Board hooks receiver"
$act  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$here\start.ps1`"" -WorkingDirectory $here
$trg  = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$set  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $name -Action $act -Trigger $trg -Settings $set -Description "Webhook receiver + Cloudflare tunnel for board-driven agents" -Force | Out-Null
Start-ScheduledTask -TaskName $name
Write-Host "Installed and started task '$name'. It starts by itself at every sign-in; config.json edits are picked up live."
Write-Host "After changing receiver.py, restart it:  Start-ScheduledTask -TaskName '$name'"
