$ErrorActionPreference = 'Stop'
$sourcePath = Join-Path $PSScriptRoot '../../a.sh'
$source = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $sourcePath))
$match = [regex]::Match($source, '(?s)function Initialize-LlamaFileRanker \{.*?\r?\n\}\r?\n\r?\nswitch \(\$Action\)')
if (-not $match.Success) { throw 'Embedded ranker not found' }
$functionSource = $match.Value.Substring(0, $match.Value.LastIndexOf('switch ($Action)'))
. ([scriptblock]::Create($functionSource))
Initialize-LlamaFileRanker
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('nature-ranker-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($fixture) | Out-Null
$originalOut = [Console]::Out
try {
    $nested = Join-Path $fixture 'nested folder'
    [IO.Directory]::CreateDirectory($nested) | Out-Null
    $sizes = New-Object 'System.Collections.Generic.List[long]'
    for ($i = 0; $i -lt 5000; $i++) {
        $size = ($i * 97) % 1009
        $parent = if ($i % 2) { $nested } else { $fixture }
        [IO.File]::WriteAllBytes((Join-Path $parent ('file-{0:D5}.bin' -f $i)), (New-Object byte[] $size))
        $sizes.Add($size)
    }
    $capture = New-Object IO.StringWriter
    [Console]::SetOut($capture)
    $clock = [Diagnostics.Stopwatch]::StartNew()
    [NatureFileRanker]::Run([string[]]@($fixture), 100)
    $clock.Stop()
    [Console]::SetOut($originalOut)
    $rows = @($capture.ToString() -split '\r?\n' | Where-Object { $_ -match '^.+\|\d+\|[\d.,]+ GB$' })
    if ($rows.Count -ne 100) { throw "Expected 100 rows, got $($rows.Count)" }
    $expected = @($sizes | Sort-Object -Descending | Select-Object -First 100)
    for ($i = 0; $i -lt 100; $i++) {
        $fields = $rows[$i] -split '\|'
        if ([long]$fields[1] -ne $expected[$i]) { throw "Wrong ranking at $i" }
        if (([IO.FileInfo]$fields[0]).Length -ne [long]$fields[1]) { throw 'Reported size differs from file' }
    }
    if ($capture.ToString() -notmatch 'files=5000\|errors=0') { throw 'Incomplete scan counters' }
    $missing = New-Object IO.StringWriter
    [Console]::SetOut($missing)
    [NatureFileRanker]::Run([string[]]@((Join-Path $fixture 'missing')), 10)
    [Console]::SetOut($originalOut)
    if ($missing.ToString() -notmatch 'errors=1') { throw 'Missing directory must not be silently treated as a complete scan' }
    Write-Output ('NATURE_FILE_RANKER_OK files=5000 top=100 scan_ms={0}' -f $clock.ElapsedMilliseconds)
} finally {
    [Console]::SetOut($originalOut)
    $resolved = [IO.Path]::GetFullPath($fixture)
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if ($resolved.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -and [IO.Path]::GetFileName($resolved).StartsWith('nature-ranker-')) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
