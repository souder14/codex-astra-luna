[CmdletBinding()]
param(
    [string]$CodexHome,
    [ValidateSet('before','after')][string]$Phase = 'before',
    [string]$Timestamp = (Get-Date -Format 'yyyyMMdd-HHmmss')
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'This snapshot tool requires Windows. See SETUP.md for other platforms.' }
if ($Timestamp -notmatch '^\d{8}-\d{6}$') { throw 'Timestamp must be YYYYMMDD-HHMMSS.' }
if (-not $CodexHome) {
    $CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
}
$root = [IO.Path]::GetFullPath($CodexHome)
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw "Codex home not found: $root" }
$version = (& codex --version | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot determine Codex version.' }
$helpText = (& codex --help | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'Cannot read Codex help.' }
$backup = Join-Path $root "backups/astra-luna-$Phase-$Timestamp"
if (Test-Path -LiteralPath $backup) { throw "Refusing to overwrite snapshot: $backup" }
New-Item -ItemType Directory -Path $backup | Out-Null
$acl = New-Object System.Security.AccessControl.DirectorySecurity
$acl.SetAccessRuleProtection($true,$false)
$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow')))
(New-Object System.IO.DirectoryInfo($backup)).SetAccessControl($acl)
if (-not (Get-Acl $backup).AreAccessRulesProtected) { throw 'Backup ACL protection failed.' }
$names = @('config.toml','AGENTS.md','AGENTS.override.md','agents/luna-worker.toml','skills/astra-luna/SKILL.md','skills/astra-luna/agents/openai.yaml')
$entries = @()
foreach ($name in $names) {
    $source = Join-Path $root $name
    # Reject junctions/symlinks on every existing component inside Codex home.
    $cursor = $source
    while ($cursor -ne $root -and $cursor.Length -gt $root.Length) {
        if (Test-Path -LiteralPath $cursor) {
            if ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Refusing reparse path: $cursor" }
        }
        $cursor = Split-Path $cursor -Parent
    }
    $exists = Test-Path -LiteralPath $source -PathType Leaf
    if ((Test-Path -LiteralPath $source) -and -not $exists) { throw "Expected regular file: $source" }
    $entry = [ordered]@{name=$name; existed=$exists; introduced=$false}
    if ($exists) {
        $item = Get-Item -LiteralPath $source
        $entry.sddl = (Get-Acl -LiteralPath $source).Sddl
        $entry.lastWriteTimeUtc = $item.LastWriteTimeUtc.ToString('o')
        $entry.creationTimeUtc = $item.CreationTimeUtc.ToString('o')
        $entry.attributes = [int]$item.Attributes
        $dest = Join-Path $backup $name
        New-Item -ItemType Directory -Path (Split-Path $dest) -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $dest
        $entry.sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        if ($entry.sha256 -ne (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash) { throw "Backup mismatch: $name" }
    }
    $entries += [pscustomobject]$entry
}
$manifest = [ordered]@{timestamp=$Timestamp; phase=$Phase; codexVersion=$version; codexHome=$root; activeProfile='Agent must record profile/precedence audit in environment.json'; files=$entries}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $backup 'snapshot.json') -Encoding UTF8
$entries | ForEach-Object { if ($_.existed) { "$($_.sha256)  $($_.name)" } } | Set-Content (Join-Path $backup "CHECKSUMS.$Phase.txt")
@("Timestamp: $Timestamp", "Codex: $version", "CODEX_HOME: $root", 'ACLs and original metadata: snapshot.json', 'Record active profile, managed requirements and project precedence in environment.json.') + @($entries | ForEach-Object { "$($_.name): existed=$($_.existed)" }) | Set-Content (Join-Path $backup 'BACKUP_MANIFEST.txt')
$helpText | Set-Content (Join-Path $backup 'codex-help.txt')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'restore.ps1') -Destination (Join-Path $backup 'restore.ps1')
& (Join-Path $backup 'restore.ps1') -VerifyOnly
Write-Output "Backup directory: $backup"
Write-Output "Rollback: powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$backup\restore.ps1`""
