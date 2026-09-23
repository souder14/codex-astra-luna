[CmdletBinding(SupportsShouldProcess=$true)]
param([switch]$Force, [switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
function Get-SnapshotHash([string]$FilePath) {
    # Windows PowerShell's Get-FileHash can inherit WhatIf in its internal
    # provider pipeline. Hashing is read-only and must still run during a dry run.
    $stream = [IO.File]::OpenRead($FilePath)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','') }
    finally { $sha.Dispose(); $stream.Dispose() }
}
$snapshot = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'snapshot.json') -Raw | ConvertFrom-Json
$root = [IO.Path]::GetFullPath($snapshot.codexHome).TrimEnd('\')
$allowed = @('config.toml','AGENTS.md','AGENTS.override.md','agents/luna-worker.toml','skills/astra-luna/SKILL.md','skills/astra-luna/agents/openai.yaml')
# Validate the entire snapshot before touching any live file.
foreach ($entry in $snapshot.files) {
    if ($entry.name -notin $allowed) { throw "Unexpected manifest path: $($entry.name)" }
    $target = [IO.Path]::GetFullPath((Join-Path $root $entry.name))
    if (-not $target.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "Unsafe target: $target" }
    $cursor = $target
    while ($cursor -ne $root -and $cursor.Length -gt $root.Length) {
        if (Test-Path -LiteralPath $cursor) {
            if ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Refusing reparse path: $cursor" }
        }
        $cursor = Split-Path $cursor -Parent
    }
    if ($entry.existed) {
        $source = Join-Path $PSScriptRoot $entry.name
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing backup: $source" }
        if ((Get-SnapshotHash $source) -ne $entry.sha256) { throw "Corrupt backup: $source" }
    }
}
if ($VerifyOnly) { Write-Output 'Snapshot verified; no live files changed.'; return }
if (-not $Force -and -not $WhatIfPreference) {
    if ((Read-Host "Restore this snapshot to $root? Type RESTORE to confirm") -cne 'RESTORE') { throw 'Restoration cancelled.' }
}
foreach ($entry in $snapshot.files) {
    $target = [IO.Path]::GetFullPath((Join-Path $root $entry.name))
    if ($entry.existed) {
        if ($PSCmdlet.ShouldProcess($target, 'Restore original file, timestamps and permissions')) {
            Copy-Item -LiteralPath (Join-Path $PSScriptRoot $entry.name) -Destination $target -Force
            if ((Get-SnapshotHash $target) -ne $entry.sha256) { throw "Restoration hash mismatch: $target" }
            $item = Get-Item -LiteralPath $target
            $item.CreationTimeUtc = [datetime]$entry.creationTimeUtc
            $item.LastWriteTimeUtc = [datetime]$entry.lastWriteTimeUtc
            $acl = Get-Acl -LiteralPath $target
            $acl.SetSecurityDescriptorSddlForm($entry.sddl)
            Set-Acl -LiteralPath $target -AclObject $acl
            $item.Attributes = [IO.FileAttributes]$entry.attributes
            Write-Output "Restored: $target"
        }
    } elseif (Test-Path -LiteralPath $target) {
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "Refusing to remove non-file: $target" }
        # Only remove files recorded as actually introduced by this migration.
        if ($entry.introduced -eq $true -and $PSCmdlet.ShouldProcess($target, 'Remove migration-created file')) {
            Remove-Item -LiteralPath $target -Force
            Write-Output "Removed migration-created file: $target"
        } elseif ($entry.introduced -ne $true) { Write-Output "Preserved unrelated later file: $target" }
    }
}
if ($WhatIfPreference) { Write-Output "Dry run complete; no live files changed. Snapshot retained at $PSScriptRoot" }
else { Write-Output "Restoration complete. Snapshot retained at $PSScriptRoot" }
