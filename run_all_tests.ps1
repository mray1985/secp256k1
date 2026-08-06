<#PSScriptInfo

.VERSION 1.0

.AUTHOR
Mistral Vibe

.DESCRIPTION
Runs all Puzzle 135 tests and saves output to DOCX

#>

# Create output directory
$outputDir = ".\Test_Results"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Run all tests
Write-Host "================================================================================"
Write-Host "PUZZLE 135 - COMPREHENSIVE TEST SUITE"
Write-Host "================================================================================"
Write-Host ""

# Test 1: Normalization Matrix
Write-Host "[1/4] Running normalization matrix test..."
$output1 = "$outputDir\normalize_$timestamp.txt"
python normalize_puzzle135.py *>&1 | Tee-Object -FilePath $output1

Write-Host ""
Write-Host "[2/4] Running true2.txt correlation test..."
$output2 = "$outputDir\correlate_true2_$timestamp.txt"
python correlate_true2.py *>&1 | Tee-Object -FilePath $output2

Write-Host ""
Write-Host "[3/4] Running candidate test..."
$output3 = "$outputDir\test_candidates_$timestamp.txt"
python test_candidates_ascii.py *>&1 | Tee-Object -FilePath $output3

Write-Host ""
Write-Host "[4/4] Running candidate generation and test..."
$output4 = "$outputDir\generate_and_test_$timestamp.txt"
python generate_and_test_candidates.py *>&1 | Tee-Object -FilePath $output4

Write-Host ""
Write-Host "================================================================================"
Write-Host "ALL TESTS COMPLETE"
Write-Host "================================================================================"
Write-Host ""
Write-Host "Output files:"
Write-Host "  1. $output1"
Write-Host "  2. $output2"
Write-Host "  3. $output3"
Write-Host "  4. $output4"
Write-Host ""

# Create DOCX summary
Write-Host "Creating DOCX summary..."

$docxScript = @"
from docx import Document
import glob
import os

timestamp = '$timestamp'
output_dir = '$outputDir'

# Read all output files
output_files = glob.glob(os.path.join(output_dir, '*_'+timestamp+'.txt'))
output_files.sort()

doc = Document()
doc.add_heading('Puzzle 135 - Test Results ' + timestamp, 0)

for filepath in output_files:
    filename = os.path.basename(filepath)
    doc.add_heading(filename, level=1)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    doc.add_paragraph(content)
    doc.add_page_break()

output_docx = os.path.join(output_dir, 'Puzzle135_Results_' + timestamp + '.docx')
doc.save(output_docx)
print(f'DOCX saved to: {output_docx}')
"@

$docxScript | Out-File -FilePath "temp_docx.py" -Encoding UTF8
python temp_docx.py
Remove-Item -Path "temp_docx.py" -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "DONE!"
