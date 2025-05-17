#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _
from . import E2Globals

from .E2SelectionList import E2PSelectionList, E2PSelectionEntryComponent
from .plugin import skin_path, cfg, hdr, hasConcurrent, hasMultiprocessing

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from enigma import ePoint, eTimer
from PIL import Image
# from requests.adapters import HTTPAdapter, Retry
from Screens.Screen import Screen

import datetime
import os
import time
import requests
import shutil

try:
    from http.client import HTTPConnection
    HTTPConnection.debuglevel = 0
except:
    from httplib import HTTPConnection
    HTTPConnection.debuglevel = 0


class E2Piconizer_SelectPicons(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        skin = os.path.join(skin_path, "e2piconizer_select.xml")

        with open(skin, "r") as f:
            self.skin = f.read()

        self.setup_title = _("Select Picons")
        self.downloadfolder = ""
        self.urls = []
        self.upscale = 1
        self.picon_list = []
        self.final_picon_list = []
        self.selectedindex = []
        self.preview = ""

        self["trimmarks"] = Pixmap()
        self["preview"] = Pixmap()

        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText("")
        self["key_yellow"] = StaticText("")
        self["key_blue"] = StaticText("")

        self["description"] = Label(_("Select the picons you wish to download. \nPress OK to toggle the selection."))
        self["piconsource"] = Label(_(cfg.source.value))

        self["text"] = Label(_("Downloading picon list. Please wait..."))

        self.selection_list = []
        self["list"] = E2PSelectionList(self.selection_list, enableWrapAround=True)
        self["list"].onSelectionChanged.append(self.getCurrentEntry)

        self.setupVariables()

        self["actions"] = ActionMap(["E2PiconizerActions"], {
            "red": self.keyCancel,
            "green": self.keyGreen,
            "yellow": self.sort,
            "blue": self["list"].toggleAllSelection,
            "cancel": self.keyCancel,
            "ok": self["list"].toggleSelection,
        }, -2)

        os.system("echo 1 > /proc/sys/vm/drop_caches")
        os.system("echo 2 > /proc/sys/vm/drop_caches")
        os.system("echo 3 > /proc/sys/vm/drop_caches")

        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.start)
        except:
            try:
                self.timer.callback.append(self.start)
            except:
                self.start()
        self.timer.start(50, True)

        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self.getCurrentEntry()

    def start(self):
        if self.urls != []:
            self.getJson()
            self.getHeader()
            self.getExtra()
        else:
            self.getLocal()

        self["key_green"].setText(_("Continue"))
        self["key_yellow"].setText(_("Sort Z-A"))
        self["key_blue"].setText(_("Toggle All"))

        self.selection_list = [E2PSelectionEntryComponent(str(x["title"]), str(x["last_modified_timestamp"]), str(x["last_modified_short"]), str(x["picon_url"]), str(x["index"]), x["selected"]) for x in self.final_picon_list]
        self["list"].setList(self.selection_list)

        self["list"].sort(sortType=0, flag=False)
        self["list"].moveToIndex(0)
        self.getCurrentEntry()
        self["text"].hide()

    def getCurrentEntry(self):
        if self.selection_list != []:
            self.currentSelection = self["list"].getSelectionIndex()
            self.selectedindex = int(self.selection_list[self.currentSelection][0][4])

            self.timer1 = eTimer()
            try:
                self.timer1_conn = self.timer1.timeout.connect(self.delayedDownload)
            except:
                try:
                    self.timer1.callback.append(self.delayedDownload)
                except:
                    self.delayedDownload()
            self.timer1.start(500, True)

    def delayedDownload(self):
        if cfg.source.value != "Local":
            if str(self.selection_list[self.currentSelection][0][3]).startswith("http"):
                self.downloadPreview()
                self.updatePreview(E2Globals.piconSize)
            else:
                self.temp = str(self.selection_list[self.currentSelection][0][3])
                self.updatePreview(E2Globals.piconSize)
        else:
            self.temp = str(self.selection_list[self.currentSelection][0][3])
            self.updatePreview(E2Globals.piconSize)

    def keyCancel(self):
        self.close()

    def keyGreen(self):
        if self["text"] == "":
            return
        else:
            from . import downloadpicons
            selected = self["list"].getSelectionsList()
            self.session.openWithCallback(self.close, downloadpicons.E2Piconizer_DownloadPicons, selected)

    def sort(self):
        if self["text"] == "":
            return
        else:
            current_sort = self["key_yellow"].getText()

            if current_sort == "Sort A-Z":
                self["key_yellow"].setText(_("Sort Z-A"))
                sort_type = 0
                reverse_flag = False
            if current_sort == "Sort Z-A":
                self["key_yellow"].setText(_("Sort Date"))
                sort_type = 0
                reverse_flag = True
            if current_sort == "Sort Date":
                self["key_yellow"].setText(_("Sort A-Z"))
                sort_type = 1
                reverse_flag = True

            self["list"].sort(sortType=sort_type, flag=reverse_flag)
            self["list"].moveToIndex(0)
            self.getCurrentEntry()

    def setupVariables(self):
        self.webapi = ""

        if cfg.quality.value == "normal":
            self.upscale = 1

        if cfg.quality.value == "large":
            self.upscale = 2

        gfxWidth = int(E2Globals.piconSize[0]) - int(cfg.padding.value) * 2 * int(self.upscale)
        gfxHeight = int(E2Globals.piconSize[1]) - int(cfg.padding.value) * 2 * int(self.upscale)

        if cfg.quality.value == "maximum":
            gfxWidth = 800
            gfxHeight = 800

        if cfg.source.value == "Sky UK":
            self.urls = []
            self.urls.append("https://awk.epgsky.com/hawk/linear/services/4101/1")  # uk london hd
            self.urls.append("https://awk.epgsky.com/hawk/linear/services/4104/50")  # ireland

            self.base = "services"
            self.ptitle = "t"
            self.sid = "sid"
            self.piconurl = "https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/" + str(gfxWidth) + "/" + str(gfxHeight) + "/skychb"
            self.webapi = "awk"

        if cfg.source.value == "Local":
            self.urls = []

    def fetch_url(self, url):
        r = ""
        response = ""

        try:
            r = requests.get(url, headers={"Content-Type": "application/json", 'Connection': 'Close'}, stream=True, verify=False)
            r.raise_for_status()
            if r.status_code == 200:
                try:
                    response = r.json()
                    return response
                except Exception as e:
                    print(e)
                    return ""

        except Exception as e:
            print(e)
            return ""

    def getJson(self):
        results = ""
        channels_all = ""

        threads = len(self.urls)
        if threads > 10:
            threads = 10

        self.result_list = []

        if hasConcurrent:
            try:
                from concurrent.futures import ThreadPoolExecutor
                executor = ThreadPoolExecutor(max_workers=threads)

                with executor:
                    results = executor.map(self.fetch_url, self.urls)
            except Exception as e:
                print(e)

        elif hasMultiprocessing:
            try:
                from multiprocessing.pool import ThreadPool
                pool = ThreadPool(threads)
                results = pool.imap(self.fetch_url, self.urls)
                pool.close()
                # pool.join()

            except Exception as e:
                print(e)

        for result in results:

            self.result_list.append(result)

        # copy the json channels into a seperate channel base list.
        channels_json = []

        if self.result_list:
            for result in self.result_list:
                if result:
                    try:
                        channels_json.append(result[self.base])
                    except Exception as e:
                        print(e)

        # combine uk & ROI json files
        if cfg.source.value == "Sky UK":
            channels_all = {x[self.ptitle]: x for x in channels_json[0] + channels_json[1] if "adult" in x and x['adult'] is False}.values()
        else:
            channels_all = channels_json[0]

        self.picon_list = []

        excludelist = [8040, 8266, 8025, 8346, 8459, 8331, 8301]

        for channel in channels_all:
            picon_values = {}

            if self.webapi == "awk":
                if int(channel[self.sid]) not in excludelist:
                    try:
                        picon_values["sid"] = channel[self.sid]
                        picon_values["title"] = channel[self.ptitle]
                        picon_values["picon_url"] = self.piconurl + str(picon_values["sid"]) + ".png"
                        picon_values["status"] = False
                    except:
                        continue

            picon_values["selected"] = True

            self.picon_list.append(picon_values)

    def getLastModifiedDate(self, picon_list):
        url = picon_list["picon_url"]
        if url != "":

            # session = requests.Session()

            response = ""
            jsonheaders = {"Content-Type": "application/json", 'Connection': 'Close'}

            try:
                r = requests.head(url, headers=jsonheaders, stream=True, verify=False)
                r.raise_for_status()
                if r.status_code == 200:
                    response = r.headers
                else:
                    return
            except Exception as e:
                print(e)
                if cfg.quality.value == "maximum":
                    try:
                        url = url.replace("/800", "/0")
                        r = requests.head(url, headers=jsonheaders, stream=True, verify=False)
                        r.raise_for_status()
                        if r.status_code == requests.codes.ok:
                            response = r.headers
                        else:
                            return
                    except Exception as e:
                        print(e)

            if response:
                if "Last-Modified" in response:
                    lastModified = response["Last-Modified"]
                    picon_list["last_modified"] = lastModified
                    picon_list["last_modified_timestamp"] = time.mktime(datetime.datetime.strptime(lastModified, "%a, %d %b %Y %H:%M:%S %Z").timetuple())
                    picon_list["last_modified_short"] = time.strftime("%d/%m/%Y", time.localtime(int(picon_list["last_modified_timestamp"])))
                else:
                    picon_list["last_modified"] = ""
                    picon_list["last_modified_timestamp"] = ""
                    picon_list["last_modified_short"] = ""

                picon_list["status"] = True
                picon_list["picon_url"] = url
                picon_list["index"] = self.index
                self.index += 1

                self.final_picon_list.append(picon_list)

    def getHeader(self):
        self.result_list = []
        self.index = 0

        threads = len(self.picon_list)
        if threads > 20:
            threads = 20

        if hasConcurrent:
            try:
                from concurrent.futures import ThreadPoolExecutor
                executor = ThreadPoolExecutor(max_workers=threads)

                with executor:
                    executor.map(self.getLastModifiedDate, self.picon_list)

            except Exception as e:
                print(e)

        elif hasMultiprocessing:
            try:
                from multiprocessing.pool import ThreadPool
                pool = ThreadPool(threads)
                pool.imap(self.getLastModifiedDate, self.picon_list)
                pool.close()
                pool.join()

            except Exception as e:
                print(e)

    def getLocal(self):
        locallist = [x for x in os.listdir(cfg.locallocation.value) if x.endswith(".png")]

        self.final_picon_list = []
        self.index = 0

        for local in locallist:
            picon_values = {}
            picon_values["sid"] = ""
            picon_values["title"] = local.split(".")[0]
            picon_values["picon_url"] = cfg.locallocation.value + local
            picon_values["selected"] = True
            picon_values["last_modified_timestamp"] = ""
            picon_values["last_modified_short"] = ""
            picon_values["index"] = self.index
            self.final_picon_list.append(picon_values)
            self.index += 1

    def getExtra(self):
        extralist = [x for x in os.listdir("/etc/enigma2/E2Piconizer/extra_picons/") if x.endswith(".png")]

        for extra in extralist:
            picon_values = {}
            picon_values["sid"] = ""
            picon_values["title"] = extra.split(".")[0]
            picon_values["picon_url"] = os.path.join("/etc/enigma2/E2Piconizer/extra_picons", extra)
            picon_values["selected"] = True
            picon_values["last_modified_timestamp"] = ""
            picon_values["last_modified_short"] = ""
            picon_values["index"] = self.index
            self.final_picon_list.append(picon_values)
            self.index += 1

    def downloadPreview(self):
        currentpicon = self.final_picon_list[self.selectedindex]["picon_url"]
        self.temp = "/tmp/temp.png"
        r = requests.get(currentpicon, headers=hdr, stream=True, verify=False)

        if r.status_code == 200:
            with open(self.temp, "wb") as f:
                try:
                    shutil.copyfileobj(r.raw, f)
                except:
                    self.temp = ""

    def updatePreview(self, piconSize):
        from . import buildgfx
        bg = buildgfx.createEmptyImage(piconSize)

        if cfg.background.value == "colour":
            bg = buildgfx.addColour(piconSize, cfg.colour.value, cfg.transparency.value)

        if cfg.background.value == "graphic":
            bg = buildgfx.addGraphic(piconSize, cfg.graphic.value)

        if self.temp:
            if cfg.reflection.value:
                im = buildgfx.createReflectedPreview(self.temp, piconSize, int(cfg.padding.value), int(cfg.reflectionstrength.value), int(cfg.reflectionsize.value))
            else:
                im = buildgfx.createPreview(self.temp, piconSize, int(cfg.padding.value))
        else:
            im = bg

        im = buildgfx.blendBackground(im, bg, cfg.background.value, cfg.reflection.value, int(cfg.offsety.value))

        if cfg.background.value != "transparent" and cfg.glass.value:
            im = buildgfx.addGlass(piconSize, cfg.glassgfx.value, im)

        if int(cfg.rounded.value) != 0:
            im = buildgfx.addCorners(im, int(cfg.rounded.value))

        self.savePicon(im)

    def savePicon(self, im):
        self.preview = "/tmp/preview.png"
        if cfg.bitdepth.value == "8bit":
            alpha = im.split()[-1]
            im = im.convert("RGB").convert("P", palette=Image.ADAPTIVE)
            mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
            im.paste(255, mask)
            im.save(self.preview, transparency=255)
            self.showPicon()
        else:
            im.save(self.preview, "PNG")
            self.showPicon()

    def showPicon(self):
        if self["preview"].instance:
            self["preview"].instance.setPixmapFromFile(self.preview)
            self["preview"].instance.move(ePoint(E2Globals.piconx + E2Globals.offsetx, E2Globals.picony + E2Globals.offsety))
            self["trimmarks"].instance.setPixmapFromFile(E2Globals.trimmarks)
