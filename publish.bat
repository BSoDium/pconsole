@echo off
@rem if this fails, try : python -m pip install --user --upgrade setuptools wheel
echo CWD: %cd%
if %ERRORLEVEL% neq 0 goto ProcessError
    python setup.py sdist bdist_wheel 
:Follow
twine check dist/*
pip install -e .
echo try the installed version on a third-party program be4 commiting, don't be stupid, this is important
pause
echo then provide username and password
twine upload dist/* 
exit /b 0

:ProcessError
python -m pip install --user --upgrade setuptools wheel
goto Follow