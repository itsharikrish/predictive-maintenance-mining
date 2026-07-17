# fix_frontend_structure.ps1
# Fixes Next.js structure by moving frontend/page.tsx -> frontend/app/page.tsx
# Run this from the main project folder.

$frontend = Join-Path $PWD "frontend"
$appDir = Join-Path $frontend "app"
$rootPage = Join-Path $frontend "page.tsx"
$appPage = Join-Path $appDir "page.tsx"

if (-not (Test-Path $frontend)) {
    Write-Host "Error: frontend folder not found in current directory."
    exit 1
}

if (-not (Test-Path $appDir)) {
    New-Item -ItemType Directory -Path $appDir | Out-Null
    Write-Host "Created folder: frontend/app"
}

if ((Test-Path $rootPage) -and (-not (Test-Path $appPage))) {
    Move-Item $rootPage $appPage
    Write-Host "Moved frontend/page.tsx -> frontend/app/page.tsx"
} elseif (Test-Path $appPage) {
    Write-Host "frontend/app/page.tsx already exists. No move needed."
} else {
    Write-Host "Could not find frontend/page.tsx. Please check your project files."
}

Write-Host "Done. Now run:"
Write-Host "git add ."
Write-Host "git commit -m 'fix nextjs app folder structure'"
Write-Host "git push"
