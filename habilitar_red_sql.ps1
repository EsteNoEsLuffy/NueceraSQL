# Ejecutar en PowerShell COMO ADMINISTRADOR.
# Habilita TCP/IP en el puerto 1433 para SQLEXPRESS01 y abre el firewall.
$base = "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\MSSQL15.SQLEXPRESS01\MSSQLServer\SuperSocketNetLib\Tcp"
Set-ItemProperty $base -Name Enabled -Value 1
Get-ChildItem $base | ForEach-Object {
    Set-ItemProperty $_.PSPath -Name TcpDynamicPorts -Value ""
    if ($_.PSChildName -eq "IPAll") { Set-ItemProperty $_.PSPath -Name TcpPort -Value "1433" }
}
# Modo de autenticacion mixto (usuarios SQL como AdminNancy)
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\MSSQL15.SQLEXPRESS01\MSSQLServer" -Name LoginMode -Value 2

New-NetFirewallRule -DisplayName "SQL Server 1433" -Direction Inbound -Protocol TCP -LocalPort 1433 -Action Allow -Profile Any -ErrorAction SilentlyContinue | Out-Null

Restart-Service 'MSSQL$SQLEXPRESS01' -Force
Test-NetConnection 127.0.0.1 -Port 1433 | Select-Object TcpTestSucceeded
