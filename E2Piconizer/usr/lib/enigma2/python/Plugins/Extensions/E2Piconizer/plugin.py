#!/usr/bin/python
# -*- coding: utf-8 -*-


# from __future__ import absolute_import

# for localized messages
from . import _


from Components.config import config, ConfigSelection, ConfigSubsection, ConfigYesNo, ConfigSelectionNumber,ConfigDirectory
from enigma import getDesktop
from Plugins.Plugin import PluginDescriptor
import os



screenwidth = getDesktop(0).size()


if screenwidth.width() > 1280:
	skin_directory = '/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/skin/fhd/'
else:
	skin_directory = '/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/skin/hd/'

skin_path = skin_directory + 'default/'
graphic_directory = '/etc/enigma2/E2Piconizer/backgrounds/'
graphics = os.listdir(graphic_directory)

glass_directory = '/etc/enigma2/E2Piconizer/glass/'
glass = os.listdir(glass_directory)

testpicons_directory = '/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/testpicons/'
testpicons = os.listdir(testpicons_directory)

tempdirectory = '/var/volatile/tmp/tempdownload'

hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

SourceList = [
	('Sky UK', 'Sky UK/IE'),
	('Virgin UK', 'Virgin UK/IE'),
	('Horizon AT', _('Horizon TV (AT) - Austrian / German')),
	('Horizon CH', _('Horizon TV (CH) - Swiss / German / French / Italian')),
	('Horizon CZ', _('Horizon TV (CZ) - Czech')),
	('Horizon DE', _('Horizon TV (DE) - German')),
	('Horizon HU', _('Horizon TV (HU) - Hungarian')),
	('Horizon NL', _('Horizon TV (NL) - Dutch')),
	('Horizon PL', _('Horizon TV (PL) - Polish')),
	('Horizon RO', _('Horizon TV (RO) - Romanian')),
	('Horizon SK', _('Horizon TV (SK) - Slovakian')),
	('Local',      _('Local media folder')),
	]

SizeList = [
	('minipicons', _('MiniPicons - 50x30 Pixel')),
	('picons', _('Picons - 100x60 Pixel')),
	('xpicons', _('XPicons - 220x132 Pixel')),
	('zpicons', _('ZPicons - 220x88 Pixel (Display Duo2)')),
	('zzpicons1', _('ZZPicons1 - 400x160 bzw')),
	('zzpicons2', _('ZZPicons2 - 400x170 Pixel')),
	('zzzpicons', _('ZZZPicons - 400x240 Pixel')),
	]

if screenwidth.width() <= 1280:
	SizeList = [
		('minipicons', _('MiniPicons - 50x30 Pixel')),
		('picons', _('Picons - 100x60 Pixel')),
		('xpicons', _('XPicons - 220x132 Pixel')),
		('zpicons', _('ZPicons - 220x88 Pixel (Display Duo2)')),
		]


ColourList = [
	("F0A30A", _("Amber")),
	("825A2C", _("Brown")),
	("5E0901", _("Burgundy")),
	("0050EF", _("Cobalt")),
	("911D10", _("Crimson")),
	("1BA1E2", _("Cyan")),
	("00008B", _("Dark Blue")),
	("2F1A09", _("Dark Brown")),
	("0F0F0F", _("Dark Grey")),
	("A61D4D", _("Magenta")),
	("A4C400", _("Lime")),
	("6A00FF", _("Indigo")),
	("5FA816", _("Bright Green")),
	("70AD11", _("Green")),
	("009A93", _("Turquoise")),
	("008A00", _("Emerald")),
	("76608A", _("Mauve")),
	("FF5A00", _("Mandarin")),
	("0000CD", _("Medium Blue")),
	("0A173A", _("Midnight")),
	("000080", _("Navy")),
	("6D8764", _("Olive")),
	("C3461B", _("Orange")),
	("F472D0", _("Pink")),
	("E51400", _("Red")),
	("27408B", _("Royal Blue")),
	("7A3B3F", _("Sienna")),
	("647687", _("Steel")),
	("149BAF", _("Teal")),
	("6C0AAB", _("Violet")),
	("D8C100", _("Bright Yellow")),
	("BF9217", _("Yellow")),
	("000000", _("Black")),
	("151515", _("Greyscale 1")),
	("1C1C1C", _("Greyscale 2")),
	("2E2E2E", _("Greyscale 3")),
	("424242", _("Greyscale 4")),
	("585858", _("Greyscale 5")),
	("6E6E6E", _("Greyscale 6")),
	("848484", _("Greyscale 7")),
	("A4A4A4", _("Greyscale 8")),
	("BDBDBD", _("Greyscale 9")),
	("D8D8D8", _("Greyscale 10")),
	("E6E6E6", _("Greyscale 11")),
	("F2F2F2", _("Greyscale 12")),
	("FAFAFA", _("Greyscale 13")),
	("FFFFFF", _("White"))
	]

