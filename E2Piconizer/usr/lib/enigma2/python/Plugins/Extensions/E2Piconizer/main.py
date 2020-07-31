#!/usr/bin/python
# -*- coding: utf-8 -*-


# from __future__ import absolute_import

# for localized messages
from . import _
from . import buildgfx
from . import selectpicons
from . import E2Globals

from .plugin import skin_path, cfg, testpicons_directory
from Components.ActionMap import NumberActionMap
from Components.config import config, getConfigListEntry, configfile
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from enigma import getDesktop, ePoint
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

screenwidth = getDesktop(0).size()


class E2Piconizer_Main(ConfigListScreen, Screen):

    def __init__(self, session):
        self.session = session

        skin = skin_path + 'e2piconizer_settings.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()

        self.setup_title = _('Settings')
        Screen.__init__(self, session)
        self['actions'] = NumberActionMap(['ColorActions', 'OkCancelActions', 'MenuActions'], {
            'red': self.cancel,
            'green': self.save,
            'yellow': self.reset,
            'cancel': self.cancel,
            'menu': self.cancel,
            'ok': self.ok}, -2)
        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('OK'))
        self['key_yellow'] = StaticText(_('Reset Position'))
        self['description'] = Label('')

        self.onChangedEntry = []
        self.list = []

        self.preview = ""

        self["trimmarks"] = Pixmap()
        self["preview"] = Pixmap()

        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self.initConfig()
        self.createSetup()
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)
        self.updatePreview(E2Globals.piconSize)

    def changedEntry(self):
        self.item = self['config'].getCurrent()
        for x in self.onChangedEntry:
            x()
        self.createSetup()
        self.updatePreview(E2Globals.piconSize)

    def initConfig(self):
        self.cfg_source = getConfigListEntry(_('Picon source'), cfg.source, _("Select the source of your picons.\n\nHorizon sources will only download a picon of max size 160 pixels wide.\nIf larger picon size selected it will just be centered at this size."))
        self.cfg_locallocation = getConfigListEntry(_('Offline picon location'), cfg.locallocation, _("Select the location of where your offline picon sources are located.\nPress 'OK' to change location."))
        self.cfg_downloadlocation = getConfigListEntry(_('Download location'), cfg.downloadlocation, _("Select the location of where to download picons to.\nPress 'OK' to change location.\nRecommended to download to a separate folder on your usb/hdd, then transfer and rename manually or via eChannelizer."))
        self.cfg_size = getConfigListEntry(_('Picon size'), cfg.size, _("Select the size of the picons."))
        self.cfg_testpicon = getConfigListEntry(_('Test picon'), cfg.testpicon, _("Select the picon to visualise how your picons will appear."))
        self.cfg_quality = getConfigListEntry(_('Download size'), cfg.quality, _('Select the size of the picon to be downloaded.\nLarger picon download helps reduce antialias edge jaggies.'))
        self.cfg_bitdepth = getConfigListEntry(_('Colour Palette'), cfg.bitdepth, _('Select the picon bit depth. 24bit is normal highest quality, 8bit is 256 max colours.'))
        self.cfg_background = getConfigListEntry(_('Background type'), cfg.background, _('Select the background for your picon.'))
        self.cfg_colour = getConfigListEntry(_('Background colour'), cfg.colour, _('Select background colour.'))
        self.cfg_transparency = getConfigListEntry(_('Background transparency'), cfg.transparency, _('Select the transparency of background colour.'))
        self.cfg_graphic = getConfigListEntry(_('Background graphic'), cfg.graphic, _('Select a graphic to use as a background for your picon set.\nBackground graphics live in /etc/engima2/e2piconizer/backgrounds. Minimum size must be 400 x 240 pixels.'))
        self.cfg_padding = getConfigListEntry(_('Padding'), cfg.padding, _('Select the padding around your picon graphic.\ni.e if using a background graphic.'))
        self.cfg_rounded = getConfigListEntry(_('Rounded corners'), cfg.rounded, _('Select the corner radius of your picon set.'))
        self.cfg_reflection = getConfigListEntry(_('Reflection'), cfg.reflection, _('Apply a mirror reflection to the graphic.'))
        self.cfg_reflectionstrength = getConfigListEntry(_('Reflection strength'), cfg.reflectionstrength, _('Adjust the strength/opacity of the picon reflection.'))
        self.cfg_reflectionsize = getConfigListEntry(_('Reflection size %'), cfg.reflectionsize, _('Adjust the height percent of the picon reflection.'))
        self.cfg_offsety = getConfigListEntry(_('Offset-Y'), cfg.offsety, _('Adjust the offset height of the picon and reflection.'))
        self.cfg_glass = getConfigListEntry(_('Glass effect'), cfg.glass, _('Apply a glass effect over the picon.'))
        self.cfg_glassgfx = getConfigListEntry(_('Glass graphic'), cfg.glassgfx, _('Select a graphic to use as the glass effect for your picon set.\nGlass graphics live in /etc/engima2/e2piconizer/glass. Minimum size must be 400 x 240 pixels.'))

    def createSetup(self):
        if cfg.size.value == "minipicons":
            E2Globals.piconSize = [50, 30]
            E2Globals.trimmarks = "/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/icons/trimmarks-50-30.png"

        if cfg.size.value == "picons":
            E2Globals.piconSize = [100, 60]
            E2Globals.trimmarks = "/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/icons/trimmarks-100-60.png"

        if cfg.size.value == "xpicons":
            E2Globals.piconSize = [220, 132]
            E2Globals.trimmarks = "/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/icons/trimmarks-220-132.png"

        if cfg.size.value == "zpicons":
            E2Globals.piconSize = [220, 88]
            E2Globals.trimmarks = "/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/icons/trimmarks-220-88.png"

        if cfg.size.value == "zzpicons1":
            E2Globals.piconSize = [400, 160]
            E2Globals.trimmarks = "/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/icons/trimmarks-400-160.png"

        if cfg.size.value == "zzpicons2":
            E2Globals.piconSize = [400, 170]
            E2Globals.trimmarks = "/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/icons/trimmarks-400-170.png"

        if cfg.size.value == "zzzpicons":
            E2Globals.piconSize = [400, 240]
            E2Globals.trimmarks = "/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/icons/trimmarks-400-240.png"

        self.testpicon = cfg.testpicon.value

        self.list = []
        self.list.append(self.cfg_source)
        if cfg.source.value == 'Local':
            self.list.append(self.cfg_locallocation)
        self.list.append(self.cfg_downloadlocation)
        self.list.append(self.cfg_size)
        self.list.append(self.cfg_testpicon)

        if cfg.source.value == 'Sky UK':
            self.list.append(self.cfg_quality)

        self.list.append(self.cfg_bitdepth)

        self.list.append(self.cfg_background)

        if cfg.background.value == 'colour':
            self.list.append(self.cfg_colour)
            self.list.append(self.cfg_transparency)

        if cfg.background.value == 'graphic':
            self.list.append(self.cfg_graphic)

        self.list.append(self.cfg_reflection)

        if cfg.reflection.value:
            self.list.append(self.cfg_reflectionstrength)
            self.list.append(self.cfg_reflectionsize)
            self.list.append(self.cfg_offsety)

        if cfg.background.value != 'transparent':
            self.list.append(self.cfg_glass)

            if cfg.glass.value:
                self.list.append(self.cfg_glassgfx)

        self.list.append(self.cfg_padding)

        if cfg.background.value != 'transparent':
            self.list.append(self.cfg_rounded)

        self['config'].list = self.list
        self['config'].l.setList(self.list)

    def save(self):
        if self['config'].isChanged():
            for x in self['config'].list:
                x[1].save()
            configfile.save()

        self.session.open(selectpicons.E2Piconizer_SelectPicons)

    def ok(self):
        ConfigListScreen.keyOK(self)
        sel = self['config'].getCurrent()[1]
        if sel and sel == cfg.downloadlocation:
            self.setting = 'download'
            self.openDirectoryBrowser(cfg.downloadlocation.value)

        if sel and sel == cfg.locallocation:
            self.setting = 'local'
            self.openDirectoryBrowser(cfg.locallocation.value)

        else:
            pass

    def openDirectoryBrowser(self, path):
        try:
            self.session.openWithCallback(
                self.openDirectoryBrowserCB,
                LocationBox,
                windowTitle=_("Choose Directory:"),
                text=_("Choose directory"),
                currDir=str(path),
                bookmarks=config.movielist.videodirs,
                autoAdd=False,
                editDir=True,
                inhibitDirs=["/bin", "/boot", "/dev", "/home", "/lib", "/proc", "/run", "/sbin", "/sys", "/var"],
                minFree=15)
        except Exception as e:
            print ('openDirectoryBrowser get failed: ', str(e))

    def openDirectoryBrowserCB(self, path):
        if path is not None:
            if self.setting == 'download':
                cfg.downloadlocation.setValue(path)

            if self.setting == 'local':
                cfg.locallocation.setValue(path)
        return

    def cancel(self, answer=None):
        if answer is None:
            if self['config'].isChanged():
                self.session.openWithCallback(self.cancel, MessageBox, _('Really close without saving settings?'))
            else:
                self.close()
        elif answer:
            for x in self['config'].list:
                x[1].cancel()
            self.close()
        return

    def reset(self):
        cfg.padding.value = 0
        cfg.colour.value = '000000'
        cfg.transparency.value = '80'
        cfg.rounded.value = 0
        cfg.offsety.value = 0
        cfg.reflectionsize.value = 50
        cfg.reflectionstrength.value = 1
        self.createSetup()
        self.updatePreview(E2Globals.piconSize)

    def updatePreview(self, piconSize):

        bg = buildgfx.createEmptyImage(piconSize)

        if screenwidth.width() > 1280:
            E2Globals.offsetx = max(0, (400 - piconSize[0]) // 2)
            E2Globals.offsety = max(0, (240 - piconSize[1]) // 2)
            E2Globals.piconx = 30
            E2Globals.picony = 519
        else:
            E2Globals.offsetx = max(0, (220 - piconSize[0]) // 2)
            E2Globals.offsety = max(0, (132 - piconSize[1]) // 2)
            E2Globals.piconx = 42
            E2Globals.picony = 360

        if cfg.background.value == 'colour':
            bg = buildgfx.addColour(piconSize, cfg.colour.value, cfg.transparency.value)

        if cfg.background.value == 'graphic':
            bg = buildgfx.addGraphic(piconSize, cfg.graphic.value)

        if cfg.reflection.value:
            im = buildgfx.createReflectedPreview(testpicons_directory + self.testpicon, piconSize, cfg.padding.value, cfg.reflectionstrength.value, cfg.reflectionsize.value)
        else:
            im = buildgfx.createPreview(testpicons_directory + self.testpicon, piconSize, cfg.padding.value)

        im = buildgfx.blendBackground(im, bg, cfg.background.value, cfg.reflection.value, cfg.offsety.value)

        if cfg.background.value != 'transparent' and cfg.glass.value:
            im = buildgfx.addGlass(piconSize, cfg.glassgfx.value, im)

        im = buildgfx.addCorners(im, cfg.rounded.value)

        self.savePicon(im)
        self.showPicon()

    def savePicon(self, im):
        self.preview = "/tmp/preview.png"
        im.save(self.preview, "PNG")

    def showPicon(self):
        self["preview"].instance.setPixmapFromFile(self.preview)
        self["preview"].instance.move(ePoint(E2Globals.piconx + E2Globals.offsetx, E2Globals.picony + E2Globals.offsety))
        self["trimmarks"].instance.setPixmapFromFile(E2Globals.trimmarks)
