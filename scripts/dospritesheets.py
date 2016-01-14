#!/usr/bin/python

# dospritesheets.py
# Copyright (C) 2015 Taras Tovchenko
# Email: doctorset@gmail.com
# You can redistribute and/or modify this software under the terms of the GNU
# General Public License as published by the Free Software Foundation;
# either version 2 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this
# program; if not, write to the Free Software Foundation, Inc., 59 Temple Place,
# Suite 330, Boston, MA 02111-1307 USA

import sys
import os, os.path
import subprocess
import datetime
import re
import argparse
import zlib
import struct


scriptDir = os.path.dirname(os.path.realpath(__file__))

def spritePacker():
	if 'darwin' == sys.platform:
		return os.path.join(scriptDir, '../tools/platform/macos/spriteglue.app/Contents/MacOS/spriteglue')
	if sys.platform.startswith('linux'):
		return os.path.join(scriptDir, '../tools/platform/linux/spriteglue/spriteglue')
	if 'win32' == sys.platform:
		return os.path.join(scriptDir, '../tools/platform/windows/spriteglue/spriteglue.exe')

	return ''

def pvrConverter():
	if 'darwin' == sys.platform:
		return os.path.join(scriptDir, '../tools/platform/macos/PVRTexToolCLI')
	if sys.platform.startswith('linux'):
		return os.path.join(scriptDir, '../tools/platform/linux/PVRTexToolCLI')
	if 'win32' == sys.platform:
		return os.path.join(scriptDir, '../tools/platform/windows/PVRTexToolCLI.exe')

	return ''

def pkmConverter():
	if 'darwin' == sys.platform:
		return os.path.join(scriptDir, '../tools/platform/macos/etc1tool')
	if sys.platform.startswith('linux'):
		return os.path.join(scriptDir, '../tools/platform/linux/etc1tool')
	if 'win32' == sys.platform:
		return os.path.join(scriptDir, '../tools/platform/windows/etc1tool.exe')

	return ''

def wasSourceModified(srcFolder, outTexture):
	if not os.path.isdir(srcFolder):
		print srcFolder + ' isn\'t a folder'
		sys.exit(1)

	if os.path.isfile(outTexture):
		srcModDate = datetime.datetime.fromtimestamp(os.path.getmtime(srcFolder))
		dstModDate = datetime.datetime.fromtimestamp(os.path.getmtime(outTexture))
		return srcModDate > dstModDate
	return True

def assemble(srcFolder, outTexture, scale, maxSize, hasAlpha):
	texBaseName = os.path.basename(outTexture)
	extension = re.search(r'\.(.*)$', texBaseName).groups()[0].lower()
	pngFilePath = os.path.join(os.path.dirname(outTexture), re.sub(r'\..*$', '.png', texBaseName))
	doPkm = 'pkm' == extension and not hasAlpha
	doPvr = 'pvr.ccz' == extension and not hasAlpha

	if not wasSourceModified(srcFolder, outTexture):
		return

	subprocess.call([spritePacker(),
		srcFolder,
		'--sheet', pngFilePath,
		'--scale', str(scale),
		'--opt', 'rgba8888' if hasAlpha else 'rgb888',
		'--max-size-w', str(maxSize),
		'--suffix', extension,
		'--powerOf2' if doPvr else '',
		'--square' if doPvr else ''])

	if doPvr:
		pvrFilePath = os.path.join(os.path.dirname(outTexture), re.sub(r'\..*$', '.pvr', texBaseName))
		subprocess.call([pvrConverter(),
		'-i', pngFilePath,
		'-o', pvrFilePath,
		'-f', 'PVRTC1_4_RGB',
		'-q', 'pvrtcbest',
		'-shh'])
		os.remove(pngFilePath)

		indata = open(pvrFilePath, 'rb').read()
		outdata = struct.pack('>4s2H2I', 'CCZ!', 0, 2, 0, sys.getsizeof(indata)) + zlib.compress(indata, zlib.Z_BEST_COMPRESSION)
		pvrcczFile = open(outTexture, 'wb')
		pvrcczFile.write(outdata)
		pvrcczFile.close()
		os.remove(pvrFilePath)

	if doPkm:
		subprocess.call([pkmConverter(),
		pngFilePath,
		'-o', outTexture])
		os.remove(pngFilePath)

def makeLOD(lodPath, dstDirPath, scale, maxSize, hasAlpha, fmt):
	for name in os.listdir(lodPath):
		srcPath = os.path.join(lodPath, name)
		if os.path.isdir(srcPath) and not name.startswith('.'):
			assemble(srcPath, os.path.join(dstDirPath, name + '.' + fmt), scale, maxSize, hasAlpha)

def makePreset(srcDir, dstDir, subDir, scale, maxSize, rgbaFmt, rgbFmt):
	if not dstDir:
		return

	if not os.path.exists(dstDir):
			os.makedirs(dstDir)

	srcPath = os.path.join(srcDir, 'rgba/shared')
	if os.path.exists(srcPath):
		makeLOD(srcPath, dstDir, scale, maxSize, True, rgbaFmt)

	srcPath = os.path.join(srcDir, 'rgb/shared')
	if os.path.exists(srcPath):
		makeLOD(srcPath, dstDir, scale, maxSize, False, rgbFmt)

	srcPath = os.path.join(srcDir, os.path.join('rgba', subDir))
	if os.path.exists(srcPath):
		makeLOD(srcPath, dstDir, 1, maxSize, True, rgbaFmt)

	srcPath = os.path.join(srcDir, os.path.join('rgb', subDir))
	if os.path.exists(srcPath):
		makeLOD(srcPath, dstDir, 1, maxSize, False, rgbFmt)

def run():
	parser = argparse.ArgumentParser(prog='SPRITESHEET GENERATOR')
	parser.add_argument('-appRoot')
	parser.add_argument('-fmt')
	parser.add_argument('-lods', nargs='*', default=['xhd', 'hd', 'sd'])
	args = parser.parse_args()

	textureDir = os.path.join(os.path.join(args.appRoot, 'temp/textures'), args.fmt)
	if not os.path.exists(textureDir):
		os.makedirs(textureDir)

	texSD = texHD = texXHD = None
	for lod in args.lods:
		if 'sd' == lod:
			texSD = os.path.join(textureDir, 'sd')
		elif 'hd' == lod:
			texHD = os.path.join(textureDir, 'hd')
		elif 'xhd' == lod:
			texXHD = os.path.join(textureDir, 'xhd')

	srcDir = os.path.join(args.appRoot, 'assets/spritesheets')
	makePreset(srcDir, texSD, 'sd', 0.25, 1024, 'png', args.fmt)
	makePreset(srcDir, texHD, 'hd', 0.5, 2048, 'png', args.fmt)
	makePreset(srcDir, texXHD, 'xhd', 1, 4096, 'png', args.fmt)

# -------------- main --------------
if __name__ == '__main__':
	run()

	