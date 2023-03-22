#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Pi-Webradio: implementation of class Player
#
# The class Player implements the playback device for existing recordings
#
# Quelle: (Author: Bernhard Bablok, License: GPL3, Website: https://github.com/bablokb/pi-webradio)
# Bearbeitet: Simone Roßberg
# -----------------------------------------------------------------------------

import os, time, datetime, subprocess, threading, copy, queue

from webradio import Base

class Player(Base):
  """ Player-Controller """

  def __init__(self,app):
    """ Initialisierung """

    self._app     = app
    self.debug    = app.debug
    self._api     = app.api
    self._backend = app.backend

    self._lock        = threading.Lock()
    self._file        = None
    self._dirinfo     = None
    self._dirplay     = None
    self._dirstop     = threading.Event()
    self._init_thread = None

    self.read_config()
    self.register_apis()

  # --- Konfiguration lesen   --------------------------------------------------

  def read_config(self):
    """ Konfiguration aus Konfigurationsdatei lesen """
Standardverzeichnis
    # Section [PLAYER]
    self._wait_dir = int(self.get_value(self._app.parser,"PLAYER",
                                        "player_wait_dir",10))
    self._root_dir = self.get_value(self._app.parser,"PLAYER",
                                    "player_root_dir",
                                    os.path.expanduser("~"))
    self._root_dir = os.path.abspath(self._root_dir)

    self._def_dir = self.get_value(self._app.parser,"PLAYER",
                                    "player_def_dir",
                                    self._root_dir)
    self._def_dir = os.path.abspath(self._def_dir)

    self._dir = self._def_dir
    self.msg("Player: Stammverzeichnis:    %s" % self._root_dir)
    self.msg("Player: Standardverzeichnis: %s" % self._def_dir)

  # --- Register APIs   ------------------------------------------------------

  def register_apis(self):
    """ Register API-Funktionen """

    self._api.player_play_file  = self.player_play_file
    self._api.player_stop       = self.player_stop
    self._api.player_pause      = self.player_pause
    self._api.player_resume     = self.player_resume
    self._api.player_toggle     = self.player_toggle
    self._api.player_select_dir = self.player_select_dir
    self._api.player_play_dir   = self.player_play_dir
    self._api._player_get_cover_file = self._player_get_cover_file

  # --- gibt den persistenten Zustand dieser Klasse zurück   -------------------------------

  def get_persistent_state(self):
    """ Persistenten Zustand zurückgeben (überschreibt SRBase.get_pesistent_state()) """
    return {
      'player_dir': self._dir,
      'player_file': self._file
      }

  # --- den persistenten Zustand dieser Klasse wiederherstellen  ------------------------------

  def set_persistent_state(self,state_map):
    """ persistenten Zustand wiederherstellen (überschreibt SRBase.set_pesistent_state()) """

    self.msg("Player: dauerhaften Zustand wiederherstellen")
    if 'player_dir' in state_map:
      self._dir = state_map['player_dir']
      self.msg("Player: aktuelles Verzeichnis (vorläufig):  %s" % self._dir)
    if 'player_file' in state_map:
      self._file = state_map['player_file']
      self.msg("Player: aktuelle Datei (vorläufig): %s" % self._file)
    self._api.update_state(section="player",key="last_dir",
                           value=self._dir[len(self._root_dir):]+os.path.sep,
                           publish=False)
    self._init_thread = threading.Thread(target=self._init_state)
    self._init_thread.start()

  # --- Abfrage von dir-info während der Initialisierung   ----------------------

  def _init_state(self):
    """ Warten auf das Verzeichnis und abfragen Dir-info """

    # Verzeichnis prüfen (ggf. warten)
    self.msg("Player: warten auf %s" % self._dir)
    while not os.path.exists(self._dir) and self._wait_dir:
      time.sleep(1)
      self._wait_dir -= 1

    # Nochmal Überprüfen
    if self._check_dir(self._dir):
      self._get_dirinfo(self._dir,True)

    else:
      # Hoppla, Überprüfung fehlgeschlagen, jetzt alles überprüfen
      if not os.path.exists(self._root_dir):
        self.msg("[WARNING] Player: Verzeichnis %s des Players existiert nicht" %
                 self._root_dir,True)
        self._root_dir = os.path.expanduser("~")
        self.msg("[WARNING] Player: verwendet %s als Rückfall" % self._root_dir,True)
      if not self._check_dir(self._def_dir):
        self._def_dir = self._root_dir
        self.msg("[WARNING] Player: verwendet %s als Rückfall" % self._root_dir,True)
      self._dir = self._def_dir
      self._get_dirinfo(self._dir,True)

    # jetzt auch Dateien prüfen
    if self._file and not self._check_file(self._file):
      self._file = None

    self._init_thread = None
    self.msg("Player: aktuelle dir:  %s" % self._dir)
    self.msg("Player: aktuelle Datei: %s" % self._file)

  # --- Verzeichnis prüfen   ---------------------------------------------------

  def _check_dir(self,path):
    """ Prüfen, ob das Verzeichnis gültig ist """

    path = os.path.abspath(path)
    if not os.path.exists(path):
      self.msg("[WARNING] Player: %s ist nicht vorhanden" % path)
      return False

    if not os.path.commonpath([self._root_dir,path]) == self._root_dir:
      self.msg("[WARNING] Player: %s ist kein untergeordnetes Element des Stammverzeichnisse" % path,
               True)
      return False

    return True

  # --- Datei prüfen   ---------------------------------------------------------

  def _check_file(self,path):
    """ Überprüfen Sie, ob die Datei gültig ist"""

    path = os.path.abspath(path)
    if not os.path.exists(path):
      self.msg("[WARNING] Player: %s ist nicht vorhanden" % path)
      return False
    else:
      return self._check_dir(os.path.dirname(path))

  # --- Druckdauer/-zeit   ----------------------------------------

  def _pp_time(self,seconds):
    """ Druckzeit als mm:ss oder hh:mm """

    m, s = divmod(seconds,60)
    h, m = divmod(m,60)
    if h > 0:
      return "{0:02d}:{1:02d}:{2:02d}".format(h,m,s)
    else:
      return "{0:02d}:{1:02d}".format(m,s)

  # --- start spielen   -------------------------------------------------------

  def player_play_file(self,file=None,last=True):
    """ start spielen """

    if self._init_thread:
      self._init_thread.join()

    if file:
      if not os.path.isabs(file):
        file = os.path.join(self._dir,file)
      if not self._check_file(file):
        raise ValueError("invalid filename %s" % file)
      self._file = file

    if not self._file:
      raise ValueError("default file not set")

    if self._dirinfo:
      self._dirinfo['cur_file'] = self._file

    # Dadurch werden die Informationen an alle Clients übertragen, auch wenn die Datei
    # spielt schon
    # Möglicherweise müssen wir auch die verstrichene Zeit verschieben?!

    total_secs = int(subprocess.check_output(["mp3info", "-p","%S",self._file]))
    file_info = {'name': os.path.basename(self._file),
                 'total': total_secs,
                 'total_pretty': self._pp_time(total_secs),
                 'last': last}
    self._api._push_event({'type': 'file_info', 'value': file_info })
    if self._backend.play(self._file,last):
      self._api.update_state(section="player",key="last_file",
                             value=os.path.basename(self._file),publish=False)
    self._api.update_state(section="player",key="time",
                           value=[0,file_info['total'],file_info['total_pretty']],
                           publish=False)
    return file_info

  # --- Stop spielen   -------------------------------------------------------

  def player_stop(self):
    """ Stop spielen (play->stop, pause->stop)"""

    if self._dirplay:
      self._dirstop.set()         # dadurch wird auch das Backend gestoppt
      self._dirplay.join()
    else:
      self._backend.stop()        # Backend wird eof-event veröffentlichen

  # --- Pausiert spielen   -----------------------------------------------------

  def player_pause(self):
    """ pausiert playing (play->pause) """

    self._backend.pause()

  # --- weiter spielen   ----------------------------------------------------

  def player_resume(self):
    """ weiter spielen (pause->play) """

    self._backend.resume()

  # --- Abspielen umschalten   ------------------------------------------------------

  def player_toggle(self):
    """ Abspielen umschalten (play->pause, pause->play) """

    self._backend.toggle()

  # --- Verzeichnis auswählen, Einträge zurückgeben   ------------------------------------

  def player_select_dir(self,dir=None):
    """ Verzeichnis auswählen:
        ein Verzeichnis, das mit einem / beginnt, wird immer relativ interpretiert
        auf root_dir, ansonsten relativ zum aktuellen Verzeichnis
    """

    if self._init_thread:
      self._init_thread.join()

    self._lock.acquire()

    if not dir:
      # aktuelles Verzeichnis verwenden, aktuelle Datei behalten
      dir = self._dir
    else:
      if os.path.isabs(dir):
        dir = os.path.normpath(self._root_dir+dir)   # cannot use join here!
        self.msg("Player: dir ist absolut, vollständiger Pfad %s" % dir)
      else:
        dir = os.path.normpath(os.path.join(self._dir,dir))
        self.msg("Player: dir ist relativ, vollständiger Pfad %s" % dir)
      if not self._check_dir(dir):
        self._lock.release()
        raise ValueError("invalid directory %s" % dir)

    cache_valid = False
    if dir == self._dir:
      if self._dirinfo:
        cache_valid = True
    else:
      # neues aktuelles Verzeichnis setzen
      self._dir = dir

    # Ereignis zuerst veröffentlichen (Verzeichnis relativ zu root_dir zurückgeben)
    cur_dir = self._dir[len(self._root_dir):]+os.path.sep
    self._api._push_event({'type':  'dir_select', 'value': cur_dir})
    self._api.update_state(section="player",key="last_dir",
                           value=cur_dir,
                           publish=False)

    # dann neue Verzeichnisinfo abfragen
    if not cache_valid:
      self._get_dirinfo(dir)
      self._dirinfo['cur_dir'] = cur_dir
    else:
      self.msg("Player: Verwenden von zwischengespeicherten Verzeichnisinformationen für %s" % dir)

    self._lock.release()
    return self._dirinfo

  # --- Alle Dateien im Verzeichnis abspielen   -----------------------------------------

  def player_play_dir(self,start=None):
    """ alle Dateien im aktuellen Verzeichnis beginnend mit abspielen
        die angegebene Datei
    """

    if self._init_thread:
      self._init_thread.join()

    # Überprüfen Sie den vorhandenen Player-Thread, stoppen Sie ihn und warten Sie, bis er beendet ist
    if self._dirplay:
      self._dirstop.set()
      self._dirplay.join()

    # Dateiliste kopieren
    if not start:
      files = copy.deepcopy(self._dirinfo['files'])
    else:
      try:
        index = self._dirinfo['files'].index(start)
        self.msg("Player: starte play_dir mit Datei %s (index %i)" %
                 (start,index))
        files = copy.deepcopy(self._dirinfo['files'][index:])
      except ValueError:
        raise ValueError("file %s does not exist" % start)

    # Player-Thread starten, Dateien als Argument übergeben
    self._dirstop.clear()
    self._dirplay = threading.Thread(target=self._play_dir,args=(files,))
    self._dirplay.start()

  # --- Alle Dateien abspielen (Helfer)   --------------------------------------------

  def _play_dir(self,files):
    """ alle angegebenen Dateien abspielen """

    ev_queue = self._api._add_consumer("_play_dir")
    do_exit = False

    index_last = len(files)-1
    for index,fname in enumerate(files):
      if do_exit:
        break
      self.msg("Player: _play_dir: nächste Datei abspielen %s" % fname)
      self.player_play_file(fname,last=index==index_last)
      while True:
        """ Implementierung würde nur Warteschlange blockieren, dann könnten wir diesen Thread erst stoppen, nachdem ein Ereignis eintritt """
        if self._dirstop.wait(timeout=1.0):
          do_exit = True
          break
        try:
          ev = ev_queue.get(block=False)
          ev_queue.task_done()
          if ev:
            if ev['type'] == 'eof' and ev['value']['name'] == fname:
              self.msg("Player: Verarbeitung von eof für %s" % fname)
              break                              # Nächste Datei starten
          else:
            do_exit = True
            break
        except queue.Empty:
          pass

    # cleanup
    self.msg("Player: _play_dir stoppen und aufräumen")
    self._api._del_consumer("_play_dir")
    self._backend.stop()
    self._dirplay = None

  # --- Rückgabename der Cover-Datei (currently only cover.jpg)   ---------------

  def _player_get_cover_file(self):
    """ Rückgabename der Cover-Datei """

    cover = os.path.join(self._dir,"cover.jpg")
    if os.path.exists(cover):
      return cover
    else:
      return None

  # --- Erstellen der Verzeichnisinformationen für das angegebene Verzeichnis   --------------------------------

  def _get_dirinfo(self,dir,init=False):
    """ Verzeichnisinformationen erstellen """

    self._dirinfo =  {'dirs':  [], 'files': [], 'dur': []}
    self.msg("Player: Sammeln dir-info für %s" % dir)

    # Der erste Eintrag ist das übergeordnete Verzeichnis
    if self._dir != self._root_dir:
      self._dirinfo['dirs'].append('..')

    for f in os.listdir(dir):
      if os.path.isfile(os.path.join(dir,f)):
        if f.endswith(".mp3"):
          self._dirinfo['files'].append(f)
      else:
        self._dirinfo['dirs'].append(f)

    # ... Ergebnisse sortieren
    self._dirinfo['files'].sort()
    self._dirinfo['dirs'].sort()

    # aktuelle Datei setzen
    if self._file and init:
      self._dirinfo['cur_file'] = os.path.basename(self._file)
    else:
      if len(self._dirinfo['files']):
        self._file = os.path.join(self._dir,self._dirinfo['files'][0])
        self._dirinfo['cur_file'] = self._dirinfo['files'][0]
      else:
        self._dirinfo['cur_file'] = None
      self._api.update_state(section="player",key="last_file",
                             value= self._dirinfo['cur_file'],publish=False)

    # Zeit-Info hinzufügen
    for f in self._dirinfo['files']:
      secs = int(subprocess.check_output(["mp3info",
                                          "-p","%S",
                                          os.path.join(dir,f)]))
      self._dirinfo['dur'].append((secs,self._pp_time(secs)))
