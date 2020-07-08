#!/usr/bin/python
# -*- coding: utf-8 -*-


# from __future__ import absolute_import

# for localized messages
from . import _
from . import E2Globals
from . import buildgfx

from .plugin import skin_path, cfg, hdr
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from enigma import eTimer
from multiprocessing.pool import ThreadPool
from PIL import Image
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

import io
import os
import re
import sys
import unicodedata


pythonVer = 2
if sys.version_info.major == 3:
	pythonVer = 3

if pythonVer == 2:
	from urllib2 import urlopen, Request
else:
	from urllib.request import urlopen, Request


class E2Piconizer_DownloadPicons(Screen):

	def __init__(self, session, selected):
		Screen.__init__(self, session)
		self.session = session
		self.selected = selected

		skin = skin_path + 'e2piconizer_progress.xml'
		with open(skin, 'r') as f:
			self.skin = f.read()

		Screen.setTitle(self, _('Downloadng Picons'))

		self['action'] = Label(_('Building Picons...'))
		self['status'] = Label('')
		self['progress'] = ProgressBar()
		self['actions'] = ActionMap(['SetupActions'], {'cancel': self.keyCancel}, -2)

		self.job_current = 0
		self.job_picon_name = ''
		self.job_total = len(self.selected)
		self.picon_num = 0
		self.pause = 100

		self.onFirstExecBegin.append(self.start)


	def keyCancel(self):
		self.close()


	def start(self):
		if self.job_total > 0:
			self.progresscount = self.job_total
			self.progresscurrent = 0
			self['progress'].setRange((0, self.progresscount))
			self['progress'].setValue(self.progresscurrent)
			self.timer = eTimer()
			self.timer.start(self.pause, 1)
			self.timer.callback.append(self.buildPicons)

		else:
			self.showError(_('No picons selected.'))


	def fetch_url(self, url, i):
		imgRequest = Request(url[i][3], headers=hdr)

		try:
			response = urlopen(imgRequest)
		except Exception as e:
			print(e)
			response = ""
			pass

		if response != "":

			image_file = io.BytesIO(response.read())

			piconname = self.selected[i][0]

			if pythonVer == 2:
				self.piconname = unicodedata.normalize('NFKD', unicode(piconname, 'utf_8', errors='ignore')).encode('ASCII', 'ignore')
			elif pythonVer == 3:
				piconname = unicodedata.normalize('NFKD', piconname).encode('ASCII', 'ignore').decode('ascii')

			piconname = re.sub('[^a-z0-9]', '', piconname.replace('&', 'and').replace('+', 'plus').replace('*', 'star').lower())
			self.timer3 = eTimer()
			self.timer3.start(self.pause, 1)
			self.timer3.callback.append(self.makePicon(image_file, piconname))


	def log_result(self, result):
		self.result_list.append(result)
		self['action'].setText(_('Making Funky Picons'))
		self.progresscurrent += 1
		self['progress'].setValue(self.progresscurrent)
		self['status'].setText('Picon %d of %d' % (self.progresscurrent, self.job_total))

		if self.progresscurrent == self.selectedlength:
			self.timer3 = eTimer()
			self.timer3.start(3000, 1)
			self.timer3.timeout.get().append(self.finished())


	def buildPicons(self):
		self.selectedlength = len(self.selected)
		pool = ThreadPool(20)
		self.result_list = []

		if cfg.source.value != 'Local':
			for i in range(self.selectedlength):
				pool.apply_async(self.fetch_url, args=(self.selected, i), callback=self.log_result)
			pool.close()
		else:
			for i in range(self.selectedlength):
				pool.apply_async(self.makeLocalPicon, args=(self.selected, i), callback=self.log_result)
			pool.close()


	def finished(self):
		self.session.openWithCallback(self.done, MessageBox, 'Finished.\n\nRestart your GUI if downloaded to picons folder.\n\nYour created picons can be found in \n' + str(cfg.downloadlocation.value) + '\n\nUse E-Channelizer to correctly assign your picons to your channels.', MessageBox.TYPE_INFO, timeout=30)


	def showError(self, message):
		question = self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)
		question.setTitle(_('Create Picons'))
		self.close()


	def done(self, answer=None):
		self.close()


	def makeLocalPicon(self, lfile, i):
		image_file = lfile[i][3]
		piconname = lfile[i][0]
		piconname = piconname.encode('ASCII', 'ignore').lower()
		piconname = re.sub('[^a-z0-9]', '', piconname.replace('&', 'and').replace('+', 'plus').replace('*', 'star').lower())

		self.timer3 = eTimer()
		self.timer3.start(self.pause, 1)
		self.timer3.callback.append(self.makePicon(image_file, piconname))


	def makePicon(self, piconfile, piconname):
		filename = piconfile
		piconSize = E2Globals.piconSize
		bg = buildgfx.createEmptyImage(piconSize)

		"""
		if cfg.source.value != 'Local':
			picon_location = tempdirectory + "/"
		else:
			picon_location = cfg.locallocation.value
			"""

		if cfg.background.value == 'colour':
			bg = buildgfx.addColour(piconSize, cfg.colour.value, cfg.transparency.value)

		if cfg.background.value == 'graphic':
			bg = buildgfx.addGraphic(piconSize, cfg.graphic.value)

		if filename:
			if cfg.reflection.value:
				try:
					im = buildgfx.createReflectedPreview(filename, piconSize, cfg.padding.value, cfg.reflectionstrength.value, cfg.reflectionsize.value)
				except:
					im = buildgfx.createEmptyImage(piconSize)
					pass
			else:
				try:
					im = buildgfx.createPreview(filename, piconSize, cfg.padding.value)
				except:
					im = buildgfx.createEmptyImage(piconSize)
					pass
		else:
			im = buildgfx.createEmptyImage(piconSize)

		im = buildgfx.blendBackground(im, bg, cfg.background.value, cfg.reflection.value, cfg.offsety.value)

		if cfg.background.value != 'transparent' and cfg.glass.value:
			im = buildgfx.addGlass(piconSize, cfg.glassgfx.value, im)

		im = buildgfx.addCorners(im, cfg.rounded.value)
		self.timer1 = eTimer()
		self.timer1.start(self.pause, 1)
		self.timer1.callback.append(self.savePicon(im, piconname))


	def savePicon(self, im, piconname):

		if not os.path.exists(cfg.downloadlocation.value):
			os.makedirs(cfg.downloadlocation.value)

		if cfg.bitdepth.value == "8bit":

			alpha = im.split()[-1]
			im = im.convert('RGB').convert('P', palette=Image.ADAPTIVE)
			mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
			im.paste(255, mask)
			im.save(cfg.downloadlocation.value + '/' + piconname + ".png", transparency=255)
		else:
			im.save(cfg.downloadlocation.value + '/' + piconname + ".png", optimize=True)
