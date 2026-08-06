<#PSScriptInfo

.VERSION 1.0

.AUTHOR
Mistral Vibe

.DESCRIPTION
Runs the Puzzle 135 test and prints to screen.

#>

Write-Host "================================================================================"
Write-Host "PUZZLE 135 - COMPREHENSIVE TEST"
Write-Host "================================================================================"
Write-Host ""

# Run the Python test
Write-Host "Running normalization matrix test..."
python normalize_puzzle135.py

Write-Host ""
Write-Host "================================================================================"
Write-Host "Running candidate EC multiplication test..."
Write-Host "================================================================================"
Write-Host ""
python test_candidates_ascii.py

Write-Host ""
Write-Host "================================================================================"
Write-Host "DONE"
Write-Host "================================================================================"
