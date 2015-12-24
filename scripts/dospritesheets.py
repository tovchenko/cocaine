!#/usr/bin/python

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
import platform
import zlib


scriptDir = os.path.dirname(os.path.realpath(__file__))

def spritePacker():
	if 'Darwin' == platform.system():
		return os.path.join(scriptDir, '../tools/platform/macos/spriteglue.app/Contents/MacOS/spriteglue')
	if 'Linux' == platform.system():
		return os.path.join(scriptDir, '../tools/platform/linux/spriteglue/spriteglue')
	if 'Windows' == platform.system():
		return os.path.join(scriptDir, '../tools/platform/windows/spriteglue/spriteglue.exe')

	return ''

def pvrConverter():
	if 'Darwin' == platform.system():
		return os.path.join(scriptDir, '../tools/platform/macos/PVRTexToolCLI')
	if 'Linux' == platform.system():
		return os.path.join(scriptDir, '../tools/platform/linux/PVRTexToolCLI')
	if 'Windows' == platform.system():
		return os.path.join(scriptDir, '../tools/platform/windows/PVRTexToolCLI.exe')

	return ''

def pkmConverter():
	if 'Darwin' == platform.system():
		return os.path.join(scriptDir, '../tools/platform/macos/etc1tool')
	if 'Linux' == platform.system():
		return os.path.join(scriptDir, '../tools/platform/linux/etc1tool')
	if 'Windows' == platform.system():
		return os.path.join(scriptDir, '../tools/platform/windows/etc1tool.exe')

	return ''

def wasTextureModified(srcFolder, outTexture):
	if not os.path.isdir(srcFolder):
		print srcFolder + ' isn\'t a folder'
		sys.exit(1)

	if os.path.isfile(outTexture):
		srcModDate = datetime.datetime.fromtimestamp(os.path.gettime(srcFolder))
		dstModDate = datetime.datetime.fromtimestamp(os.path.gettime(outTexture))
		if srcModDate > dstModDate:
			return True
	return False

def assemble(srcFolder, outTexture, scale, maxSize, hasAlpha):
	texBaseName = os.path.basename(outTexture)
	extension = re.search(r'\.(.*)$', texBaseName).groups()[0].lower()
	pngFilePath = re.sub(r'\..*$', '.png', outTexture)
	doPkm = 'pkm' == extension and not hasAlpha
	doPvr = 'pvr.ccz' == extension and not hasAlpha

	if not wasTextureModified(srcFolder, outTexture):
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
		pvrFilePath = re.sub(r'\..*$', '.pvr', outTexture)
		subprocess.call([pvrConverter(),
		'-i', pngFilePath,
		'-o', pvrFilePath,
		'-f', 'PVRTC1_4_RGB',
		'-q', 'pvrtcbest',
		'-shh'])
		os.remove(pngFilePath)

		indata = open(pvrFilePath, 'rb').read()
		outdata = zlib.compress(indata, zlib.Z_BEST_COMPRESSION)
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
		if os.path.isdir(srcPath):
			assemble(srcPath, os.path.join(dstDirPath, name + '.' + fmt), scale, maxSize, hasAlpha)

def run():
	parser = argparse.ArgumentParser(prog='SPRITESHEET GENERATOR')
	parser.add_argument('-appRoot')
	parser.add_argument('-fmt')
	parser.add_argument('-lods', nargs='*', default=['HDR', 'HD', 'SD'])
	args = parser.parse_args()

	textureDir = os.path.join(os.path.join(args.appRoot, 'runtime/temp/Textures'), args.fmt)
	if not os.path.exists(textureDir):
		os.makedirs(textureDir)

	texSD

	