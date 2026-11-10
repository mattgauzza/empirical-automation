# Starts the receiver and the Cloudflare tunnel. Run from this folder:
#   powershell -ExecutionPolicy Bypass -File start.ps1
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$cfg  = Get-Content "$here\config.json" -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force "$here\logs" | Out-Null
Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" | Where-Object { $_.CommandLine -like '*receiver.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
# pythonw = no console window (a console can freeze the receiver if clicked)
Start-Process -FilePath "pythonw" -ArgumentList "`"$here\receiver.py`"" -WorkingDirectory $here
# Restart only THIS tunnel (any other cloudflared tunnels on the PC are left alone), hidden and
# logging to a file: a visible console window can freeze a program when it's clicked.
Get-CimInstance Win32_Process -Filter "Name='cloudflared.exe'" | Where-Object { $_.CommandLine -like "*$($cfg.tunnel_name)*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Process -WindowStyle Hidden -FilePath "cloudflared" -ArgumentList "tunnel --logfile `"$here\logs\tunnel.log`" run --url http://localhost:$($cfg.port) $($cfg.tunnel_name)"
Write-Host "Receiver on http://localhost:$($cfg.port)/  ->  https://$($cfg.public_host)/<route>"
