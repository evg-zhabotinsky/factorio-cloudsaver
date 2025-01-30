#!/usr/bin/env python3

print('\nStarted Factorio-Cloudsaver -- savegame manager for more reliable and faster Steam Cloud syncing\n')

import os
import sys
import time
import subprocess

# Maximum file size for Steam Cloud:
maxsize = 100 * 1024**2  # 100MB
# Round size up to this (must be a divisor of the above):
sizequant = 1 * 1024**2  # 1MB
# Recompute
maxsize //= sizequant

# Autosave management
sync_daily = 7
keep_daily = 30
keep_hourly = 24
keep_last = 20

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

extstr = '.zip'
autostr = '_autosave'
fragstr = 'save_fragment_'
lastfragstr = 'last_save_fragment_'

def fragnames(name, n):
    if n <= 1:
        return [name]
    return [f'{name}.{lastfragstr if i == n else fragstr}{i}' for i in range(1, n + 1)]

def savename(fullname:str):
    if fullname.endswith(extstr):
        return fullname[:-len(extstr)]
    return None

def parsefrag(basename:str):  # => (name, partcount)
    p = basename.rsplit('.', 1)
    if len(p) == 1:
        return (basename, 1)
    if p[1].startswith(fragstr):
        if not p[1][len(fragstr):].isdigit:
            return (basename, 1)
        return (None, None)  # Ignore non-last parts here
    if p[1].startswith(lastfragstr):
        n = p[1][len(lastfragstr):]
        if not n.isdigit:
            return (basename, 1)
        return (p[0], int(n))

def findsaves(nameset:set):
    res = dict()
    for i in nameset:
        name, parts = parsefrag(i)
        if name is None:
            continue
        if name in res and res[name] < parts:
            continue
        res[name] = parts
    for i, j in list(res.items()):
        if not nameset.issuperset(fragnames(i, j)):
            del res[i]
    return res

def trydel(name, dir=nativedir):
    path = os.path.join(dir, name + extstr)
    try:
        os.remove(path)
    except:
        print(f'Failed to remove: {path}')

def delfrag(name, n):
    for i in fragnames(name, n):
        trydel(i, fragdir)

def prunesaves(saves:dict, nameset:set, dir):
    for i in nameset.difference(i for name, n in saves.items()
                                  for i in fragnames(name, n)):
        trydel(i, dir)

def dirsaves(dir):
    nameset = set(savename(i) for i in os.listdir(dir))
    nameset.discard(None)
    return nameset

def prepdir(dir):
    nameset = dirsaves(dir)
    saves = findsaves(nameset)
    prunesaves(saves, nameset, dir)
    return saves

def readsave(name, dir=nativedir):
    with open(os.path.join(dir, name + extstr), 'rb') as f:
        return f.read()

def writesave(data, ts, name, dir=nativedir):
    path = os.path.join(dir, name + extstr)
    with open(path, 'wb') as f:
        f.write(data)
    os.utime(path, (ts, ts))

def readfragsave(name, n):
    data = b''
    for i in fragnames(name, n):
        data += readsave(i, fragdir)
    return data

def writefragsave(data, ts, name):
    sz = (len(data) + sizequant - 1) // sizequant
    if sz <= maxsize:
        writesave(data, ts, name, fragdir)
        return 1
    n = (sz + maxsize - 1) // maxsize
    sz = (sz + n - 1) // n * sizequant
    n = (len(data) + sz - 1) // sz
    p = 0
    for i in fragnames(name, n):
        t = p + sz
        writesave(data[p:t], ts, i, fragdir)
        p = t
    return n

def scansaves():
    res = dict()
    for i in os.scandir(nativedir):
        name = savename(i.name)
        if name is None:
            continue
        st = i.stat()
        res[name] = (st.st_size, st.st_mtime)
    return res

def handle_autosaves(stamps:dict):
    # Rename default-named autosaves
    for name, (sz, ts) in sorted(stamps.items()):
        if name[len(autostr):].isdigit():
            tz = time.strftime('%z', time.localtime(ts))
            tz = f'{"PM"[tz[0]=="-"]}{tz[-4:]}'
            newname = f'{autostr}_{time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(ts))}{tz}'
            os.replace(os.path.join(nativedir, name + extstr),
                       os.path.join(nativedir, newname + extstr))
            stamps[newname] = stamps[name]
            del stamps[name]
    # Prune old autosaves
    daily = dict()
    hourly = dict()
    names = sorted(stamps.keys())
    for i in names:
        j = i.rsplit('-', 2)[0]
        hourly[j] = i
        j = j.rsplit('_', 1)[0]
        daily[j] = i
    names = names[-keep_last:]
    names = sorted(set(hourly.values()).difference(names))[-keep_hourly:] + names
    names = sorted(set(daily.values()).difference(names))[-keep_daily:] + names
    # Only return autosaves to be synced
    today = f'{autostr}_{time.strftime("%Y-%m-%d", time.localtime(time.time()))}'
    if today in daily:
        del daily[today]
    res = dict()
    for i in sorted(daily.values())[-sync_daily:]:
        res[i] = stamps[i]
    return res

save_stamps = dict()
def prepare():
    savedir_saves = prepdir(nativedir)
    fragdir_saves = prepdir(fragdir)
    # Move fragments from savedir and prune deleted non-auto-saves
    for name, n in savedir_saves.items():
        if n == 1:
            if name not in fragdir_saves and not name.startswith(autostr):
                trydel(name)
            continue
        if name in fragdir_saves:
            continue
        for i in fragnames(name, n):
            j = i + extstr
            try:
                os.rename(os.path.join(nativedir, j), os.path.join(fragdir, j))
            except:
                print('Failed to move {j} from savedir to fragdir')
                trydel(i)
    savedir_saves = scansaves()
    save_stamps.clear()
    for name, n in fragdir_saves.items():
        data = readfragsave(name, n)
        if name in savedir_saves and data == readsave(name):
            ts = savedir_saves[name][1]
        else:
            ts = os.path.getmtime(os.path.join(fragdir, fragnames(name, n)[-1] + extstr))
            writesave(data, ts, name)
        save_stamps[name] = (n, len(data), ts)

def scan_updates():
    print('Scanning save folder for modifications...')
    new_stamps = scansaves()
    # Handle autosaves
    autosaves = {name: v for name, v in new_stamps.items() if name.startswith(autostr)}
    for name in autosaves.keys():
        del new_stamps[name]
    new_stamps.update(handle_autosaves(autosaves))
    # Prune removed saves
    for name in set(save_stamps.keys()).difference(new_stamps.keys()):
        delfrag(name, save_stamps[name][0])
        del save_stamps[name]
    # Sync new saves
    for name, (sz, ts) in new_stamps.items():
        if name in save_stamps:
            if save_stamps[name][1:] == (sz, ts):
                continue
            delfrag(name, save_stamps[name][0])
        n = writefragsave(readsave(name), ts, name)
        save_stamps[name] = (n, sz, ts)
    print('Save scan done')

# Create needed directories
for i in (nativedir, savedir):
    try:
        os.mkdir(i)
    except FileExistsError:
        pass
# Move dirs into place
os.rename(nativedir, fragdir)
os.rename(savedir, nativedir)

try:
    # Start the game right away to save startup time
    game = subprocess.Popen(gamecmd)
    print('Game started. While it loads, preparing the saves...')

    prepare()
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
    raise

# Move dirs back where they were
os.rename(nativedir, savedir)
os.rename(fragdir, nativedir)

print('\nFactorio-Cloudsaver done.\n')

# input("Press [Enter] key to quit.")
