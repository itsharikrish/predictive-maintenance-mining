# add_next_root_layout.ps1
# Creates frontend/app/layout.tsx for Next.js App Router
# Run this from the main project folder.

$frontend = Join-Path $PWD "frontend"
$appDir = Join-Path $frontend "app"
$layoutFile = Join-Path $appDir "layout.tsx"

if (-not (Test-Path $frontend)) {
    Write-Host "Error: frontend folder not found in current directory."
    exit 1
}

if (-not (Test-Path $appDir)) {
    New-Item -ItemType Directory -Path $appDir | Out-Null
    Write-Host "Created folder: frontend/app"
}

$layoutContent = @'
export const metadata = {
  title: "Predictive Maintenance Dashboard",
  description: "Live sensor telemetry with ML-based failure-risk prediction",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
'@

Set-Content -Path $layoutFile -Value $layoutContent
Write-Host "Created/updated frontend/app/layout.tsx"
Write-Host "Done. Now run:"
Write-Host "git add ."
Write-Host "git commit -m 'add nextjs root layout'"
Write-Host "git push"
