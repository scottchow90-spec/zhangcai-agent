# One immutable directory per product version. Rebuilds require a new version.
$releaseVersion = (Get-Content -LiteralPath (Join-Path $projectRoot 'package.json') -Raw -Encoding UTF8 | ConvertFrom-Json).version
if ($releaseVersion -notmatch '^\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?$') { throw 'Invalid release version.' }
$releaseRoot = Join-Path $projectRoot "dist-installer\releases\$releaseVersion"
New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null

function Assert-NewArtifact([string]$artifact) {
  if (Test-Path -LiteralPath $artifact) { throw "Refusing to overwrite an existing release: $artifact. Increment package.json version." }
}
