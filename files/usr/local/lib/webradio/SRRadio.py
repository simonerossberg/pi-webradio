#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Pi-Webradio: implementation of class Radio
#
# The class Radio implements the core functionality of the web-radio.
#
# (Quelle: Author: Bernhard Bablok, License: GPL3, Website: https://github.com/bablokb/pi-webradio)
#
# Bearbeitet Simone Roßberg
# -----------------------------------------------------------------------------

import os, time, datetime, shlex, json
import queue, collections
import threading, signal, subprocess, traceback

from webradio import *

class Radio(Base):
  """ Radiosteuerung """

  def __init__(self,app):
    """ Initialisierung """

    self._app          = app
    self._api          = app.api
    self.debug         = app.debug
    self._backend      = app.backend

    self._channel_nr   = 0                  # aktuelle Kanalnummer
    self._last_channel = 0                  # letzte aktive Kanalnummer
    self.stop_event    = app.stop_event
    self.read_config()
    self.register_apis()
    self.read_channels()

  # --- Konfiguration lesen   --------------------------------------------------

  def read_config(self):
    """ Konfiguration aus Konfigurationsdatei lesen """

    # section [GLOBAL]
    default_path        = "files/etc/pi-webradio.channels"
    self._channel_file  = self.get_value(self._app.parser,"GLOBAL","channel_file",
                                         default_path)

    # section [WEB]
    default_web_root = os.path.realpath(
      os.path.join(self._app.options.pgm_dir,"..","lib","webradio","web"))
    self._web_root  = self.get_value(self._app.parser,"WEB","web_root",
                                         default_web_root)

  # --- Register APIs   ------------------------------------------------------

  def register_apis(self):
    """ Register API-Funktionen """

    self._api.radio_on             = self.radio_on
    self._api.radio_off            = self.radio_off
    self._api.radio_pause          = self.radio_pause
    self._api.radio_resume         = self.radio_resume
    self._api.radio_toggle         = self.radio_toggle
    self._api.radio_get_channels   = self.radio_get_channels
    self._api.radio_get_channel    = self.radio_get_channel
    self._api.radio_play_channel   = self.radio_play_channel
    self._api.radio_play_next      = self.radio_play_next
    self._api.radio_play_prev      = self.radio_play_prev

  # --- gibt den persistenten Zustand dieser Klasse zurück   -------------------------------

  def get_persistent_state(self):
    """ Persistenten Zustand zurückgeben (überschreibt SRBase.get_pesistent_state()) """
    return {
      'channel_nr': self._last_channel
      }

  # --- den persistenten Zustand dieser Klasse wiederherstellen   ------------------------------

  def set_persistent_state(self,state_map):
    """ persistenten Zustand wiederherstellen (überschreibt SRBase.set_pesistent_state()) """

    self.msg("Radio: dauerhaften Zustand wiederherstellen")
    if 'channel_nr' in state_map:
      self._last_channel = state_map['channel_nr']

    self._api.update_state(section="radio",key="channel_nr",
                           value=self._last_channel,publish=False)

  # --- Kanäle lesen   -------------------------------------------------------

  def read_channels(self):
    """ Kanäle in eine Liste einlesen """

    self._channels = []
    try:
      self.msg("Radio: Laden von Kanälen von %s" % self._channel_file)
      f = open(self._channel_file,"r")
      self._channels = json.load(f)
      f.close()
      nr=1
      for channel in self._channels:
        channel['nr'] = nr
        logo_path = os.path.join(self._web_root,"images",channel['logo'])
        if os.path.exists(logo_path):
          channel['logo'] = os.path.join("images",channel['logo'])
        else:
          channel['logo'] = None
        nr += 1
    except:
      self.msg("Radio: Das Laden von Kanälen ist fehlgeschlagen")
      if self.debug:
        traceback.print_exc()

  # --- Kanalinfo abrufen   ----------------------------------------------------

  def radio_get_channel(self,nr=0):
    """ return info-dict {name,url,logo} für Kanal-Nr """

    try:
      nr = int(nr)
    except:
      nr = 0
    if nr == 0:
      if self._last_channel == 0:
        nr = 1
      else:
        nr = self._last_channel

    return dict(self._channels[nr-1])

  # --- Senderliste zurückgeben   ------------------------------------------------

  def radio_get_channels(self):
    """ vollständige Kanalliste zurückgeben """

    return [dict(c) for c in self._channels]

  # --- gegebenen Kanal spielen   --------------------------------------------------

  def radio_play_channel(self,nr=0):
    """ switch to given channel """

    channel = self.radio_get_channel(int(nr))
    nr      = channel['nr']
    self.msg("Radio: start playing channel %d (%s)" % (nr,channel['name']))

    # check if we have to do anything
    if self._backend.play(channel['url']):
      self._api.update_state(section="radio",key="channel_nr",
                             value=channel,publish=False)
      self._api._push_event({'type': 'radio_play_channel', 'value': channel})
      self._channel_nr   = nr
      self._last_channel = self._channel_nr
    else:
      self.msg("Radio: already on channel %d" % nr)
      # theoretically we could also have lost our backend
    return channel

  # --- switch to next channel   ----------------------------------------------

  def radio_play_next(self):
    """ switch to next channel """

    self.msg("Radio: switch to next channel")
    if self._channel_nr == 0:
      return self.radio_play_channel(0)
    elif self._channel_nr == len(self._channels):
      return self.radio_play_channel(1)
    else:
      return self.radio_play_channel(1+self._channel_nr)

  # --- switch to previous channel   ------------------------------------------


  def radio_play_prev(self):
    """ switch to previous channel """

    self.msg("Radio: switch to previous channel")
    if self._channel_nr == 0:
      return self.radio_play_channel(0)
    if self._channel_nr == 1:
      return self.radio_play_channel(len(self._channels))
    else:
      return self.radio_play_channel(self._channel_nr-1)

  # --- turn radio off   ------------------------------------------------------

  def radio_off(self):
    """ turn radio off """

    self.msg("Radio: turning radio off")
    self._channel_nr = 0
    self._backend.stop()

  # --- turn radio on   -------------------------------------------------------

  def radio_on(self):
    """ turn radio on """

    if self._channel_nr == 0:
      self.msg("Radio: turning radio on")
      self.radio_play_channel()
    else:
      self.msg("Radio: ignoring command, radio already on")

  # --- pause radio   ---------------------------------------------------------

  def radio_pause(self):
    """ pause playing """

    self.msg("Radio: pause playing")
    self._backend.pause()

  # --- pause radio   ---------------------------------------------------------

  def radio_resume(self):
    """ resume playing """

    self.msg("Radio: resume playing")
    self._backend.resume()

  # --- toggle radio state   --------------------------------------------------

  def radio_toggle(self):
    """ toggle playing """

    self.msg("Radio: toggle playing")
    self._backend.toggle()
