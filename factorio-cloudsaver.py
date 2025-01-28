#!/usr/bin/env python3

print('\nStarted Factorio-Cloudsaver -- savegame manager for more reliable and faster Steam Cloud syncing\n')

import os
import sys
import time
import subprocess

# Maximum file size for Steam Cloud:
maxsize = 100 * 1024^2  # 100MB
# Round size up to this (must be a divisor of the above):
sizequant = 1 * 1024^2  # 1MB
# Recompute
maxsize //= sizequant

poll_interval = .5  # seconds -- Game still running check interval
scan_interval = 10  # seconds -- Native save directory polling interval

# Various paths
pj = os.path.join
ourdir = os.path.abspath(os.path.dirname(__file__))
nativedir = os.path.abspath(pj(ourdir, os.path.pardir, 'saves'))
fragdir = pj(ourdir, 'fragments')
savedir = pj(ourdir, 'saves')

# We are passed the game command in arguments
gamecmd = sys.argv[1:]

# This represents a saved game
class GameSave(object):
    def __init__(self):
        pass

# Global state
savedict = dict()  # All game saves and the "compact" data that allows to screen for changes

print(f'Our directory: {ourdir}\n'
    f'Factorio saves dir: {nativedir}\n'
    f'Game working directory: {os.getcwd()}\n'
    f'Game command and arguments: {repr(gamecmd)}\n')

# Create needed directories
for i in (nativedir, savedir):
    try:
        os.mkdir(i)
    except FileExistsError:
        pass

if os.path.exists(fragdir):
    print(f'This directory exists:\n'
        f'{fragdir}\n'
        f'It\'s not supposed to!\n\n'
        f'YOU ARE RISKING LOSING YOUR SAVES RIGHT NOW!!!\n\n'
        f'Currently, your saves might be in:\n'
        f'{fragdir}\n'
        f'{savedir}\n'
        f'{nativedir}\n\n'
        f'Make sure your saves and "Steam_Autocloud.vdf" are in this directory:\n'
        f'{nativedir}\n'
        f'Better yet, back them up somewhere else too just in case.\n\n'
        f'After that, press [Enter] to quit and sync to cloud.\n'
        f'Finally, remove the following directory:\n'
        f'{fragdir}\n'
        f'After that, the game should start fine.')
    input()
    exit()

save_stamps = dict()
def scan_updates():
    print('Scanning save folder for modifications...')
    found = set()
    for entry in os.scandir(nativedir):
        if not entry.name.endswith('.zip'):
            continue
        if entry.name.startswith('_autosave'):
            continue
        found.add(entry.name)
        st = entry.stat()
        if entry.name in save_stamps and save_stamps[entry.name] == (st.st_size, st.st_mtime):
            continue
        p = os.path.join(fragdir, entry.name.rsplit('.', 1)[0])
        if entry.name in save_stamps:
            n = save_stamps[entry.name][0]
            if n == 1:
                n = [f'{p}.zip']
            else:
                n = [f'{p}.firstof.{n}.zip'] + [f'{p}.partidx.{i}.zip' for i in range(2, n + 1)]
                for i in n:
                    try:
                        os.remove(i)
                    except:
                        print('Failed to remove stale fragment: {i}')
        with open(entry.path, 'rb') as f:
            data = f.read()
        sz = (len(data) + sizequant - 1) // sizequant
        if sz <= maxsize:
            with open(f'{p}.zip', 'wb') as f:
                f.write(data)
        else:
            n = (sz + maxsize - 1) // maxsize
            sz = (sz + n - 1) // n * sizequant
            n = (len(data) + sz - 1) // sz
            with open(f'{p}.firstof.{n}.zip', 'wb') as f:
                f.write(data[:sz])
            for i in range(2, n):
                with open(f'{p}.partidx.{i}.zip', 'wb') as f:
                    f.write(data[sz*(i-1): sz*i])
            with open(f'{p}.partidx.{n}.zip', 'wb') as f:
                f.write(data[sz*(n-1):])
        save_stamps[entry.name] = (n, len(data), st.st_mtime)

    print('Save scan done')

# Move dirs into place
os.rename(nativedir, fragdir)
os.rename(savedir, nativedir)

