# Factorio-Cloudsaver
This is a "simple" script to manage Factorio saves, especially for better Steam Cloud syncing

## Features
- Rename autosaves from plain number suffixes to creation date-time
- Keep last 30 each of daily, hourly, and simply latest saves locally
- Sync only last 7 daily autosaves? excluding today's, to Steam Cloud
- Split large saves into 100MB fragments for more stable syncing
- Numbers are editable in the script

## Usage
- Replace all `C:\Users\<your username>\` below to your actual user directory path
- Download the release .zip into the Factorio saves directory
  - On Windows it is `C:\Users\<your username>\AppData\Roaming\Factorio\saves\`
  - On *nix it is `~/.factorio/saves/`
- Repeat these steps after each fresh install of Factorio:
  - Put this in "Launch options" in Steam game properties:
    - Windows: `"C:\Users\<your username>\AppData\Roaming\Factorio\factorio-cloudsaver\factorio-cloudsaver.bat" %command%`
    - Linux: `~/.factorio/factorio-cloudsaver/factorio-cloudsaver.py %command%`
  - Extract the folder from the .zip next to the saves folder
- Run the game normally
  - On first launch on Windows, it will download Python
