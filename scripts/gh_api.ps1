# GitHub API 호출 헬퍼
# Usage: . .\scripts\gh_api.ps1   (dot-source로 함수 로드)

function Load-Env {
    $envFile = Join-Path $PSScriptRoot "..\.env"
    if (-not (Test-Path $envFile)) {
        throw ".env 파일이 없습니다. .env.example을 복사해 작성하세요."
    }
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.+)$") {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

function Invoke-GhApi {
    param(
        [string]$Method = "GET",
        [string]$Endpoint,   # e.g. "/issues"
        [hashtable]$Body = @{}
    )

    Load-Env

    $token = $env:GITHUB_TOKEN
    $repo  = $env:GITHUB_REPO

    $headers = @{
        "Authorization"        = "Bearer $token"
        "Accept"               = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }

    $uri = "https://api.github.com/repos/$repo$Endpoint"

    if ($Method -eq "GET") {
        return Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers
    }

    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes(($Body | ConvertTo-Json -Depth 5))
    return Invoke-RestMethod -Uri $uri -Method $Method -Headers $headers `
        -Body $bodyBytes -ContentType "application/json; charset=utf-8"
}
