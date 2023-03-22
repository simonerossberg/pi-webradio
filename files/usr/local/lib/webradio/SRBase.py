#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Pi-Webradio: Implementierung der Klasse Base
#
# Die Klasse Base ist die Mutterklasse aller Klassen und implementiert gemeinsame Methoden
#
# Quelle: (Author: Bernhard Bablok, License: GPL3, Website: https://github.com/bablokb/pi-webradio)
# Bearbeitet: Simone Roßberg
# -----------------------------------------------------------------------------

import sys, time

class Base:
  """ Base-Klasse mit gängigen Methoden """

  # --- Debug-Meldungen ausgeben   ------------------------------------------------

  def msg(self,text,force=False):
    """ Debug-Meldungen ausgeben """

    if force:
      sys.stderr.write("%s\n" % text)
    elif self.debug:
      sys.stderr.write("[DEBUG %s] %s\n" % (time.strftime("%H:%M:%S"),text))
    sys.stderr.flush()

  # --- Konfigurationswert lesen   --------------------------------------------

  def get_value(self,parser,section,option,default):
    """ Wert der Konfigurationsvariablen abrufen und gegebenen Standardwert zurückgeben, falls nicht gesetzt """

    if parser.has_section(section):
      try:
        value = parser.get(section,option)
      except:
        value = default
    else:
      value = default
    return value

  # --- return persistent state of this class   -------------------------------

  def get_persistent_state(self):
    """ Persistenten Zustand zurückgeben (implementiert durch Unterklassen) """
    return {}

  # --- set state state of this class   ---------------------------------------

  def set_persistent_state(self,state_map):
    """ set state (implementiert durch Unterklassen) """
    pass
