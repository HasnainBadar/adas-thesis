# run_all_S_results.ps1
# Runs all 36 friction-aware result scenarios headless
# Run from C:\esmini directory
# PowerShell -ExecutionPolicy Bypass -File C:\adas-thesis\scenarios\S_results\run_all_S_results.ps1

$esmini = "C:\esmini\bin\esmini.exe"
$raw    = "C:\adas-thesis\results\raw"
$scen   = "C:\adas-thesis\scenarios\S_results"

Write-Host 'Running AEB scenarios...' -ForegroundColor Cyan
& $esmini --osc "$scen\AEB\S_AEB_dry_50kph.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_AEB_dry_50kph.dat"
Write-Host "Done: S_AEB_dry_50kph.xosc" -ForegroundColor Green
& $esmini --osc "$scen\AEB\S_AEB_dry_80kph.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_AEB_dry_80kph.dat"
Write-Host "Done: S_AEB_dry_80kph.xosc" -ForegroundColor Green
& $esmini --osc "$scen\AEB\S_AEB_dry_120kph.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_AEB_dry_120kph.dat"
Write-Host "Done: S_AEB_dry_120kph.xosc" -ForegroundColor Green
& $esmini --osc "$scen\AEB\S_AEB_damp_50kph.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_AEB_damp_50kph.dat"
Write-Host "Done: S_AEB_damp_50kph.xosc" -ForegroundColor Green
& $esmini --osc "$scen\AEB\S_AEB_damp_80kph.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_AEB_damp_80kph.dat"
Write-Host "Done: S_AEB_damp_80kph.xosc" -ForegroundColor Green
& $esmini --osc "$scen\AEB\S_AEB_damp_120kph.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_AEB_damp_120kph.dat"
Write-Host "Done: S_AEB_damp_120kph.xosc" -ForegroundColor Green
& $esmini --osc "$scen\AEB\S_AEB_wet_50kph.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_AEB_wet_50kph.dat"
Write-Host "Done: S_AEB_wet_50kph.xosc" -ForegroundColor Green
& $esmini --osc "$scen\AEB\S_AEB_wet_80kph.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_AEB_wet_80kph.dat"
Write-Host "Done: S_AEB_wet_80kph.xosc" -ForegroundColor Green
& $esmini --osc "$scen\AEB\S_AEB_wet_120kph.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_AEB_wet_120kph.dat"
Write-Host "Done: S_AEB_wet_120kph.xosc" -ForegroundColor Green
& $esmini --osc "$scen\AEB\S_AEB_icy_50kph.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_AEB_icy_50kph.dat"
Write-Host "Done: S_AEB_icy_50kph.xosc" -ForegroundColor Green
& $esmini --osc "$scen\AEB\S_AEB_icy_80kph.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_AEB_icy_80kph.dat"
Write-Host "Done: S_AEB_icy_80kph.xosc" -ForegroundColor Green
& $esmini --osc "$scen\AEB\S_AEB_icy_120kph.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_AEB_icy_120kph.dat"
Write-Host "Done: S_AEB_icy_120kph.xosc" -ForegroundColor Green

