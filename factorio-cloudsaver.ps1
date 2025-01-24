# Define the Python version and download URL
$pythonVersion = "3.6.8"
$downloadUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-embed-amd64.zip"

# Get the base name of the script (without extension)
$scriptBaseName = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Name)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonDir = Join-Path $scriptDir "python"
$pythonExe = Join-Path $pythonDir "python.exe"
$pythonZip = Join-Path $scriptDir "python.zip"

# Check if python3 is available in the PATH
$pythonInPath = Get-Command python3 -ErrorAction SilentlyContinue
if ($pythonInPath) {
    Write-Host "python3 is already available on the PATH."
    $pythonExe = "python3"
    Run-PythonScript
    exit
}

# Check if Python is already installed in the "python" directory
if (Test-Path $pythonExe) {
    Write-Host "Found portable Python in the 'python' directory."
    Run-PythonScript
    exit
}

# Download the embeddable Python ZIP file if not found
Write-Host "Downloading Python $pythonVersion embeddable ZIP..."
Invoke-WebRequest -Uri $downloadUrl -OutFile $pythonZip

# Extract the ZIP file into the "python" directory
Write-Host "Extracting Python into the 'python' directory..."
Expand-Archive -Path $pythonZip -DestinationPath $pythonDir

# Clean up the downloaded ZIP file
Remove-Item $pythonZip

# Check if the Python executable was successfully extracted
if (-Not (Test-Path $pythonExe)) {
    Write-Host "Failed to install Python. Exiting..."
    exit 1
}

Write-Host "Python installation complete. Using portable Python in '$pythonDir'..."

# Run the Python script with the same base name as the PowerShell script
Run-PythonScript

# Function to run the Python script
function Run-PythonScript {
    $pythonScriptPath = Join-Path $scriptDir "$scriptBaseName.py"
    
    if (Test-Path $pythonScriptPath) {
        Write-Host "Running the Python script '$pythonScriptPath'..."
        & $pythonExe $pythonScriptPath
    } else {
        Write-Host "Python script '$pythonScriptPath' not found. Exiting..."
        exit 1
    }
}
