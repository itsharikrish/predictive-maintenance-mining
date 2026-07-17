# push_to_github.ps1
# Windows PowerShell version
# Usage: .\push_to_github.ps1 -Username "your-github-username" -RepoName "your-repo-name"

param(
    [Parameter(Mandatory=$true)][string]$Username,
    [Parameter(Mandatory=$true)][string]$RepoName
)

Write-Host "Initializing git repository..."
git init

Write-Host "Adding all files..."
git add .

Write-Host "Committing..."
git commit -m "first upload"

Write-Host "Setting main branch..."
git branch -M main

Write-Host "Adding remote origin..."
$remoteUrl = "https://github.com/$Username/$RepoName.git"
git remote remove origin -ErrorAction SilentlyContinue
git remote add origin $remoteUrl

Write-Host "Pushing to GitHub... (you will be prompted for username and a Personal Access Token, NOT your password)"
git push -u origin main

Write-Host "Done! Check https://github.com/$Username/$RepoName"
