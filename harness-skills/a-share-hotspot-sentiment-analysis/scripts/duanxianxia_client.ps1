[CmdletBinding()]
param(
    [switch]$ListDatasets,

    [ValidateSet(
        'datasource',
        'hotlist',
        'jinjidata',
        'ztlive',
        'ztplate',
        'ztcount',
        'ztpool',
        'platechart1',
        'platechart2',
        'amount'
    )]
    [string[]]$Dataset,

    [string]$InputSnapshot,

    [string]$Output
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

[Net.ServicePointManager]::SecurityProtocol =
    [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

$siteOrigin = 'https://duanxianxia.com'
$datasourceUrl = "$siteOrigin/vendor/stockdata/datasource.json"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$datasetDefinitions = [ordered]@{
    datasource = [ordered]@{
        description = 'Site data source configuration'
        method = 'GET'
        location = 'datasource'
        path = ''
        encrypted = $false
    }
    hotlist = [ordered]@{
        description = 'Hot stock list'
        method = 'GET'
        location = 'absolute'
        path = 'https://x.duanxianxia.cn/vendor/stockdata/hotlist.json'
        encrypted = $false
    }
    jinjidata = [ordered]@{
        description = 'Promotion data'
        method = 'GET'
        location = 'data'
        path = '/vendor/stockdata/jinjidata.json'
        encrypted = $false
    }
    ztlive = [ordered]@{
        description = 'Limit-up live feed'
        method = 'GET'
        location = 'site'
        path = '/vendor/stockdata/ztlive.json'
        encrypted = $false
    }
    ztplate = [ordered]@{
        description = 'Limit-up sectors'
        method = 'GET'
        location = 'data'
        path = '/vendor/stockdata/ztplate.json'
        encrypted = $false
    }
    ztcount = [ordered]@{
        description = 'Limit-up count'
        method = 'GET'
        location = 'site'
        path = '/vendor/stockdata/ztcount.json'
        encrypted = $false
    }
    ztpool = [ordered]@{
        description = 'Limit-up pool'
        method = 'GET'
        location = 'data'
        path = '/vendor/stockdata/ztpool.json'
        encrypted = $true
    }
    platechart1 = [ordered]@{
        description = 'Sector chart 1'
        method = 'GET'
        location = 'data'
        path = '/vendor/stockdata/platechart1.json'
        encrypted = $true
    }
    platechart2 = [ordered]@{
        description = 'Sector chart 2'
        method = 'GET'
        location = 'site'
        path = '/vendor/stockdata/platechart2.json'
        encrypted = $true
    }
    amount = [ordered]@{
        description = 'Current market turnover'
        method = 'POST'
        location = 'site'
        path = '/api/getLastAmount'
        encrypted = $false
    }
}

if ($ListDatasets) {
    foreach ($name in $datasetDefinitions.Keys) {
        $definition = $datasetDefinitions[$name]
        [pscustomobject]@{
            Dataset = $name
            Description = $definition.description
            Method = $definition.method
            Encrypted = $definition.encrypted
        }
    }
    return
}

function Get-SecFetchSite {
    param([Parameter(Mandatory = $true)][string]$Uri)

    $hostName = ([Uri]$Uri).DnsSafeHost
    if ($hostName -eq 'duanxianxia.com') {
        return 'same-origin'
    }
    if ($hostName.EndsWith('.duanxianxia.com', [StringComparison]::OrdinalIgnoreCase)) {
        return 'same-site'
    }
    return 'cross-site'
}

function Invoke-DuanxianxiaRequest {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [ValidateSet('GET', 'POST')][string]$Method = 'GET'
    )

    $headers = @{
        Accept = 'application/json, text/javascript, */*; q=0.01'
        'Accept-Language' = 'zh-CN,zh;q=0.9'
        Referer = "$siteOrigin/web/main"
        'X-Requested-With' = 'XMLHttpRequest'
        'Sec-Fetch-Dest' = 'empty'
        'Sec-Fetch-Mode' = 'cors'
        'Sec-Fetch-Site' = Get-SecFetchSite -Uri $Uri
        'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
    }

    $requestParameters = @{
        Uri = $Uri
        Method = $Method
        Headers = $headers
        UseBasicParsing = $true
        TimeoutSec = 30
        MaximumRedirection = 5
    }

    $response = Invoke-WebRequest @requestParameters
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
        throw "HTTP $($response.StatusCode): $Uri"
    }

    $rawBytes = $response.RawContentStream.ToArray()
    $utf8 = [Text.UTF8Encoding]::new($false, $true)
    $content = $utf8.GetString($rawBytes)
    if ($content.Length -gt 0 -and $content[0] -eq [char]0xFEFF) {
        $content = $content.Substring(1)
    }

    return [pscustomobject]@{
        StatusCode = [int]$response.StatusCode
        Content = $content
        ContentLength = [int64]$rawBytes.LongLength
    }
}

