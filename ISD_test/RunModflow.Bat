if not exist "..\..\output\NUL" mkdir "..\..\output"
if not exist "..\..\output\output.ISD_test\NUL" mkdir "..\..\output\output.ISD_test"
..\..\bin\mf2005.exe ISD_test.nam /wait
pause
