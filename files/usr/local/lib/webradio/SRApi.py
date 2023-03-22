#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Pi-Webradio: Implementierung der Klasse API
#
# Sammelung alle API-Funktionen
#
# Quelle: (Author: Bernhard Bablok, License: GPL3, Website: https://github.com/bablokb/pi-webradio)
# Bearbeitet: Simone Roßberg
# ----------------------------------------------------------------------------

from webradio import Base

class Api(Base):
  """ Die Klasse enthält Verweise auf alle API-Funktionen """

  def __init__(self,app):
    """ Initialisierung """

    self._app          = app
    self.debug         = app.debug

  # --- API nach Namen ausführen   ------------------------------------------------

  def _exec(self,name,**args):
    """ API nach Namen ausführen """

    if hasattr(self,name):
      self.msg("ausführen: %s(%r)" % (name,dict(**args)))
      return getattr(self,name)(**args)
    else:
      self.msg("unbekannte API-Methode %s" % name)
      raise NotImplementedError("API %s nicht implementiert" % name)

  # --- Liste der APIs zurückgeben   ------------------------------------------------

  def get_api_list(self):
    """ Liste der APIs zurückgeben """

    return [func for func in dir(self)
            if callable(getattr(self, func)) and not func.startswith("_")
            and func not in Base.__dict__ ]
