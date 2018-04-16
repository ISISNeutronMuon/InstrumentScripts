xcopy /q /s /e /h /Y githooks\* .git\hooks

if %errorlevel% neq 0 (
    echo "Setup did not complete"	
) else (
    echo "Setup completed successfully"
)
pause
