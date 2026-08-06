@echo off
cd /d "%~dp0"
echo Generating sequence files...
python generate_n_sequences.py
if errorlevel 1 goto fail
echo.
echo Generating PDF...
python generate_scalar_double_chain_pdf.py
if errorlevel 1 goto fail
echo.
echo DONE: Scalar_Double_Chain_Session.pdf
start "" "%~dp0Scalar_Double_Chain_Session.pdf"
exit /b 0

:fail
echo.
echo FAILED. Try: pip install fpdf2
pause
exit /b 1
