import os, time, datetime, subprocess, threading, copy, queue

from webradio import Base

class Bluetooth(Base):
  """ Player-controller """

  def __init__(self,app):
    """ initialization """

    self._app     = app
    self.debug    = app.debug
    self._api     = app.api
    self._backend = app.backend

    

    #self.read_config()
    self.register_apis()

  # --- read configuration   --------------------------------------------------

  def read_config(self):
    """ read configuration from config-file """

    # section [PLAYER]
    pass

  # --- register APIs   ------------------------------------------------------

  def register_apis(self):
    """ register API-functions """

    self._api.bluetooth_start = self.bluetooth_start
    self._api.bluetooth_stop = self.bluetooth_stop

  # --- start playing   -------------------------------------------------------

  def bluetooth_start(self):
    """ start playing """
    print("Bluetooth start")

    
  # --- stop playing   -------------------------------------------------------

  def bluetooth_stop(self):
    """ stop playing (play->stop, pause->stop)"""
    print("Bluetooth stop")
   