TransparencyList = [
	("FF", "0%"),
	("F4", "5%"),
	("E7", "10%"),
	("DA", "15%"),
	("CD", "20%"),
	("C0", "25%"),
	("B4", "30%"),
	("A7", "35%"),
	("9A", "40%"),
	("8D", "45%"),
	("80", "50%"),
	("74", "55%"),
	("67", "60%"),
	("5A", "65%"),
	("4D", "70%"),
	("40", "75%"),
	("34", "80%"),
	("27", "85%"),
	("1A", "90%"),
	("0D", "95%"),
	("00", "100%")
	]

config.plugins.E2Piconizer = ConfigSubsection()
cfg = config.plugins.E2Piconizer

cfg.source = ConfigSelection(default='Sky UK', choices=SourceList)
cfg.size = ConfigSelection(default='xpicons', choices=SizeList)
cfg.testpicon = ConfigSelection(default='picon1.png', choices=testpicons)
cfg.quality = ConfigSelection(default='normal', choices=[('normal', _('Normal')), ('large', _('Large (slower)')), ('maximum', _('Maximum (slow)'))])
cfg.background = ConfigSelection(default='transparent', choices=[('transparent', _('Transparent')), ('colour', _('Colour')), ('graphic', _('Graphic'))])

cfg.colour = ConfigSelection(default='000000', choices=ColourList)
cfg.transparency = ConfigSelection(default='80', choices=TransparencyList)
cfg.graphic = ConfigSelection(default='default.png', choices=graphics)

cfg.reflection = ConfigYesNo(default=False)
cfg.reflectionsize = ConfigSelectionNumber(10, 100, 10, default=50)
cfg.reflectionstrength = ConfigSelectionNumber(1, 3, 1, default=1)
cfg.offsety = ConfigSelectionNumber(-50, 50, 2, default=0)

cfg.glass = ConfigYesNo(default=False)
cfg.glassgfx = ConfigSelection(default='mirror-glass.png', choices=glass)

cfg.padding = ConfigSelectionNumber(0, 50, 2, default=0)
cfg.rounded = ConfigSelectionNumber(0, 50, 2, default=0)

cfg.downloadlocation = ConfigDirectory(default='/etc/enigma2/E2Piconizer/downloads/')
cfg.locallocation = ConfigDirectory(default='/etc/enigma2/E2Piconizer/local_source/')

cfg.bitdepth = ConfigSelection(default='24bit', choices=[('24bit', _('24 bit full colour')), ('8bit', _('8 bit 256 indexed colours'))])


def main(session, **kwargs):
	from . import main
	session.open(main.E2Piconizer_Main)


def mainmenu(menuid, **kwargs):
	if menuid == 'mainmenu':
		return [(_("E2 Piconizer"), main, 'E2Piconizer', 4)]
	else:
		return []


def Plugins(**kwargs):
	# add_skin_font()
	iconFile = 'icons/e2piconizer.png'
	if screenwidth.width() > 1280:
		iconFile = 'icons/e2piconizerFHD.png'

	description = _('KiddaC - Picon Downloader / Creator')
	name = _('E2Piconizer')
	# main_menu = PluginDescriptor(name = name, description = description, where= PluginDescriptor.WHERE_MENU, fnc=mainmenu, needsRestart=True)

	result = [PluginDescriptor(name=name, description=description, where=PluginDescriptor.WHERE_PLUGINMENU, icon=iconFile, fnc=main)]

	# result.append(main_menu)
	return result
