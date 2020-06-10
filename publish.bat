@echo off
cls
@rem if this fails, try : python -m pip install --user --upgrade setuptools wheel

set "cecho=powershell write-host -fore"
%cecho% Cyan CWD: %cd% 

@rem updating pip
python -m pip install pip==19.0.1
@rem try catch block
python setup.py sdist bdist_wheel 
if %ERRORLEVEL% neq 0 CALL:ProcessError1

:Wheel
%cecho% Cyan "Checking package wheel"
twine check dist/*
if %ERRORLEVEL% neq 0 CALL:ProcessError2

:Twine
python -m pip install -e .
%cecho% Cyan "The program will pause now. Please test the new package before publishing it."
@python test.py
set /p DUMMY=Press ENTER to continue...
%cecho% Cyan "please provide username and password for pypi"
twine upload dist/* 
%cecho% Cyan "reinstalling from pypi"
python -m pip uninstall -y pconsole
python -m pip install pconsole
%cecho% Green "done"
%cecho% Cyan "showing info"
python -m pip show pconsole
pause
exit /b 0

:ProcessError1
%cecho% Red "Process failed. Redirecting..."
python -m pip install --user --upgrade setuptools wheel
goto:eof

:ProcessError2
%cecho% Red "Process failed. Redirecting..."
python -m pip install twine
goto:eof

:ECHORED 
@rem unused
%Windir%\System32\WindowsPowerShell\v1.0\Powershell.exe write-host -foregroundcolor Red %1 
goto:eof