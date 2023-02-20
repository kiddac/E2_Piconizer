#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _
from . import E2Globals
from . import buildgfx

from .plugin import skin_path, cfg, hdr, hasConcurrent, hasMultiprocessing
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from enigma import eTimer
from PIL import Image, ImageFile, PngImagePlugin
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

import io
import os
import re
import sys
import unicodedata


_simple_palette = re.compile(b"^\xff*\x00\xff*$")


def mycall(self, cid, pos, length):
    if cid.decode("ascii") == "tRNS":
        return self.chunk_TRNS(pos, length)
    else:
        return getattr(self, "chunk_" + cid.decode("ascii"))(pos, length)


def mychunk_TRNS(self, pos, length):
    s = ImageFile._safe_read(self.fp, length)
    if self.im_mode == "P":
        if _simple_palette.match(s):
            i = s.find(b"\0")
            if i >= 0:
                self.im_info["transparency"] = i
        else:
            self.im_info["transparency"] = s
    elif self.im_mode in ("1", "L", "I"):
        self.im_info["transparency"] = i16(s)
    elif self.im_mode == "RGB":
        self.im_info["transparency"] = i16(s), i16(s, 2), i16(s, 4)
    return s


pythonVer = 2
if sys.version_info.major == 3:
    pythonVer = 3

if pythonVer == 2:
    from urllib2 import urlopen, Request
else:
    from urllib.request import urlopen, Request
    PngImagePlugin.ChunkStream.call = mycall
    PngImagePlugin.PngStream.chunk_TRNS = mychunk_TRNS


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
        self.complete = False

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
            response = urlopen(imgRequest, timeout=10)
        except Exception as e:
            print(e)
            response = ""

        if response != "":

            image_file = io.BytesIO(response.read())

            piconname = self.selected[i][0]

            if pythonVer == 2:
                piconname = unicodedata.normalize('NFKD', unicode(piconname, 'utf_8', errors='ignore')).encode('ASCII', 'ignore')
            elif pythonVer == 3:
                piconname = unicodedata.normalize('NFKD', piconname).encode('ASCII', 'ignore').decode('ascii')

            piconname = re.sub('[^a-z0-9]', '', piconname.replace('&', 'and').replace('+', 'plus').replace('*', 'star').lower())
            self.timer3 = eTimer()
            self.timer3.start(self.pause, 1)
            self.timer3.callback.append(self.makePicon(image_file, piconname))

    def log_result(self, result=None):
        self.progresscurrent += 1
        self['action'].setText(_('Making Funky Picons'))
        self['progress'].setValue(self.progresscurrent)
        self['status'].setText('Picon %d of %d' % (self.progresscurrent, self.job_total))
        if self.progresscurrent == self.job_total - 1 or self.progresscurrent == self.job_total:
            self.timer3 = eTimer()
            self.timer3.start(3000, 1)
            self.timer3.timeout.get().append(self.finished())

    def buildPicons(self):

        if hasConcurrent:
            print("******* trying concurrent futures 1 ******")
            try:
                from concurrent.futures import ThreadPoolExecutor
                executor = ThreadPoolExecutor(max_workers=30)

                if cfg.source.value != 'Local':
                    for i in range(self.job_total):
                        piconname = self.selected[i]
                        print("*** piconname ", i, piconname)
                        try:
                            results = executor.submit(self.fetch_url, self.selected, i)
                            results.add_done_callback(self.log_result)
                        except Exception as e:
                            print("********** ERROR ", e)
                else:
                    for i in range(self.job_total):
                        try:
                            results = executor.submit(self.makeLocalPicon, self.selected, i)
                            results.add_done_callback(self.log_result)
                        except Exception as e:
                            print("********** ERROR ", e)

            except Exception as e:
                print(e)

        elif hasMultiprocessing:
            try:
                print("*** trying multiprocessing ThreadPool 1 ***")
                from multiprocessing.pool import ThreadPool
                pool = ThreadPool(30)

                if cfg.source.value != 'Local':
                    for i in range(self.job_total):
                        piconname = self.selected[i]
                        print("*** piconname ", i, piconname)
                        pool.apply_async(self.fetch_url, args=(self.selected, i), callback=self.log_result)
                else:
                    for i in range(self.job_total):
                        pool.apply_async(self.makeLocalPicon, args=(self.selected, i), callback=self.log_result)
                pool.close()

            except Exception as e:
                print(e)

    def finished(self):
        if self.complete is False:
            self.session.openWithCallback(self.done, MessageBox, 'Finished.\n\nRestart your GUI if downloaded to picons folder.\n\nYour created picons can be found in \n' + str(cfg.downloadlocation.value) + '\n\nUse E-Channelizer to correctly assign your picons to your channels.', MessageBox.TYPE_INFO, timeout=30)
            self.complete = True

    def showError(self, message):
        question = self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)
        question.setTitle(_('Create Picons'))
        self.close()

    def done(self, answer=None):
        self.close()

    def makeLocalPicon(self, lfile, i=None):
        image_file = lfile[i][3]
        piconname = lfile[i][0]

        if pythonVer == 2:
            piconname = unicodedata.normalize('NFKD', unicode(piconname, 'utf_8', errors='ignore')).encode('ASCII', 'ignore')
        elif pythonVer == 3:
            piconname = unicodedata.normalize('NFKD', piconname).encode('ASCII', 'ignore').decode('ascii')

        piconname = re.sub('[^a-z0-9]', '', piconname.replace('&', 'and').replace('+', 'plus').replace('*', 'star').lower())

        self.timer3 = eTimer()
        self.timer3.start(self.pause, 1)
        self.timer3.callback.append(self.makePicon(image_file, piconname))

    def makePicon(self, piconfile, piconname):
        filename = piconfile
        piconSize = E2Globals.piconSize
        bg = buildgfx.createEmptyImage(piconSize)

        if cfg.background.value == 'colour':
            bg = buildgfx.addColour(piconSize, cfg.colour.value, cfg.transparency.value)

        if cfg.background.value == 'graphic':
            bg = buildgfx.addGraphic(piconSize, cfg.graphic.value)

        if filename:
            if cfg.reflection.value:
                try:
                    im = buildgfx.createReflectedPreview(filename, piconSize, int(cfg.padding.value), int(cfg.reflectionstrength.value), int(cfg.reflectionsize.value))
                except:
                    im = buildgfx.createEmptyImage(piconSize)
                    pass
            else:
                try:
                    im = buildgfx.createPreview(filename, piconSize, int(cfg.padding.value))
                except:
                    im = buildgfx.createEmptyImage(piconSize)
                    pass
        else:
            im = buildgfx.createEmptyImage(piconSize)

        im = buildgfx.blendBackground(im, bg, cfg.background.value, cfg.reflection.value, int(cfg.offsety.value))

        if cfg.background.value != 'transparent' and cfg.glass.value:
            im = buildgfx.addGlass(piconSize, cfg.glassgfx.value, im)

        if int(cfg.rounded.value) != 0:
            im = buildgfx.addCorners(im, int(cfg.rounded.value))

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
