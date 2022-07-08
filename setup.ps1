$service_settings = @"
[Unit]
Description=Discord bot
After=network.target

[Service]
User={0}
StartLimitBurst=0
WorkingDirectory={1}
ExecStart={2} -m robomania -c .env
Restart=always
Type=exec

[Install]
WantedBy=multi-user.target
"@

$service_path = "/lib/systemd/system/robomania.service"

if (-not(Test-Path -Path $service_path -PathType Leaf)) {
    $user = whoami

    $formatted_service_settings = [String]::Format($service_settings, $user, $env:ROBOMANIA_CWD, $env:ROBOMANIA_PY)

    try {
        $null = New-Item -ItemType File -Path $service_path -Force -ErrorAction Stop -Value $formatted_service_settings
        Write-Host "Created service file"

        sudo chmod 644 $service_path
        sudo systemctl daemon-reload
        sudo systemctl enable robomania
        sudo systemctl start robomania
    } catch {
        throw $_.Exception.Message
    }
} else {
    sudo systemctl restart robomania
}
