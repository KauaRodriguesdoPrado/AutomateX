# Executa o script Python que abre o Chrome com o perfil do usuário.
# Uso:
#   .\run_chrome_and_script.ps1

$pythonScript = "c:\Users\Tab 10\Python\automation\code-willian.py"

if (-not (Test-Path $pythonScript)) {
    Write-Error "Script Python não encontrado em: $pythonScript"
    exit 1
}

Write-Host "Executando script Python: $pythonScript"
python $pythonScript
