Set-Location $PSScriptRoot

$reportPath = ".\diagnostico_ui_01b_base.txt"

cmd /c "echo === DATA === > diagnostico_ui_01b_base.txt"
cmd /c "echo %date% %time% >> diagnostico_ui_01b_base.txt"

cmd /c "echo. >> diagnostico_ui_01b_base.txt"
cmd /c "echo === BRANCH === >> diagnostico_ui_01b_base.txt"
cmd /c "git branch --show-current >> diagnostico_ui_01b_base.txt 2>&1"

cmd /c "echo. >> diagnostico_ui_01b_base.txt"
cmd /c "echo === GIT STATUS === >> diagnostico_ui_01b_base.txt"
cmd /c "git status --short >> diagnostico_ui_01b_base.txt 2>&1"

cmd /c "echo. >> diagnostico_ui_01b_base.txt"
cmd /c "echo === BASE.HTML === >> diagnostico_ui_01b_base.txt"
cmd /c "type templates\base.html >> diagnostico_ui_01b_base.txt 2>&1"

cmd /c "echo. >> diagnostico_ui_01b_base.txt"
cmd /c "echo === NAVBAR.HTML === >> diagnostico_ui_01b_base.txt"
cmd /c "type templates\partials\navbar.html >> diagnostico_ui_01b_base.txt 2>&1"

cmd /c "echo. >> diagnostico_ui_01b_base.txt"
cmd /c "echo === SIDEBAR.HTML === >> diagnostico_ui_01b_base.txt"
cmd /c "type templates\partials\sidebar.html >> diagnostico_ui_01b_base.txt 2>&1"

cmd /c "echo. >> diagnostico_ui_01b_base.txt"
cmd /c "echo === MESSAGES.HTML === >> diagnostico_ui_01b_base.txt"
cmd /c "if exist templates\partials\messages.html (type templates\partials\messages.html) else (echo ARQUIVO NAO EXISTE) >> diagnostico_ui_01b_base.txt 2>&1"

cmd /c "echo. >> diagnostico_ui_01b_base.txt"
cmd /c "echo === STATIC UI FILES === >> diagnostico_ui_01b_base.txt"
cmd /c "dir /s /b static\ui >> diagnostico_ui_01b_base.txt 2>&1"

cmd /c "echo. >> diagnostico_ui_01b_base.txt"
cmd /c "echo === DJANGO CHECK === >> diagnostico_ui_01b_base.txt"
cmd /c "python manage.py check >> diagnostico_ui_01b_base.txt 2>&1"

Write-Host ""
Write-Host "Diagnostico concluido." -ForegroundColor Green
Write-Host "Nenhum arquivo do projeto foi alterado." -ForegroundColor Cyan
Write-Host "Envie o arquivo: $reportPath" -ForegroundColor Yellow
