# Called automatically by Vagrant trigger.ruby — do not run manually.
param(
    [string]$RepoRoot = (Split-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent) -Parent)
)

$ErrorActionPreference = 'Continue'
$Marker = '# nano-devops-auto'
$Domains = @(
    'odoo.nano.platform', 'ai.nano.platform', 'grafana.nano.platform',
    'prometheus.nano.platform', 'aggregator.nano.platform', 'faulty.nano.platform',
    'data.nano.platform', 'health.nano.platform', 'user.nano.platform',
    'crm-ingest.nano.platform', 'crm-demo.nano.platform', 'goclaw.nano.platform',
    'shopee-search.nano.platform', 'shopee-api.nano.platform'
)
$FallbackIp = '192.168.157.10'

Set-Location $RepoRoot

function Get-VmIp {
    Write-Host '[nano] Getting VM IP...'
    $out = & vagrant ssh -c "cat /opt/platform/vm-service-ip 2>/dev/null" 2>&1
    Write-Host "[nano] VM IP output: $out"
    $line = ($out | Out-String).Trim() -split "`r?`n" |
        Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' } | Select-Object -Last 1
    if ($line) { return $line.Trim() }
    Write-Host "[nano] Using fallback IP: $FallbackIp"
    return $FallbackIp
}

# Re-launch elevated for hosts + certutil
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host '[nano] Requesting admin (UAC) for hosts + HTTPS CA...'
    $arg = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -RepoRoot `"$RepoRoot`""
    Start-Process powershell.exe -Verb RunAs -ArgumentList $arg -Wait
    exit $LASTEXITCODE
}

$ip = Get-VmIp
Write-Host "[nano] VM IP: $ip"

$hostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
Write-Host "[nano] Updating hosts file at $hostsPath..."
$lines = @(Get-Content $hostsPath -ErrorAction SilentlyContinue | Where-Object { $_ -notmatch [regex]::Escape($Marker) })
$newBlock = @($Marker) + ($Domains | ForEach-Object { "$ip $_ $Marker" })
Set-Content -Path $hostsPath -Value ($lines + $newBlock) -Encoding ASCII
Write-Host '[nano] hosts updated'

$caTmp = Join-Path $env:TEMP 'nano-rootCA.crt'
Write-Host "[nano] Fetching root CA from VM..."
$caOut = & vagrant ssh -c "cat /opt/platform/config/traefik/certs/rootCA.crt 2>/dev/null" 2>&1 | Out-String
Write-Host "[nano] Root CA output length: $($caOut.Length)"
if ($caOut -match '-----BEGIN CERTIFICATE-----') {
    $start = $caOut.IndexOf('-----BEGIN CERTIFICATE-----')
    $end = $caOut.IndexOf('-----END CERTIFICATE-----') + '-----END CERTIFICATE-----'.Length
    $certContent = $caOut.Substring($start, $end - $start)
    Write-Host "[nano] Extracted cert content, saving to $caTmp..."
    $certContent | Set-Content $caTmp -Encoding ASCII
    Write-Host "[nano] Importing root CA into Windows Trusted Root store..."
    $certutilOut = & certutil -addstore -f Root $caTmp 2>&1
    Write-Host "[nano] certutil output: $certutilOut"
    Write-Host '[nano] root CA trusted'
} else {
    Write-Host '[nano] WARNING: Could not find root CA certificate in VM output!'
    Write-Host "[nano] VM output: $caOut"
}

Write-Host '[nano] Waiting for platform (up to 20 min)...'
$ready = $false
for ($i = 0; $i -lt 120; $i++) {
    $chk = & vagrant ssh -c "test -f /opt/platform/.platform-ready && echo READY" 2>&1 | Out-String
    if ($chk -match 'READY') { $ready = $true; break }
    Start-Sleep -Seconds 10
}
if ($ready) {
    Write-Host '[nano] Opening CRM + Odoo'
    Start-Process 'https://crm-demo.nano.platform'
    Start-Sleep -Seconds 2
    Start-Process 'https://odoo.nano.platform'
} else {
    Write-Host '[nano] Still booting — try https://crm-demo.nano.platform later'
    Write-Host '[nano] vagrant ssh -c "tail -f /var/log/nano-post-up.log"'
}
