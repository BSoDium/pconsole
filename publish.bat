@echo off
@rem if this fails, try : python -m pip install --user --upgrade setuptools wheel
powershell write-host -fore Cyan CWD: %cd%
if %ERRORLEVEL% neq 0 goto ProcessError
    python setup.py sdist bdist_wheel 
:Follow
powershell write-host -fore Cyan "Checking package wheel"
twine check dist/*
pip install -e .
powershell write-host -fore Cyan "The program will pause now. Please test the new package before publishing it."
python test.py
set /p DUMMY=Press ENTER to continue...
powershell write-host -fore Cyan "please provide username and password for pypi"
twine upload dist/* 
powershell write-host -fore Cyan "reinstalling from pypi"
pip uninstall pconsole
pip install pconsole
powershell write-host -fore Green "done"
powershell write-host -fore Cyan "showing info"
pip show pconsole
exit /b 0

:ProcessError
powershell write-host -fore Red "Process failed, redirecting..."
python -m pip install --user --upgrade setuptools wheel
goto Follow

:ECHORED
%Windir%\System32\WindowsPowerShell\v1.0\Powershell.exe write-host -foregroundcolor Red %1 
goto:eof