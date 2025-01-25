# Define the Python version and download URL
$downloadUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-embed-amd64.zip"
$pythonVersion = "3.6.8"

# Get the base name of the script (without extension)
$scriptBaseName = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Name)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonDir = Join-Path $scriptDir "python"
$pythonExe = Join-Path $pythonDir "python.exe"
$pythonZip = Join-Path $scriptDir "python.zip"
$pythonScript = Join-Path $scriptDir "$scriptBaseName.py"
$scriptArgs = $args

# Function to check if a Python executable supports f-strings
function Test-PythonFStringSupport {
    param (
        [string]$pythonCommand
    )
    & $pythonCommand -c "f''"
    return $LASTEXITCODE -eq 0
}

function Get-Python {
    # Download the embeddable Python ZIP file if not found
    Write-Host "Downloading Python $pythonVersion embeddable ZIP..."
    Invoke-WebRequest -Uri $downloadUrl -OutFile $pythonZip

    # Extract the ZIP file into the "python" directory
    Write-Host "Extracting Python into '$pythonDir'..."
    if (Test-Path -Path $pythonDir) {
        Remove-Item -Path $pythonDir -Recurse -Force
    }
    Expand-Archive -Path $pythonZip -DestinationPath $pythonDir

    # Clean up the downloaded ZIP file
    Remove-Item $pythonZip

    # Check if the Python executable was successfully extracted
    if (-Not (Test-PythonFStringSupport $pythonExe)) {
        Write-Host "Failed to install Python. Exiting..."
        exit 1
    }

    Write-Host "Python installation successful, available at '$pythonExe'."
}

if ($args.Count -eq 0) {
    Write-Host "Script invoked without arguments."
    if (Test-PythonFStringSupport $pythonExe) {
        Write-Host "Supported Python version is found at '$pythonExe'."
    }
    if (Test-PythonFStringSupport "python3" -or Test-PythonFStringSupport "python") {
        Write-Host "Supported Python version is found in PATH."
    }
    if (1 -eq $Host.UI.PromptForChoice("Dowload minimal portable Python $pythonVersion to '$pythonDir'?", "", @("&No (quit)", "&Yes"), 0)) {
        Get-Python
        Write-Host "Press any key to quit."
        [void][System.Console]::ReadKey($true)
    }
    exit 0
}

# Find supported Python
if (Test-PythonFStringSupport $pythonExe) {
    Write-Host "Supported Python found at '$pythonExe'"
    $pythonCommand = $pythonExe
} elseif (Test-PythonFStringSupport "python3") {
    Write-Host "Supported Python found as 'python3'"
    $pythonCommand = "python3"
} elseif (Test-PythonFStringSupport "python") {
    Write-Host "Supported Python found as 'python'"
    $pythonCommand = "python"
} else {
    Write-Host "No supported Python found."
    Get-Python
    $pythonCommand = $pythonExe
}

# Run the Python script with the same base name as the PowerShell script
if (Test-Path $pythonScript) {
    Write-Host "Running '$pythonScript'..."
    & $pythonCommand $pythonScript @scriptArgs
    [void][System.Console]::ReadKey($true)
    exit $LASTEXITCODE
} else {
    Write-Host "Python script '$pythonScript' not found. Exiting..."
    exit 1
}
