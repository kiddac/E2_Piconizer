#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _
from . import E2Globals

from .plugin import skin_path, cfg, hdr, hasConcurrent, hasMultiprocessing, pythonVer
from unicodedata import normalize

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from enigma import eTimer
from PIL import Image
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

import io
import os
import re
import requests

try:
    from http.client import HTTPConnection
    HTTPConnection.debuglevel = 0
except:
    from httplib import HTTPConnection
    HTTPConnection.debuglevel = 0

if pythonVer == 3:
    unicode = str


class E2Piconizer_DownloadPicons(Screen):

    def __init__(self, session, selected):
        Screen.__init__(self, session)
        self.session = session
        self.selected = selected
        skin = os.path.join(skin_path, "e2piconizer_progress.xml")

        with open(skin, "r") as f:
            self.skin = f.read()

        self.setup_title = _("Downloadng Picons")

        self["action"] = Label(_("Building Picons..."))
        self["status"] = Label("")
        self["progress"] = ProgressBar()

        self["actions"] = ActionMap(["E2PiconizerActions"], {
            "cancel": self.keyCancel
        }, -2)

        self.job_current = 0
        self.job_picon_name = ""
        self.job_total = len(self.selected)
        self.picon_num = 0
        self.pause = 100
        self.complete = False
        self.onFirstExecBegin.append(self.start)

        self.processed = set()

        os.system("echo 1 > /proc/sys/vm/drop_caches")
        os.system("echo 2 > /proc/sys/vm/drop_caches")
        os.system("echo 3 > /proc/sys/vm/drop_caches")

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

    def keyCancel(self):
        self.close()

    def start(self):
        if self.job_total > 0:
            self.progresscount = self.job_total
            self.progresscurrent = 0
            self["progress"].setRange((0, self.progresscount))
            self["progress"].setValue(self.progresscurrent)

            self.timer = eTimer()
            try:
                self.timer_conn = self.timer.timeout.connect(self.buildPicons)
            except:
                try:
                    self.timer.callback.append(self.buildPicons)
                except:
                    self.buildPicons()
            self.timer.start(100, True)

        else:
            self.showError(_("No picons selected."))

    def fetch_url(self, url, i):
        try:
            response = requests.get(url[i][3], headers=hdr, stream=True, verify=False, timeout=10)

            if response.status_code == 200:
                image_file = io.BytesIO(response.content)
                piconname = self.selected[i][0]

                if pythonVer == 2:
                    piconname = normalize("NFKD", unicode(piconname, "utf_8", errors="ignore")).encode("ASCII", "ignore")
                elif pythonVer == 3:
                    piconname = normalize("NFKD", piconname).encode("ASCII", "ignore").decode()

                piconname = re.sub("[^a-z0-9]", "", piconname.replace("&", "and").replace("+", "plus").replace("*", "star").lower())
                self.makePicon(image_file, piconname)
        except Exception as e:
            print("fetch_url error", e)

    def log_result(self, result=None):
        self.progresscurrent += 1
        self["action"].setText(_("Making Funky Picons"))
        self["progress"].setValue(self.progresscurrent)
        self["status"].setText("Picon %d of %d" % (self.progresscurrent, self.job_total))

        if self.progresscurrent >= self.job_total:
            self.timer3 = eTimer()
            try:
                self.timer3_conn = self.timer3.timeout.connect(self.finished)
            except:
                try:
                    self.timer3.callback.append(self.finished)
                except:
                    self.finished()
            self.timer3.start(3000, True)

    def buildPicons(self):
        threads = min(len(self.selected), 10)

        if hasConcurrent:
            try:
                from concurrent.futures import ThreadPoolExecutor
                executor = ThreadPoolExecutor(max_workers=threads)

                for i in range(self.job_total):
                    if i in self.processed:
                        continue
                    self.processed.add(i)
                    if str(self.selected[i][3]).startswith("http"):
                        future = executor.submit(self.fetch_url, self.selected, i)
                    else:
                        future = executor.submit(self.makeLocalPicon, self.selected, i)
                    future.add_done_callback(self.log_result)
            except Exception as e:
                print("buildPicons error", e)

        elif hasMultiprocessing:
            try:
                from multiprocessing.pool import ThreadPool
                pool = ThreadPool(threads)
                for i in range(self.job_total):
                    if i in self.processed:
                        continue
                    self.processed.add(i)
                    if str(self.selected[i][3]).startswith("http"):
                        pool.apply_async(self.fetch_url, args=(self.selected, i), callback=self.log_result)
                    else:
                        pool.apply_async(self.makeLocalPicon, args=(self.selected, i), callback=self.log_result)
                pool.close()
            except Exception as e:
                print("buildPicons (multiprocessing) error", e)

    def finished(self):
        if not self.complete:
            self.session.openWithCallback(self.done, MessageBox, "Finished.\n\nRestart your GUI if downloaded to picons folder.\n\nYour created picons can be found in \n" + str(cfg.downloadlocation.value), MessageBox.TYPE_INFO, timeout=30)
            self.complete = True

    def showError(self, message):
        question = self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)
        question.setTitle(_("Create Picons"))
        self.close()

    def done(self, answer=None):
        self.close()

    def makeLocalPicon(self, lfile, i=None):
        try:
            image_file = lfile[i][3]
            piconname = lfile[i][0]

            if pythonVer == 2:
                piconname = normalize("NFKD", unicode(piconname, "utf_8", errors="ignore")).encode("ASCII", "ignore")
            elif pythonVer == 3:
                piconname = normalize("NFKD", piconname).encode("ASCII", "ignore").decode("ascii")

            piconname = re.sub("[^a-z0-9]", "", piconname.replace("&", "and").replace("+", "plus").replace("*", "star").lower())
            self.makePicon(image_file, piconname)
        except Exception as e:
            print("makeLocalPicon error", e)

    def makePicon(self, image_file, piconname):
        from . import buildgfx
        piconSize = E2Globals.piconSize
        bg = buildgfx.createEmptyImage(piconSize)

        if cfg.background.value == "colour":
            bg = buildgfx.addColour(piconSize, cfg.colour.value, cfg.transparency.value)

        if cfg.background.value == "graphic":
            bg = buildgfx.addGraphic(piconSize, cfg.graphic.value)

        try:
            if image_file:
                if cfg.reflection.value:
                    im = buildgfx.createReflectedPreview(image_file, piconSize, int(cfg.padding.value), int(cfg.reflectionstrength.value), int(cfg.reflectionsize.value))
                else:
                    im = buildgfx.createPreview(image_file, piconSize, int(cfg.padding.value))
            else:
                im = buildgfx.createEmptyImage(piconSize)
        except Exception as e:
            print("makePicon preview error", e)
            im = buildgfx.createEmptyImage(piconSize)

        try:
            im = buildgfx.blendBackground(im, bg, cfg.background.value, cfg.reflection.value, int(cfg.offsety.value))

            if cfg.background.value != "transparent" and cfg.glass.value:
                im = buildgfx.addGlass(piconSize, cfg.glassgfx.value, im)

            if int(cfg.rounded.value) != 0:
                im = buildgfx.addCorners(im, int(cfg.rounded.value))

            self.savePicon(im, piconname)
        except Exception as e:
            print("makePicon final blend/save error", e)

    def savePicon(self, im, piconname):
        try:
            if not os.path.exists(cfg.downloadlocation.value):
                os.makedirs(cfg.downloadlocation.value)

            path = os.path.join(cfg.downloadlocation.value, piconname + ".png")

            if cfg.bitdepth.value == "8bit":
                alpha = im.split()[-1]
                im = im.convert("RGB").convert("P", palette=Image.ADAPTIVE)
                mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
                im.paste(255, mask)
                im.save(path, transparency=255)
            else:
                im.save(path, optimize=True)
        except Exception as e:
            print("savePicon error", e)