function ConvertFrom-LooseBase64 {
    param([Parameter(Mandatory = $true)][string]$Value)

    $normalized = $Value.Trim().TrimEnd('=')
    $remainder = $normalized.Length % 4
    if ($remainder -ne 0) {
        $normalized += '=' * (4 - $remainder)
    }
    return [Convert]::FromBase64String($normalized)
}

function ConvertFrom-DuanxianxiaEncryptedJson {
    param([Parameter(Mandatory = $true)][string]$Payload)

    $cipherText = $Payload.Trim()
    if ($cipherText.StartsWith('"') -and $cipherText.EndsWith('"')) {
        $cipherText = $cipherText | ConvertFrom-Json
    }

    $key = ConvertFrom-LooseBase64 -Value 'c2VjcmV0a2V5MzIyeWVzISFhYWFhYWFhYWFhYWFhYWE===='
    $iv = ConvertFrom-LooseBase64 -Value 'Zml4ZWRpdl8xNnZhbHVlZA=='
    $encryptedBytes = ConvertFrom-LooseBase64 -Value $cipherText

    $aes = [System.Security.Cryptography.Aes]::Create()
    try {
        $aes.KeySize = 256
        $aes.BlockSize = 128
        $aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
        $aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
        $aes.Key = $key
        $aes.IV = $iv

        $decryptor = $aes.CreateDecryptor()
        try {
            $plainBytes = $decryptor.TransformFinalBlock($encryptedBytes, 0, $encryptedBytes.Length)
            return [Text.Encoding]::UTF8.GetString($plainBytes)
        }
        finally {
            $decryptor.Dispose()
        }
    }
    finally {
        $aes.Dispose()
    }
}

function Resolve-DataBaseUrl {
    param([Parameter(Mandatory = $true)]$Datasource)

    if ([int]$Datasource.istrade -eq 1 -and -not [string]::IsNullOrWhiteSpace([string]$Datasource.data_url)) {
        return ([string]$Datasource.data_url).TrimEnd('/')
    }

    $baseUrls = @($Datasource.base_url)
    if ($baseUrls.Count -eq 0 -or [string]::IsNullOrWhiteSpace([string]$baseUrls[0])) {
        throw 'datasource.json did not provide a usable data_url or base_url.'
    }
    return ([string]$baseUrls[0]).TrimEnd('/')
}

function Resolve-DatasetUrl {
    param(
        [Parameter(Mandatory = $true)]$Definition,
        [Parameter(Mandatory = $true)][string]$DataBaseUrl
    )

    switch ($Definition.location) {
        'datasource' { return $datasourceUrl }
        'absolute' { return [string]$Definition.path }
        'site' { return "$siteOrigin$($Definition.path)" }
        'data' { return "$DataBaseUrl$($Definition.path)" }
        default { throw "Unknown data location type: $($Definition.location)" }
    }
}

$selectedDatasets = if ($Dataset -and $Dataset.Count -gt 0) {
    @($Dataset | Select-Object -Unique)
}
else {
    @($datasetDefinitions.Keys)
}

if ([string]::IsNullOrWhiteSpace($InputSnapshot) -and $env:CODEX_DUANXIANXIA_STATUS -eq 'CLEAN_PASS') {
    $InputSnapshot = $env:CODEX_DUANXIANXIA_SNAPSHOT
}

if (-not [string]::IsNullOrWhiteSpace($InputSnapshot)) {
    $inputPath = [IO.Path]::GetFullPath($InputSnapshot)
    if (-not [IO.File]::Exists($inputPath)) {
        throw "Inherited Duanxianxia snapshot is missing: $inputPath"
    }
    $inherited = [IO.File]::ReadAllText($inputPath, [Text.Encoding]::UTF8) | ConvertFrom-Json
    if ($inherited.source_page -ne "$siteOrigin/web/main" -or $inherited.access_scope -ne 'public HTTP data only; no browser credentials exported') {
        throw 'Inherited Duanxianxia snapshot source boundary is invalid.'
    }
    $inheritedResults = [ordered]@{}
    foreach ($name in $selectedDatasets) {
        $property = $inherited.datasets.PSObject.Properties[$name]
        if ($null -eq $property -or $property.Value.success -ne $true) {
            throw "Inherited Duanxianxia dataset is unavailable: $name"
        }
        $inheritedResults[$name] = $property.Value
    }
    if ([string]::IsNullOrWhiteSpace($Output)) {
        $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $Output = Join-Path $scriptRoot "outputs\duanxianxia_snapshot_$timestamp.json"
    }
    elseif (-not [IO.Path]::IsPathRooted($Output)) {
        $Output = Join-Path (Get-Location) $Output
    }
    $outputDirectory = Split-Path -Parent $Output
    if (-not [string]::IsNullOrWhiteSpace($outputDirectory)) {
        [IO.Directory]::CreateDirectory($outputDirectory) | Out-Null
    }
    $snapshot = [ordered]@{
        generated_at = $inherited.generated_at
        source_page = $inherited.source_page
        access_scope = $inherited.access_scope
        datasource = $inherited.datasource
        selected_datasets = $selectedDatasets
        datasets = $inheritedResults
        reuse = [ordered]@{
            mode = 'current_task_inherited_snapshot'
            source_path = $inputPath
        }
    }
    $jsonOutput = $snapshot | ConvertTo-Json -Depth 100
    [IO.File]::WriteAllText($Output, $jsonOutput, (New-Object Text.UTF8Encoding($false)))
    [pscustomobject]@{
        Output = [IO.Path]::GetFullPath($Output)
        DataBaseUrl = [string]$inherited.datasource.data_url
        DatasetCount = @($selectedDatasets).Count
        SuccessCount = @($selectedDatasets).Count
        FailedCount = 0
        Reused = $true
    }
    return
}

