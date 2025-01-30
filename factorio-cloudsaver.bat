@echo off
if not exist "%~dp0\python" powershell -Command "$v = '3.6.8'; $p = '%~dp0\python'; $z = '$p-$v.zip';" ^
        "Invoke-WebRequest -Uri https://www.python.org/ftp/python/$v/python-$v-embed-amd64.zip -OutFile $z;" ^
        "Expand-Archive -Path $z -DestinationPath $p; Remove-Item $z"
"%~dp0\python\python.exe" "%~dpn0.py" %*
pause