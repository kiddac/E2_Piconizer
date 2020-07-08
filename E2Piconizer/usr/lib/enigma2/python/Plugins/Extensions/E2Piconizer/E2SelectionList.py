#!/usr/bin/python
# -*- coding: utf-8 -*-


# from __future__ import absolute_import

from .plugin import skin_path, screenwidth
from Components.MenuList import MenuList
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER
from Tools.LoadPixmap import LoadPixmap

import skin

selectiononpng = LoadPixmap(cached=True, path=skin_path + 'images/lock_on.png')
selectionoffpng = LoadPixmap(cached=True, path=skin_path + 'images/lock_off.png')


def E2PSelectionEntryComponent(channel, last_modified_timestamp, last_modified_short, piconurl, index, selected):

	if screenwidth.width() > 1280:
		dx, dy, dw, dh = skin.parameters.get('E2PSelectionListDescr', (68, 0, 900, 56))
		mx, my, mw, mh = skin.parameters.get('E2PSelectionListMod', (938, 0, 342, 56))
		ix, iy, iw, ih = skin.parameters.get('E2PSelectionListLock', (15, 11, 38, 36))
		ix, iy, iw, ih = skin.parameters.get('E2PSelectionListLockOff', (15, 11, 38, 36))
	else:
		dx, dy, dw, dh = skin.parameters.get('E2PSelectionListDescr', (45, 0, 600, 38))
		mx, my, mw, mh = skin.parameters.get('E2PSelectionListMod', (625, 0, 228, 38))
		ix, iy, iw, ih = skin.parameters.get('E2PSelectionListLock', (10, 8, 25, 24))
		ix, iy, iw, ih = skin.parameters.get('E2PSelectionListLockOff', (10, 8, 25, 24))

	res = [
		(channel, last_modified_timestamp, last_modified_short, piconurl, index, selected),
		(eListboxPythonMultiContent.TYPE_TEXT, dx, dy, dw, dh, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, channel)
	]

	res.append((eListboxPythonMultiContent.TYPE_TEXT, mx, my, mw, mh, 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, last_modified_short))

	if selected:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, ix, iy, iw, ih, selectiononpng))
	else:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, ix, iy, iw, ih, selectionoffpng))
	return res


class E2PSelectionList(MenuList):

	def __init__(self, list=None, enableWrapAround=False):
		MenuList.__init__(self, list or [], enableWrapAround, content=eListboxPythonMultiContent)

		font = skin.fonts.get('SelectionList', ('Regular', 20, 30))
		if screenwidth.width() <= 1280:
			font = skin.fonts.get('SelectionList', ('Regular', 14, 20))

		self.l.setFont(0, gFont(font[0], font[1]))

		self.l.setItemHeight(font[2])


	def toggleSelection(self):
		if len(self.list) > 0:
			idx = self.getSelectedIndex()
			item = self.list[idx][0]
			self.list[idx] = E2PSelectionEntryComponent(item[0], item[1], item[2], item[3], item[4], not item[5])
			self.setList(self.list)


	def getSelectionsList(self):
		return [(item[0][0], item[0][1], item[0][2], item[0][3], item[0][4]) for item in self.list if item[0][5]]


	def toggleAllSelection(self):
		for idx, item in enumerate(self.list):
			item = self.list[idx][0]
			self.list[idx] = E2PSelectionEntryComponent(item[0], item[1], item[2], item[3], item[4], not item[5])
		self.setList(self.list)


	def sort(self, sortType=False, flag=False):
		# sorting by sortType:
		# 0 - channel
		# 1 - last_modified_timestamp
		# 2 - last_modified_short
		# 3 - piconurl
		# 4 - index
		# 5 - selected
		self.list.sort(key=lambda x: x[0][sortType], reverse=flag)
		self.setList(self.list)

	def len(self):
		return len(self.list)