$datasourceResponse = Invoke-DuanxianxiaRequest -Uri $datasourceUrl -Method GET
$datasourceObject = $datasourceResponse.Content | ConvertFrom-Json
$dataBaseUrl = Resolve-DataBaseUrl -Datasource $datasourceObject
$disableCache = [int]$datasourceObject.nocache -eq 1

$results = [ordered]@{}
$hasErrors = $false

foreach ($name in $selectedDatasets) {
    $definition = $datasetDefinitions[$name]
    $requestUrl = Resolve-DatasetUrl -Definition $definition -DataBaseUrl $dataBaseUrl
    if ($disableCache -and $name -ne 'datasource') {
        $separator = if ($requestUrl.Contains('?')) { '&' } else { '?' }
        $requestUrl = "$requestUrl${separator}_t=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())"
    }

    try {
        $fetchedAt = [DateTimeOffset]::Now.ToString('o')
        if ($name -eq 'datasource') {
            $response = $datasourceResponse
            $jsonText = $datasourceResponse.Content
        }
        else {
            $response = Invoke-DuanxianxiaRequest -Uri $requestUrl -Method $definition.method
            $jsonText = if ($definition.encrypted) {
                ConvertFrom-DuanxianxiaEncryptedJson -Payload $response.Content
            }
            else {
                $response.Content
            }
        }

        $parsedData = $jsonText | ConvertFrom-Json
        $results[$name] = [ordered]@{
            success = $true
            fetched_at = $fetchedAt
            url = $requestUrl
            method = $definition.method
            status_code = $response.StatusCode
            content_length = $response.ContentLength
            encrypted = [bool]$definition.encrypted
            data = $parsedData
        }
    }
    catch {
        $hasErrors = $true
        $results[$name] = [ordered]@{
            success = $false
            fetched_at = [DateTimeOffset]::Now.ToString('o')
            url = $requestUrl
            method = $definition.method
            status_code = $null
            content_length = $null
            encrypted = [bool]$definition.encrypted
            error = $_.Exception.Message
        }
    }
}

if ([string]::IsNullOrWhiteSpace($Output)) {
    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $Output = Join-Path $scriptRoot "outputs\duanxianxia_snapshot_$timestamp.json"
}
elseif (-not [IO.Path]::IsPathRooted($Output)) {
    $Output = Join-Path (Get-Location) $Output
}

$outputDirectory = Split-Path -Parent $Output
if (-not [string]::IsNullOrWhiteSpace($outputDirectory)) {
    [IO.Directory]::CreateDirectory($outputDirectory) | Out-Null
}

$snapshot = [ordered]@{
    generated_at = [DateTimeOffset]::Now.ToString('o')
    source_page = "$siteOrigin/web/main"
    access_scope = 'public HTTP data only; no browser credentials exported'
    datasource = $datasourceObject
    selected_datasets = $selectedDatasets
    datasets = $results
}

$jsonOutput = $snapshot | ConvertTo-Json -Depth 100
[IO.File]::WriteAllText($Output, $jsonOutput, (New-Object Text.UTF8Encoding($false)))

$successCount = @($results.Values | Where-Object { $_.success }).Count
$failedCount = @($results.Values | Where-Object { -not $_.success }).Count

[pscustomobject]@{
    Output = [IO.Path]::GetFullPath($Output)
    DataBaseUrl = $dataBaseUrl
    DatasetCount = @($selectedDatasets).Count
    SuccessCount = $successCount
    FailedCount = $failedCount
}

if ($hasErrors) {
    exit 1
}
