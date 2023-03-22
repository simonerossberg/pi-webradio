#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Pi-Webradio: Implementierung der Klasse Mpg123
#
# Die Klasse Mpg123 kapselt den mpg123-Prozess zum Abspielen von MP3s
#
# Quelle: (Author: Bernhard Bablok, License: GPL3, Website: https://github.com/bablokb/pi-webradio)
#
# -----------------------------------------------------------------------------

import threading, subprocess, signal, os, shlex, re, traceback
from threading import Thread
import queue, collections, time

from webradio import Base

class Mpg123(Base):
  """ mpg123 Steuerobjekt """

  def __init__(self,app):
    """ Initialisierung """

    self._app       = app
    self._api       = app.api
    self.debug      = app.debug
    self._process   = None
    self._op_event  = threading.Event()
    self._play      = False
    self._pause     = False
    self._volume    = -1
    self._mute      = False
    self._url       = None

    self.read_config()
    self.register_apis()

  # --- Konfiguration lesen   --------------------------------------------------

  def read_config(self):
    """ Konfiguration aus Konfigurationsdatei lesen """

    # Abschnitt [MPG123]
    self._vol_default = int(self.get_value(self._app.parser,"MPG123",
                                       "vol_default",30))
    self._volume      = self._vol_default
    self._vol_delta   = int(self.get_value(self._app.parser,"MPG123",
                                       "vol_delta",5))
    self._mpg123_opts = self.get_value(self._app.parser,"MPG123",
                                       "mpg123_opts","")

  # --- Register APIs   ------------------------------------------------------

  def register_apis(self):
    """ Register API-Funktionen """

    self._api.vol_up          = self.vol_up
    self._api.vol_down        = self.vol_down
    self._api.vol_set         = self.vol_set
    self._api.vol_mute_on     = self.vol_mute_on
    self._api.vol_mute_off    = self.vol_mute_off
    self._api.vol_mute_toggle = self.vol_mute_toggle
    self._api.bluetooth_start = self.bluetooth_start
    self._api.bluetooth_stop = self.bluetooth_stop

  # --- gibt den persistenten Zustand dieser Klasse zurück   -------------------------------

  def get_persistent_state(self):
    """ Persistenten Zustand zurückgeben (überschreibt SRBase.get_pesistent_state()) """
    return {
      'volume': self._volume if not self._mute else self._vol_old
      }

  # --- den persistenten Zustand dieser Klasse wiederherstellen   ------------------------------

  def set_persistent_state(self,state_map):
    """ persistenten Zustand wiederherstellen (überschreibt SRBase.set_pesistent_state()) """

    self.msg("Mpg123: persistenten Zustand wiederherstellen")
    if 'volume' in state_map:
      self._volume = state_map['volume']
    else:
      self._volume = self._vol_default
    self.msg("Mpg123: volume is: %d" % self._volume)

  # --- active-state (gibt beim Spielen true zurück)   --------------------------------

  def is_active(self):
    """ Rückkehr in den aktiven (spielenden) Zustand """

    return self._process is not None and self._process.poll() is None

  # --- Player im Hintergrund im Remote-Modus erstellen   ----------------------

  def create(self):
    """ neuer mpg123-Prozess """

    args = ["mpg123","-R"]
    opts = shlex.split(self._mpg123_opts)
    args += opts

    self.msg("Mpg123: Starten von mpg123 mit Args %r" % (args,))
    # start process with line-buffered stdin/stdout
    self._process = subprocess.Popen(args,bufsize=1,
                                     universal_newlines=True,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     errors='replace')
    self._reader_thread = Thread(target=self._process_stdout)
    self._reader_thread.start()
    self.vol_set(self._volume)

  # --- Spielen URL/file   -------------------------------------------------------

  def play(self,url,last=True):
    """ Starte die Wiedergabe, gebe True zurück, wenn eine neue Datei/URL gestartet wird """

    if self._process:
      if self._play:
        check_url = url if url.startswith("http") else os.path.basename(url)
        if check_url == self._url:   # spielt schon
          if not url.startswith("http"):
            self._op_event.clear()
            self._process.stdin.write("SAMPLE\n")
            self._op_event.wait()
          return False
        self.stop(last=False)        # da wir im Begriff sind, eine andere Datei abzuspielen
      self.msg("Mpg123: anfangen zu spielen %s" % url)
      self._last = last
      if url.startswith("http"):
        self._url   = url
      else:
        self._url   = os.path.basename(url)
      self._op_event.clear()
      if url.endswith(".m3u"):
        self._process.stdin.write("LOADLIST 0 %s\n" % url)
      else:
        self._process.stdin.write("LOAD %s\n" % url)
      self._op_event.wait()
      return True
    else:
      return False

  # --- Stoppen der Wiedergabe der aktuellen URL/Datei   ---------------------------------------

  def stop(self,last=True):
    """ Stopt spielen """

    if not self._play:
      return
    if self._process:
      self.msg("Mpg123: Stoppen der aktuellen Datei/url: %s" % self._url)
      self._last = last
      self._op_event.clear()
      self._process.stdin.write("STOP\n")
      self._op_event.wait()

  # --- Wiedergabe pausieren   -------------------------------------------------------

  def pause(self):
    """ Pause """

    if not self._url or self._pause:
      return
    if self._process:
      self.msg("Mpg123: Wiedergabe pausieren")
      if not self._pause:
        self._op_event.clear()
        self._process.stdin.write("PAUSE\n")
        self._op_event.wait()

  # --- Weiterspielen   ----------------------------------------------------

  def resume(self):
    """ weiterspielen """

    if not self._play and not self._pause:
      return
    if self._process:
      self.msg("Mpg123: weiterspielen")
      if self._pause:
        self._op_event.clear()
        self._process.stdin.write("PAUSE\n")
        self._op_event.wait()

  # --- Abspielen umschalten   ------------------------------------------------------

  def toggle(self):
    """ Abspielen umschalten """

    if not self._play:
      return
    if self._process:
      self.msg("Mpg123: Abspielen umschalten")
      self._op_event.clear()
      self._process.stdin.write("PAUSE\n")
      self._op_event.wait()

  # --- Stoppen Player   ---------------------------------------------------------

  def destroy(self):
    """ Zerstöre den aktuellen Player """

    if self._process:
      self.msg("Mpg123: Stoppen mpg123 ...")
      try:
        self._process.stdin.write("QUIT\n")
        self._process.wait(5)
        self.msg("Mpg123: ... fertig")
      except:
        # can't do anything about it
        self.msg("Mpg123: ... Ausnahme beim Zerstören von mpg123")
        pass

  # --- Prozessausgabe von mpg123   --------------------------------------------

  def _process_stdout(self):
    """ mpg123-Ausgabe lesen und verarbeiten """

    self.msg("Mpg123: Starten des mpg123 Reader-Threads")
    regex = re.compile(r".*ICY-META.*?'([^']*)';?.*\n")
    while True:
      try:
        line = self._process.stdout.readline()
        if not line:
          break;
      except:
        # catch e.g. decode-error
        continue
      if line.startswith("@F"):
        continue
      self.msg("Mpg123: Starten des mpg123 Reader-Threads: %s" % line)
      if line.startswith("@I ICY-META"):
        (line,_) = regex.subn(r'\1',line)
        self._api._push_event({'type': 'icy_meta',
                              'value': line})
      elif line.startswith("@I ICY-NAME"):
        self._api._push_event({'type': 'icy_name',
                              'value': line[13:].rstrip("\n")})
      elif line.startswith("@I ID3v2"):
        tag = line[9:].rstrip("\n").split(":")
        self._api._push_event({'type': 'id3',
                               'value': {'tag': tag[0],
                                         'value': tag[1]}})
      elif line.startswith("@P 0"):
        # @P 0 is not reliable
        if self._play:
          self._api._push_event({'type': 'eof',
                                 'value': {'name': self._url,
                                           'last': self._last}})
          self._url   = None
          self._pause = False
          self._play  = False
          self._op_event.set()
      elif line.startswith("@P 1"):
        self._pause = True
        self._api._push_event({'type': 'pause',
                              'value': self._url})
        self._op_event.set()
      elif line.startswith("@P 2"):
        self._play  = True
        self._pause = False
        self._api._push_event({'type': 'play',
                              'value': self._url})
        self._op_event.set()
      elif line.startswith("@SAMPLE"):
        sample = line.split()
        self._api._push_event({'type': 'sample',
                              'value': {'elapsed': int(sample[1])/int(sample[2]),
                                        'pause': self._pause}})
        self._op_event.set()

    self.msg("Mpg123: mpg123 Reader-Thread stoppen")

  # --- Lautstärke erhöhen   ----------------------------------------------------

  def vol_up(self,by=None):
    """ Erhöhung der Lautstärke um den Betrag oder den vorkonfigurierten Wert """

    if by:
      amount = max(0,int(by))     # nur positive Werte
    else:
      amount = self._vol_delta        # verwende den Standard
    self._volume = min(100,self._volume + amount)
    return self.vol_set(self._volume)

  # --- Lautstärke verringern   ----------------------------------------------------

  def vol_down(self,by=None):
    """ Verringern der Lautstärke um den Betrag oder den vorkonfigurierten Wert """

    if by:
      amount = max(0,int(amount))     # nur positive Werte
    else:
      amount = self._vol_delta        # verwende den Standard
    self._volume = max(0,self._volume - amount)
    return self.vol_set(self._volume)

  # --- Lautstärke einstellen   ---------------------------------------------------------

  def vol_set(self,val):
    """ Lautstärke einstellen """

    val = min(max(0,int(val)),100)
    self._volume = val
    if self._process:
      self.msg("Mpg123: Einstellen der aktuellen Lautstärke auf: %d%%" % val)
      self._process.stdin.write("VOLUME %d\n" % val)
      self._api._push_event({'type': 'vol_set',
                              'value': self._volume})
      return self._volume

  # --- stumm schalten  -------------------------------------------------------------

  def vol_mute_on(self):
    """ Stummschalten (d.h. Lautstärke auf Null stellen) """

    if not self._mute:
      self._vol_old = self._volume
      self._mute    = True
      return self.vol_set(0)

  # --- stumm aus  ------------------------------------------------------------

  def vol_mute_off(self):
    """ deactivate mute (i.e. set volume to last value) """

    if self._mute:
      self._mute = False
      return self.vol_set(self._vol_old)

  # --- stumm schalten   --------------------------------------------------------

  def vol_mute_toggle(self):
    """ stumm schalten """

    if self._mute:
      return self.vol_mute_off()
    else:
      return self.vol_mute_on()
    
  # --- start Bluetooth   ------------------------------------------------------- 
  
  def bluetooth_start(self):
    """ startet play """
    self.msg("Bluetooth start")

    
  # --- stop Bluetooth   -------------------------------------------------------

  def bluetooth_stop(self):
    """ stopt play (play->stop, pause->stop)"""
    self.msg("Bluetooth stop")
