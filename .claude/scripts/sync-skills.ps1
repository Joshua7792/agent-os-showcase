<#
.SYNOPSIS
  Keeps the OS skill/agent library complete, its twin identical, and every skill a real folder.

.DESCRIPTION
  Layout: root .claude/skills + .claude/agents are the global library;
  root .agents/ is its identical twin (Codex and other agents read it); each project keeps real copies of
  the skills/agents it uses. This script checks, and with -Fix repairs, the safe cases:
    1. a skill that is a shortcut (symlink/junction)  -> replaced by a real copy of its target
    2. a project skill/agent missing from the library -> copied into root .claude/
    3. an item in only one of .claude/ and .agents/   -> copied to the other
  and only REPORTS what needs a human decision (it never overwrites content):
    4. the same item differing between .claude/ and .agents/
    5. a project copy differing from the library copy
  Snapshot folders (*/raw/*, */archive/*) are history and skipped. Exit code 1 = issues left.
  Install new skills with `npx skills add <repo> --copy` so step 1 never has work to do.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .claude/scripts/sync-skills.ps1        # report only
  powershell -ExecutionPolicy Bypass -File .claude/scripts/sync-skills.ps1 -Fix   # repair, then commit
#>
[CmdletBinding()]
param([switch]$Fix, [string]$Root = (git rev-parse --show-toplevel))

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8   # read git's UTF-8 path output correctly
$Root = (Resolve-Path -LiteralPath $Root).Path
$skip = '/raw/|/archive/|node_modules/'
$lib = @{ skills = @('.claude/skills', '.agents/skills'); agents = @('.claude/agents', '.agents/agents') }
$script:todo = 0

function Get-Items {
  $paths = @(git -C $Root -c core.quotepath=off ls-files) + @(git -C $Root -c core.quotepath=off ls-files -o --exclude-standard)
  $seen = @{}
  foreach ($p in $paths) {
    if ($p -match $skip) { continue }
    if ($p -match '^((?:.*/)?\.(?:claude|agents|codex)/skills)/([^/]+)') { $kind = 'skills' }
    elseif ($p -match '^((?:.*/)?\.(?:claude|agents)/agents)/([^/]+\.md)$') { $kind = 'agents' }
    else { continue }
    $rel = "$($Matches[1])/$($Matches[2])"
    if (-not $seen.ContainsKey($rel)) {
      $seen[$rel] = [pscustomobject]@{ Kind = $kind; Base = $Matches[1]; Name = $Matches[2]; Rel = $rel; Path = Join-Path $Root $rel }
    }
  }
  # a skill is a folder (loose files such as licences are not skills)
  @($seen.Values | Where-Object { $_.Kind -eq 'agents' -or (Test-Path -LiteralPath $_.Path -PathType Container) })
}

function Get-Fingerprints($items) {
  # git's own blob hash (line endings normalised), one call for every file, so CRLF vs LF is never a change
  $files = @(foreach ($it in $items) {
    if ($it.Kind -eq 'agents') { [pscustomobject]@{ Rel = $it.Rel; Sub = ''; Full = $it.Path } }
    else {
      Get-ChildItem -LiteralPath $it.Path -Recurse -File -Force |
        ForEach-Object { [pscustomobject]@{ Rel = $it.Rel; Sub = $_.FullName.Substring($it.Path.Length); Full = $_.FullName } }
    }
  }) | Sort-Object Rel, Sub
  $fp = @{}
  if (-not $files) { return $fp }
  # repo-relative paths go as arguments (piping them in PowerShell 5.1 can prepend a BOM that git rejects),
  # batched by total length to stay well under Windows' 32k-character command-line limit
  $hashes = New-Object System.Collections.Generic.List[string]
  $batch = New-Object System.Collections.Generic.List[string]; $len = 0
  foreach ($f in $files) {
    $rel = $f.Full.Substring($Root.Length + 1)
    if ($batch.Count -and $len + $rel.Length -gt 20000) {
      $hashes.AddRange([string[]]@(git -C $Root hash-object -- $batch.ToArray())); $batch.Clear(); $len = 0
    }
    $batch.Add($rel); $len += $rel.Length + 3
  }
  if ($batch.Count) { $hashes.AddRange([string[]]@(git -C $Root hash-object -- $batch.ToArray())) }
  if ($hashes.Count -ne $files.Count) { throw "git hash-object returned $($hashes.Count) hashes for $($files.Count) files" }
  for ($i = 0; $i -lt $files.Count; $i++) { $fp[$files[$i].Rel] += "$($files[$i].Sub)=$($hashes[$i]);" }
  $fp
}

