from . import _
from . import buildgfx
from . import downloadpicons
from . import E2Globals

from .E2SelectionList import E2PSelectionList, E2PSelectionEntryComponent
from .plugin import skin_path, cfg, screenwidth, hdr

from Components.ActionMap import ActionMap, NumberActionMap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from enigma import getDesktop, eSize, ePoint, eTimer
from multiprocessing.pool import ThreadPool
from PIL import Image, ImageFile, PngImagePlugin
from Screens.Screen import Screen

import datetime
import json
import os
import time
import sys
import re


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


try:
    pythonVer = sys.version_info.major
except:
    pythonVer = 2

if pythonVer == 2:
    from urllib2 import urlopen, Request, HTTPError
else:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
    PngImagePlugin.ChunkStream.call = mycall
    PngImagePlugin.PngStream.chunk_TRNS = mychunk_TRNS


class E2Piconizer_SelectPicons(Screen):

    def __init__(self, session):

        self.session = session

        skin = skin_path + 'e2piconizer_select.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()

        self.setup_title = _('Select Picons')
        Screen.__init__(self, session)

        self.downloadfolder = ''
        self.urls = []
        self.upscale = 1
        self.picon_list = []
        self.selectedindex = []

        self.preview = ''

        self['trimmarks'] = Pixmap()
        self['preview'] = Pixmap()

        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText('')
        self['key_yellow'] = StaticText('')
        self['key_blue'] = StaticText('')

        self['description'] = Label(_('Select the picons you wish to download. \nPress OK to toggle the selection.'))
        self['piconsource'] = Label(_(cfg.source.value))

        self['text'] = Label(_('Downloading picon list. Please wait...'))

        self.selection_list = []
        self['list'] = E2PSelectionList(self.selection_list, enableWrapAround=True)
        self['list'].onSelectionChanged.append(self.getCurrentEntry)

        self.setupVariables()

        self['setupActions'] = ActionMap(['ColorActions', 'SetupActions', 'ChannelSelectEPGActions'], {
            'red': self.keyCancel,
            'green': self.keyGreen,
            'yellow': self.sort,
            'blue': self['list'].toggleAllSelection,
            'save': self.keyGreen,
            'cancel': self.keyCancel,
            'ok': self['list'].toggleSelection,
        }, -2)

        self.onFirstExecBegin.append(self.delayedLoad)

        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self.getCurrentEntry()

    def delayedLoad(self):
        if self.urls != []:
            self.getJson()
            self.getHeader()
            self.addHeader()
        else:
            self.getLocal()

        self['text'].hide()
        self['text'].setText('')
        self['key_green'].setText(_('Continue'))
        self['key_yellow'].setText(_('Sort Z-A'))
        self['key_blue'].setText(_('Toggle All'))

        self.selection_list = [E2PSelectionEntryComponent(str(x['title']), str(x['last_modified_timestamp']), str(x['last_modified_short']), str(x['picon_url']), str(x['index']), x['selected']) for x in self.picon_list]
        self['list'].setList(self.selection_list)

        self['list'].sort(sortType=0, flag=False)
        self['list'].moveToIndex(0)
        self.getCurrentEntry()

    def getCurrentEntry(self):
        if self.selection_list != []:
            self.currentSelection = self['list'].getSelectionIndex()
            self.selectedindex = int(self.selection_list[self.currentSelection][0][4])

            self.timer = eTimer()
            self.timer.timeout.get().append(self.delayedDownload)
            self.timer.start(500, True)

    def delayedDownload(self):
        if cfg.source.value != 'Local':
            self.downloadPreview()
            self.updatePreview(E2Globals.piconSize)
        else:
            self.temp = str(self.selection_list[self.currentSelection][0][3])
            self.updatePreview(E2Globals.piconSize)

    def keyCancel(self):
        self.close()

    def keyGreen(self):
        if self['text'] == '':
            return
        else:
            selected = self['list'].getSelectionsList()
            self.session.openWithCallback(self.close, downloadpicons.E2Piconizer_DownloadPicons, selected)

    def sort(self):
        if self['text'] == '':
            return
        else:
            current_sort = self['key_yellow'].getText()

            if current_sort == 'Sort A-Z':
                self['key_yellow'].setText(_('Sort Z-A'))
                sort_type = 0
                reverse_flag = False
            if current_sort == 'Sort Z-A':
                self['key_yellow'].setText(_('Sort Date'))
                sort_type = 0
                reverse_flag = True
            if current_sort == 'Sort Date':
                self['key_yellow'].setText(_('Sort A-Z'))
                sort_type = 1
                reverse_flag = True

            self['list'].sort(sortType=sort_type, flag=reverse_flag)
            self['list'].moveToIndex(0)
            self.getCurrentEntry()

    def setupVariables(self):
        self.webapi = ''

        if cfg.quality.value == 'normal':
            self.upscale = 1

        if cfg.quality.value == 'large':
            self.upscale = 2

        gfxWidth = int(E2Globals.piconSize[0]) - int(cfg.padding.value) * 2 * int(self.upscale)
        gfxHeight = int(E2Globals.piconSize[1]) - int(cfg.padding.value) * 2 * int(self.upscale)

        if cfg.quality.value == 'maximum':
            gfxWidth = 800
            gfxHeight = 800

        if cfg.source.value == 'Sky UK':
            self.urls = []
            self.urls.append('http://awk.epgsky.com/hawk/linear/services/4101/1')  # uk london hd
            self.urls.append('http://awk.epgsky.com/hawk/linear/services/4104/50')  # ireland

            self.base = 'services'
            self.ptitle = 't'
            self.sid = 'sid'
            self.piconurl = 'https://d2n0069hmnqmmx.cloudfront.net/epgdata/1.0/newchanlogos/' + str(gfxWidth) + '/' + str(gfxHeight) + '/skychb'
            self.webapi = 'awk'

        if cfg.source.value == 'Virgin UK':
            self.urls = []
            self.urls.append('https://web-api.horizon.tv/oesp/api/GB/eng/web/channels/')
            self.urls.append('https://web-api.horizon.tv/oesp/api/IE/eng/web/channels/')
            self.webapi = 'horizon'

        if cfg.source.value == 'Horizon AT':
            self.urls = ['https://web-api.horizon.tv/oesp/api/AT/deu/web/channels/']
            self.webapi = 'horizon'

        if cfg.source.value == 'Horizon CH':
            self.urls = ['https://web-api.horizon.tv/oesp/api/CH/eng/web/channels/']
            self.webapi = 'horizon'

        if cfg.source.value == 'Horizon CZ':
            self.urls = ['https://web-api.horizon.tv/oesp/api/CZ/ces/web/channels/']
            self.webapi = 'horizon'

        if cfg.source.value == 'Horizon DE':
            self.urls = ['https://web-api.horizon.tv/oesp/api/DE/deu/web/channels/']
            self.webapi = 'horizon'

        if cfg.source.value == 'Horizon HU':
            self.urls = ['https://web-api.horizon.tv/oesp/api/HU/hun/web/channels/']
            self.webapi = 'horizon'

        if cfg.source.value == 'Horizon NL':
            self.urls = ['https://web-api.horizon.tv/oesp/api/NL/nld/web/channels/']
            self.webapi = 'horizon'

        if cfg.source.value == 'Horizon PL':
            self.urls = ['https://web-api.horizon.tv/oesp/api/PL/pol/web/channels/']
            self.webapi = 'horizon'

        if cfg.source.value == 'Horizon RO':
            self.urls = ['https://web-api.horizon.tv/oesp/api/RO/ron/web/channels/']
            self.webapi = 'horizon'

        if cfg.source.value == 'Horizon SK':
            self.urls = ['https://web-api.horizon.tv/oesp/api/SK/slk/web/channels/']
            self.webapi = 'horizon'

        if self.webapi == 'horizon':
            self.ptitle = 'title'
            self.base = 'channels'
            self.sid = ''
            self.piconurl = ''

        if cfg.source.value == 'Local':
            self.urls = []

    def fetch_url(self, url, i):
        try:
            response = urlopen(url[i])
            return json.loads(response.read())
        except Exception as e:
            print(e)
            return None

    def log_result(self, result):
        self.result_list.append(result)

    def getJson(self):
        urllength = len(self.urls)
        pool = ThreadPool(20)
        self.result_list = []

        for i in range(urllength):
            pool.apply_async(self.fetch_url, args=(self.urls, i), callback=self.log_result)
        pool.close()
        pool.join()

        # copy the json channels into a seperate channel base list.
        channels_json = []
        for result in self.result_list:
            channels_json.append(result[self.base])

        channels_all = channels_json[0]

        # combine uk & ROI json files
        if cfg.source.value == 'Sky UK':

            # better syntax - but slower
            # channels_all = {x[self.ptitle]:x for x in channels_json[0] + channels_json[1]}.values()

            for ch2 in channels_json[1]:
                exists = False
                for ch1 in channels_json[0]:
                    if ch2[self.ptitle] == ch1[self.ptitle]:
                        exists = True
                        break
                if exists is False:
                    channels_all.append(ch2)

        # combine UK & ROI json files
        elif cfg.source.value == 'Virgin UK':

            # better syntax - but slower
            # channels_all = {x['stationSchedules'][0]['station'][self.ptitle]:x for x in channels_json[0] + channels_json[1]}.values()

            for ch2 in channels_json[1]:
                exists = False
                for ch1 in channels_json[0]:

                    if ch2['stationSchedules'][0]['station'][self.ptitle] == ch1['stationSchedules'][0]['station'][self.ptitle]:
                        exists = True
                        break
                if exists is False:
                    channels_all.append(ch2)

        else:
            channels_all = channels_json[0]

        self.picon_list = []

        for channel in channels_all:
            picon_values = {}

            if self.webapi == 'awk':
                picon_values['sid'] = channel[self.sid]
                picon_values['title'] = channel[self.ptitle]
                picon_values['picon_url'] = self.piconurl + str(picon_values['sid']) + '.png'
                picon_values['status'] = False

            if self.webapi == 'horizon':
                picon_values['sid'] = ''
                picon_values['title'] = channel['stationSchedules'][0]['station'][self.ptitle]
                picon_values['picon_url'] = ''
                picon_values['status'] = False
                for image in channel['stationSchedules'][0]['station']['images']:

                    if image['assetType'] == 'station-logo-large':
                        picon_values['picon_url'] = image['url'].split('?', 1)[0]
                        break

            picon_values['selected'] = True
            self.picon_list.append(picon_values)

    def getLastModifiedDate(self, picon_list, i):
        url = picon_list[i]['picon_url']
        if url != '':
            try:
                request = Request(url)
                request.get_method = lambda: 'HEAD'
                response = urlopen(request)

            except HTTPError as e:
                print(e)
                try:
                    url = url.replace('/800', '/0')
                    request = Request(url)
                    request.get_method = lambda: 'HEAD'
                    response = urlopen(request)

                except Exception as e:
                    print(e)
                    response = ''

            except Exception as e:
                print(e)
                response = ''

            if response != '':
                headers = response.info()
                if 'Last-Modified' in headers:
                    lastModified = headers.get('Last-Modified')
                    self.picon_list[i]['last_modified'] = lastModified
                    self.picon_list[i]['last_modified_timestamp'] = time.mktime(datetime.datetime.strptime(lastModified, '%a, %d %b %Y %H:%M:%S %Z').timetuple())
                    self.picon_list[i]['last_modified_short'] = time.strftime('%d/%m/%Y', time.localtime(int(self.picon_list[i]['last_modified_timestamp'])))
                else:
                    self.picon_list[i]['last_modified'] = ''
                    self.picon_list[i]['last_modified_timestamp'] = ''
                    self.picon_list[i]['last_modified_short'] = ''

                self.picon_list[i]['sid'] = self.picon_list[i]['sid']
                self.picon_list[i]['title'] = self.picon_list[i]['title']
                self.picon_list[i]['status'] = True
                self.picon_list[i]['picon_url'] = url
            else:
                self.picon_list[i]['status'] = False

    def getHeader(self):
        # presults = ThreadPool(20).imap(self.getLastModifiedDate, self.picon_list)
        urllength = len(self.picon_list)
        pool = ThreadPool(20)
        self.result_list = []

        for i in range(urllength):
            pool.apply_async(self.getLastModifiedDate, args=(self.picon_list, i))
        pool.close()
        pool.join()

    def addHeader(self):

        # remove status 404
        templist = [x for x in self.picon_list if not x['status'] is False]
        self.picon_list = templist

        # reindex list
        self.index = 0
        for picon in self.picon_list:
            picon['index'] = self.index
            self.index += 1

    def getLocal(self):
        locallist = [x for x in os.listdir(cfg.locallocation.value) if x.endswith(".png")]

        self.picon_list = []
        self.index = 0

        for local in locallist:
            picon_values = {}
            picon_values['sid'] = ''
            picon_values['title'] = local.split('.')[0]
            picon_values['picon_url'] = cfg.locallocation.value + local
            picon_values['selected'] = True
            picon_values['last_modified_timestamp'] = ''
            picon_values['last_modified_short'] = ''
            picon_values['index'] = self.index
            self.picon_list.append(picon_values)
            self.index += 1

    def downloadPreview(self):
        currentpicon = self.picon_list[self.selectedindex]['picon_url']
        self.temp = '/tmp/temp.png'
        imgRequest = Request(currentpicon, headers=hdr)

        with open(self.temp, 'wb') as f:
            try:
                f.write(urlopen(imgRequest).read())
                f.close()
            except:
                self.temp = ''

    def updatePreview(self, piconSize):
        bg = buildgfx.createEmptyImage(piconSize)

        if cfg.background.value == 'colour':
            bg = buildgfx.addColour(piconSize, cfg.colour.value, cfg.transparency.value)

        if cfg.background.value == 'graphic':
            bg = buildgfx.addGraphic(piconSize, cfg.graphic.value)

        if self.temp:
            if cfg.reflection.value:
                im = buildgfx.createReflectedPreview(self.temp, piconSize, cfg.padding.value, cfg.reflectionstrength.value, cfg.reflectionsize.value)
            else:
                im = buildgfx.createPreview(self.temp, piconSize, cfg.padding.value)
        else:
            im = bg

        im = buildgfx.blendBackground(im, bg, cfg.background.value, cfg.reflection.value, cfg.offsety.value)

        if cfg.background.value != 'transparent' and cfg.glass.value:
            im = buildgfx.addGlass(piconSize, cfg.glassgfx.value, im)

        if cfg.rounded != 0:
            im = buildgfx.addCorners(im, cfg.rounded.value)

        self.savePicon(im)

    def savePicon(self, im):
        self.preview = '/tmp/preview.png'
        if cfg.bitdepth.value == "8bit":
            alpha = im.split()[-1]
            im = im.convert('RGB').convert('P', palette=Image.ADAPTIVE)
            mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
            im.paste(255, mask)
            im.save(self.preview, transparency=255)
            self.showPicon()
        else:
            im.save(self.preview, 'PNG')
            self.showPicon()

    def showPicon(self):
        if self['preview'].instance:
            self['preview'].instance.setPixmapFromFile(self.preview)
            self["preview"].instance.move(ePoint(E2Globals.piconx + E2Globals.offsetx, E2Globals.picony + E2Globals.offsety))
            self["trimmarks"].instance.setPixmapFromFile(E2Globals.trimmarks)
