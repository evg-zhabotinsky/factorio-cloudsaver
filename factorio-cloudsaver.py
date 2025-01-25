#!/usr/bin/env python3

print('Factorio savegame manager for more reliable and faster Steam Cloud syncing')

import os
import sys
import subprocess

maxsize = 128 * 1024^2

pj = os.path.join
ourdir = os.path.abspath(os.path.dirname(__file__))
nativedir = os.path.abspath(pj(ourdir, os.path.pardir, 'saves'))
fragdir = pj(ourdir, 'fragments')
refdir = pj(ourdir, 'fragref')
savedir = pj(ourdir, 'saves')

gamecmd = sys.argv[1:]


for i in (nativedir, refdir, savedir):
    try:
        os.mkdir(i)
    except FileExistsError:
        pass

if os.path.exists(fragdir):
    print(f'Directory "{fragdir}" exists.\n'
          f'It\'s not supposed to!\n\n'
          f'YOU ARE RISKING LOSING YOUR SAVES RIGHT NOW!!!\n\n'
          f'Currently, your saves might be in:\n'
          f'{savedir}\n'
          f'{fragdir}\n'
          f'{refdir}\n'
          f'{nativedir}\n'
          f'Make sure your saves and "Steam_Autocloud.vdf" are this directory:\n'
          f'{nativedir}\n'
          f'Better yet, back them up somewhere else too just in case.\n'
          f'After that, press [Enter] to quit and sync to cloud.\n'
          f'Finally, remove "{fragdir}".\n'
          f'After that, the game should start fine.')
    input()
    exit()

print(gamecmd)
print(os.listdir(ourdir))