Write-Host 'Running ACC scenarios...' -ForegroundColor Cyan
& $esmini --osc "$scen\ACC\S_ACC_dry_mild.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_ACC_dry_mild.dat"
Write-Host "Done: S_ACC_dry_mild.xosc" -ForegroundColor Green
& $esmini --osc "$scen\ACC\S_ACC_dry_moderate.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_ACC_dry_moderate.dat"
Write-Host "Done: S_ACC_dry_moderate.xosc" -ForegroundColor Green
& $esmini --osc "$scen\ACC\S_ACC_dry_hard.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_ACC_dry_hard.dat"
Write-Host "Done: S_ACC_dry_hard.xosc" -ForegroundColor Green
& $esmini --osc "$scen\ACC\S_ACC_damp_mild.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_ACC_damp_mild.dat"
Write-Host "Done: S_ACC_damp_mild.xosc" -ForegroundColor Green
& $esmini --osc "$scen\ACC\S_ACC_damp_moderate.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_ACC_damp_moderate.dat"
Write-Host "Done: S_ACC_damp_moderate.xosc" -ForegroundColor Green
& $esmini --osc "$scen\ACC\S_ACC_damp_hard.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_ACC_damp_hard.dat"
Write-Host "Done: S_ACC_damp_hard.xosc" -ForegroundColor Green
& $esmini --osc "$scen\ACC\S_ACC_wet_mild.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_ACC_wet_mild.dat"
Write-Host "Done: S_ACC_wet_mild.xosc" -ForegroundColor Green
& $esmini --osc "$scen\ACC\S_ACC_wet_moderate.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_ACC_wet_moderate.dat"
Write-Host "Done: S_ACC_wet_moderate.xosc" -ForegroundColor Green
& $esmini --osc "$scen\ACC\S_ACC_wet_hard.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_ACC_wet_hard.dat"
Write-Host "Done: S_ACC_wet_hard.xosc" -ForegroundColor Green
& $esmini --osc "$scen\ACC\S_ACC_icy_mild.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_ACC_icy_mild.dat"
Write-Host "Done: S_ACC_icy_mild.xosc" -ForegroundColor Green
& $esmini --osc "$scen\ACC\S_ACC_icy_moderate.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_ACC_icy_moderate.dat"
Write-Host "Done: S_ACC_icy_moderate.xosc" -ForegroundColor Green
& $esmini --osc "$scen\ACC\S_ACC_icy_hard.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_ACC_icy_hard.dat"
Write-Host "Done: S_ACC_icy_hard.xosc" -ForegroundColor Green

Write-Host 'Running LKA scenarios...' -ForegroundColor Cyan
& $esmini --osc "$scen\LKA\S_LKA_dry_slow.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_LKA_dry_slow.dat"
Write-Host "Done: S_LKA_dry_slow.xosc" -ForegroundColor Green
& $esmini --osc "$scen\LKA\S_LKA_dry_med.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_LKA_dry_med.dat"
Write-Host "Done: S_LKA_dry_med.xosc" -ForegroundColor Green
& $esmini --osc "$scen\LKA\S_LKA_dry_fast.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_LKA_dry_fast.dat"
Write-Host "Done: S_LKA_dry_fast.xosc" -ForegroundColor Green
& $esmini --osc "$scen\LKA\S_LKA_damp_slow.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_LKA_damp_slow.dat"
Write-Host "Done: S_LKA_damp_slow.xosc" -ForegroundColor Green
& $esmini --osc "$scen\LKA\S_LKA_damp_med.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_LKA_damp_med.dat"
Write-Host "Done: S_LKA_damp_med.xosc" -ForegroundColor Green
& $esmini --osc "$scen\LKA\S_LKA_damp_fast.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_LKA_damp_fast.dat"
Write-Host "Done: S_LKA_damp_fast.xosc" -ForegroundColor Green
& $esmini --osc "$scen\LKA\S_LKA_wet_slow.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_LKA_wet_slow.dat"
Write-Host "Done: S_LKA_wet_slow.xosc" -ForegroundColor Green
& $esmini --osc "$scen\LKA\S_LKA_wet_med.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_LKA_wet_med.dat"
Write-Host "Done: S_LKA_wet_med.xosc" -ForegroundColor Green
& $esmini --osc "$scen\LKA\S_LKA_wet_fast.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_LKA_wet_fast.dat"
Write-Host "Done: S_LKA_wet_fast.xosc" -ForegroundColor Green
& $esmini --osc "$scen\LKA\S_LKA_icy_slow.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_LKA_icy_slow.dat"
Write-Host "Done: S_LKA_icy_slow.xosc" -ForegroundColor Green
& $esmini --osc "$scen\LKA\S_LKA_icy_med.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_LKA_icy_med.dat"
Write-Host "Done: S_LKA_icy_med.xosc" -ForegroundColor Green
& $esmini --osc "$scen\LKA\S_LKA_icy_fast.xosc" --fixed_timestep 0.05 --headless --record "$raw\S_LKA_icy_fast.dat"
Write-Host "Done: S_LKA_icy_fast.xosc" -ForegroundColor Green

Write-Host 'All 36 scenarios complete.' -ForegroundColor Yellow