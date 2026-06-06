# run_AEB_fixed.ps1
# Re-runs AEB scenarios with corrected obstacle positions
# Run from any directory

$e = "C:\esmini\bin\esmini"
$d = "C:\esmini\bin\dat2csv"
$r = "C:\adas-thesis\results\raw"
$s = "C:\adas-thesis\scenarios\S_results\AEB"

Write-Host "Running S_AEB_dry_50kph.xosc..." -ForegroundColor Cyan
& $e --osc "$s\S_AEB_dry_50kph.xosc" --fixed_timestep 0.05 --headless --record "$r\S_AEB_dry_50kph.dat"
& $d "$r\S_AEB_dry_50kph.dat" "$r\S_AEB_dry_50kph.csv"
Write-Host "Done: S_AEB_dry_50kph.xosc" -ForegroundColor Green

Write-Host "Running S_AEB_dry_80kph.xosc..." -ForegroundColor Cyan
& $e --osc "$s\S_AEB_dry_80kph.xosc" --fixed_timestep 0.05 --headless --record "$r\S_AEB_dry_80kph.dat"
& $d "$r\S_AEB_dry_80kph.dat" "$r\S_AEB_dry_80kph.csv"
Write-Host "Done: S_AEB_dry_80kph.xosc" -ForegroundColor Green

Write-Host "Running S_AEB_dry_120kph.xosc..." -ForegroundColor Cyan
& $e --osc "$s\S_AEB_dry_120kph.xosc" --fixed_timestep 0.05 --headless --record "$r\S_AEB_dry_120kph.dat"
& $d "$r\S_AEB_dry_120kph.dat" "$r\S_AEB_dry_120kph.csv"
Write-Host "Done: S_AEB_dry_120kph.xosc" -ForegroundColor Green

Write-Host "Running S_AEB_damp_50kph.xosc..." -ForegroundColor Cyan
& $e --osc "$s\S_AEB_damp_50kph.xosc" --fixed_timestep 0.05 --headless --record "$r\S_AEB_damp_50kph.dat"
& $d "$r\S_AEB_damp_50kph.dat" "$r\S_AEB_damp_50kph.csv"
Write-Host "Done: S_AEB_damp_50kph.xosc" -ForegroundColor Green

Write-Host "Running S_AEB_damp_80kph.xosc..." -ForegroundColor Cyan
& $e --osc "$s\S_AEB_damp_80kph.xosc" --fixed_timestep 0.05 --headless --record "$r\S_AEB_damp_80kph.dat"
& $d "$r\S_AEB_damp_80kph.dat" "$r\S_AEB_damp_80kph.csv"
Write-Host "Done: S_AEB_damp_80kph.xosc" -ForegroundColor Green

Write-Host "Running S_AEB_damp_120kph.xosc..." -ForegroundColor Cyan
& $e --osc "$s\S_AEB_damp_120kph.xosc" --fixed_timestep 0.05 --headless --record "$r\S_AEB_damp_120kph.dat"
& $d "$r\S_AEB_damp_120kph.dat" "$r\S_AEB_damp_120kph.csv"
Write-Host "Done: S_AEB_damp_120kph.xosc" -ForegroundColor Green

Write-Host "Running S_AEB_wet_50kph.xosc..." -ForegroundColor Cyan
& $e --osc "$s\S_AEB_wet_50kph.xosc" --fixed_timestep 0.05 --headless --record "$r\S_AEB_wet_50kph.dat"
& $d "$r\S_AEB_wet_50kph.dat" "$r\S_AEB_wet_50kph.csv"
Write-Host "Done: S_AEB_wet_50kph.xosc" -ForegroundColor Green

Write-Host "Running S_AEB_wet_80kph.xosc..." -ForegroundColor Cyan
& $e --osc "$s\S_AEB_wet_80kph.xosc" --fixed_timestep 0.05 --headless --record "$r\S_AEB_wet_80kph.dat"
& $d "$r\S_AEB_wet_80kph.dat" "$r\S_AEB_wet_80kph.csv"
Write-Host "Done: S_AEB_wet_80kph.xosc" -ForegroundColor Green

Write-Host "Running S_AEB_wet_120kph.xosc..." -ForegroundColor Cyan
& $e --osc "$s\S_AEB_wet_120kph.xosc" --fixed_timestep 0.05 --headless --record "$r\S_AEB_wet_120kph.dat"
& $d "$r\S_AEB_wet_120kph.dat" "$r\S_AEB_wet_120kph.csv"
Write-Host "Done: S_AEB_wet_120kph.xosc" -ForegroundColor Green

Write-Host "Running S_AEB_icy_50kph.xosc..." -ForegroundColor Cyan
& $e --osc "$s\S_AEB_icy_50kph.xosc" --fixed_timestep 0.05 --headless --record "$r\S_AEB_icy_50kph.dat"
& $d "$r\S_AEB_icy_50kph.dat" "$r\S_AEB_icy_50kph.csv"
Write-Host "Done: S_AEB_icy_50kph.xosc" -ForegroundColor Green

Write-Host "Running S_AEB_icy_80kph.xosc..." -ForegroundColor Cyan
& $e --osc "$s\S_AEB_icy_80kph.xosc" --fixed_timestep 0.05 --headless --record "$r\S_AEB_icy_80kph.dat"
& $d "$r\S_AEB_icy_80kph.dat" "$r\S_AEB_icy_80kph.csv"
Write-Host "Done: S_AEB_icy_80kph.xosc" -ForegroundColor Green

Write-Host "Running S_AEB_icy_120kph.xosc..." -ForegroundColor Cyan
& $e --osc "$s\S_AEB_icy_120kph.xosc" --fixed_timestep 0.05 --headless --record "$r\S_AEB_icy_120kph.dat"
& $d "$r\S_AEB_icy_120kph.dat" "$r\S_AEB_icy_120kph.csv"
Write-Host "Done: S_AEB_icy_120kph.xosc" -ForegroundColor Green

Write-Host "All AEB scenarios complete." -ForegroundColor Yellow