function Copy-Item2($from, $to) {
  New-Item -ItemType Directory -Force -Path (Split-Path $to) | Out-Null
  if (Test-Path -LiteralPath $from -PathType Container) { Copy-Item -LiteralPath $from -Destination $to -Recurse -Force }
  else { Copy-Item -LiteralPath $from -Destination $to -Force }
  Write-Output "FIXED  copied $($from.Substring($Root.Length + 1)) -> $($to.Substring($Root.Length + 1))"
}

# 1. shortcuts -> real folders
foreach ($it in (Get-Items | Where-Object Kind -eq 'skills')) {
  $item = Get-Item -Force -LiteralPath $it.Path
  if ($item.LinkType -notin 'SymbolicLink', 'Junction') { continue }
  $target = ($item.Target -join '')
  if (-not $Fix) { Write-Output "TODO   $($it.Rel) is a shortcut to $target"; $script:todo++; continue }
  [System.IO.Directory]::Delete($it.Path, $false)   # removes the link only; throws on a real folder
  Copy-Item -LiteralPath $target -Destination $it.Path -Recurse -Force
  Write-Output "FIXED  $($it.Rel) shortcut -> real folder"
}

# 2 + 3. missing from the library, or from one twin
foreach ($kind in 'skills', 'agents') {
  $main, $twin = $lib[$kind]
  $items = Get-Items | Where-Object Kind -eq $kind
  $inMain = @($items | Where-Object Base -eq $main | ForEach-Object Name)
  foreach ($it in ($items | Where-Object { $_.Base -notin $lib[$kind] -and $_.Name -notin $inMain } | Sort-Object Name -Unique)) {
    if ($Fix) { Copy-Item2 $it.Path (Join-Path $Root "$main/$($it.Name)"); $inMain += $it.Name }
    else { Write-Output "TODO   $($it.Rel) is not in the library ($main)"; $script:todo++ }
  }
  $inTwin = @($items | Where-Object Base -eq $twin | ForEach-Object Name)
  foreach ($pair in @(@($main, $twin, $inMain, $inTwin), @($twin, $main, $inTwin, $inMain))) {
    foreach ($name in ($pair[2] | Where-Object { $_ -notin $pair[3] })) {
      if ($Fix) { Copy-Item2 (Join-Path $Root "$($pair[0])/$name") (Join-Path $Root "$($pair[1])/$name") }
      else { Write-Output "TODO   $($pair[0])/$name is missing from $($pair[1])"; $script:todo++ }
    }
  }
}

# 4 + 5. content that differs: a person decides which copy is right
$items = Get-Items
$fp = Get-Fingerprints $items
$decide = 0
foreach ($it in ($items | Where-Object { $_.Base -ne $lib[$_.Kind][0] })) {
  $libRel = "$($lib[$it.Kind][0])/$($it.Name)"
  if (-not $fp.ContainsKey($libRel)) { continue }   # already reported as missing above
  if ($fp[$it.Rel] -ne $fp[$libRel]) {
    $what = if ($it.Base -eq $lib[$it.Kind][1]) { 'twin differs from' } else { 'project copy differs from' }
    Write-Output "DECIDE $($it.Rel) - $what $libRel (keep the right one, copy it over the other)"
    $decide++
  }
}
$left = $script:todo + $decide
Write-Output $(if ($left) { "done: $left item(s) need attention" } else { 'done: library complete, twins identical, no shortcuts, project copies current' })
exit [int]($left -gt 0)
