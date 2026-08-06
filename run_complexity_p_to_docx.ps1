<#PSScriptInfo

.VERSION 1.0

.AUTHOR
Mistral Vibe

.DESCRIPTION
Runs Complexity_Simplified_p.txt content and saves output to DOCX file.

#>

# Check if python-docx is available
try {
    python -c "import docx; print('docx available')" *>&1 | Out-Null
    $has_docx = $true
} catch {
    $has_docx = $false
}

if (-not $has_docx) {
    Write-Host "Installing python-docx..."
    pip install python-docx
}

# Create a Python script that reads Complexity_Simplified_p.txt and saves to DOCX
$python_script = @"
from docx import Document

# Read Complexity_Simplified_p.txt
file_path = '02_Research\\notes\\Complexity_Simplified_p.txt'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    # Try alternative path
    file_path = 'Complexity_Simplified_p.txt'
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

# Create DOCX document
doc = Document()
doc.add_heading('Complexity Simplified P', 0)
doc.add_paragraph(content)

# Save
output_file = 'Complexity_Simplified_p_Output.docx'
doc.save(output_file)
print(f'DOCX saved to: {output_file}')
"@

$python_script | Out-File -FilePath "temp_create_docx.py" -Encoding UTF8

Write-Host "Converting Complexity_Simplified_p.txt to DOCX..."
python temp_create_docx.py

# Clean up
Remove-Item -Path "temp_create_docx.py" -Force -ErrorAction SilentlyContinue

Write-Host "Done!"