try:
    # Start the game right away to save startup time
    game = subprocess.Popen(gamecmd)
    print('Game started. While it loads, preparing the saves...')

    # Move fragments out of savedir
    frags = []
    for entry in os.scandir(nativedir):
        if not entry.name.endswith('.zip'):
            continue
        if entry.name.startswith('_autosave'):
            continue
        p = entry.name.rsplit('.', 3)
        if len(p) < 4 or not p[2].isdigit or p[1] not in ('firstof', 'partidx'):
            continue
        frags.append(entry.name)
    for i in frags:
        t = os.path.join(fragdir, i)
        if os.path.exists(t):
            continue
        try:
            os.rename(os.path.join(nativedir, i), t)
        except:
            print('Failed to move from saves to frags: {i}')
    # Index the fragments
    frag_n = dict()
    autosaves = []
    frags = []
    for entry in os.scandir(fragdir):
        if not entry.name.endswith('.zip'):
            continue
        if entry.name.startswith('_autosave'):
            autosaves.append(entry.path)
            continue
        p = entry.name.rsplit('.', 3)
        if len(p) < 4 or not p[2].isdigit or p[1] not in ('firstof', 'partidx'):
            frag_n[entry.name.rsplit('.', 1)[0]] = 1
            continue
        j = int(p[2])
        if p[1] == 'firstof' and j > 1:
            frag_n[p[0]] = j
        elif p[1] == 'partnum' and j > 0:
            frags.append((p[0], j))
        else:
            frags.append((p[0], 0))
    # Prune dangling fragments
    for i, j in frags:
        if j <= 0 or i not in frag_n or frag_n[i] < j:
            p = os.path.join(fragdir, f'{i}.partnum.{j}.zip')
            try:
                os.remove(p)
            except:
                print('Failed to remove dangling fragment: {p}')
    del frags
    # Move autosaves out of fragdir
    for i in autosaves:
        try:
            os.replace(os.path.join(fragdir, i), os.path.join(nativedir, i))
        except:
            print('Failed to move from frags to saves: {i}')
    del autosaves
    # Prune removed saves from savedir
    stale = []
    for entry in os.scandir(nativedir):
        if not entry.name.endswith('.zip'):
            continue
        if entry.name.startswith('_autosave'):
            continue
        if entry.name.rsplit('.', 1)[0] not in frag_n:
            stale.append(entry.path)
    del frag_n
    for i in stale:
        try:
            os.remove(i)
        except:
            print('Failed to remove stale save: {i}')
    del stale
    # Make savedir contents match fragdir
    save_stamps = dict()
    borked = []
    for entry in os.scandir(fragdir):
        if not entry.name.endswith('.zip'):
            continue
        p = entry.name.rsplit('.', 3)
        if len(p) < 4 or not p[2].isdigit or p[1] not in ('firstof', 'partidx'):
            with open(entry.path, 'rb') as f:
                data = f.read()
            p = entry.name
            n = 1
        elif p[1] != 'firstof':
            continue
        else:
            n = int(p[2])
            with open(entry.path, 'rb') as f:
                data = f.read()
            for i in range(2, n + 1):
                t = os.path.join(fragdir, f'{p[0]}.partidx.{i}.zip')
                if os.path.exists(t):
                    with open(t, 'rb') as f:
                        data += f.read()
                else:
                    data = None
                    break
            if data is None:
                borked.append(entry.path)
                for i in range(2, n + 1):
                    t = os.path.join(fragdir, f'{p[0]}.partidx.{i}.zip')
                    if os.path.exists(t):
                        borked.append(t)
                continue
            p = f'{p[0]}.zip'
        p = os.path.join(nativedir, p)
        st = os.stat(p)
        upd = True
        if st.st_size == len(data):
            upd = False
        else:
            try:
                with open(p, 'rb') as f:
                    if f.read() == data:
                        upd = False
            except:
                pass
        if upd:
            with open(p, 'wb') as f:
                f.write(data)
            save_stamps[p] = (n, len(data), os.path.getmtime(p))
        else:
            save_stamps[p] = (n, st.st_size, st.st_mtime)
    del data
    for i in borked:
        try:
            os.remove(i)
        except:
            print('Failed to remove borked save fragment: {i}')
    del borked
    print('Game saves prepare done.')

    next_scan = time.monotonic()
    while game.poll() is None:
        if time.monotonic() >= next_scan:
            next_scan += scan_interval
            scan_updates()
        time.sleep(poll_interval)

    print('Game terminated.')
    scan_updates()

except:
    try:
        game.terminate()
        game.wait(timeout = 10)
    except:
        try:
            game.kill()
            game.wait(timeout = 5)
        except:
            pass

# Move dirs back where they were
os.rename(nativedir, savedir)
os.rename(fragdir, nativedir)

print('\nFactorio-Cloudsaver done.\n')

# input("Press [Enter] key to quit.")
