#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Pi-Webradio: Implementierung der Klasse EventFormatter
#
# Die Klasse EventFormatter wandelt Ereignisse in eine druckbare Form um
# 
#
# Quelle: (Author: Bernhard Bablok, License: GPL3, Website: https://github.com/bablokb/pi-webradio)
# Bearbeitet: Simone Roßberg
# -----------------------------------------------------------------------------

class EventFormatter(object):
  """ Veranstaltungen formatieren """

  # --- format map: type:format   ---------------------------------------------
  _FMT_MAP = {
    'version': 'pi-webradio version {value}',
    'icy_meta': '{value}',
    'icy_name': '{value}',
    'rec_start': 'recording {name} for {duration} minutes',
    'rec_stop': 'finished recording. File {file}, duration: {duration}m',
    'vol_set': 'setting current volume to {value}',
    'radio_play_channel': 'start playing channel {nr} ({name})',
    'play': 'playing {value}',
    'pause': 'pausing {value}',
    'file_info': '{name}: {total_pretty}',
    'id3': '{tag}: {value}',
    'keep_alive': 'current time: {value}',
    'eof': '{name} finished',
    'dir_select': 'current directory: {value}'
    }

  # --- Event formatieren   --------------------------------------------------------

  def format(self,event):
    """ gegebenes Ereignis formatieren """

    key = event['type']
    if key in EventFormatter._FMT_MAP:
      if isinstance(event['value'],dict):
        return EventFormatter._FMT_MAP[key].format(**event['value'])
      else:
        return EventFormatter._FMT_MAP[key].format(**event)
    else:
      return "%r" % event
