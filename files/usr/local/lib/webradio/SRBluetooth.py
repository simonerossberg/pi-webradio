import threading, subprocess, signal, os, shlex, re, traceback
# from threading import Thread
# import queue, collections, time

from webradio import Base

class Bluetooth(Base):
  # """ bluetooth control-object """

  def __init__(self,app):
    """ initialization """

    self._app       = app
    self._api       = app.api
    self.debug      = app.debug
   

    self.read_config()
    self.register_apis()

  # --- read configuration   --------------------------------------------------

  def read_config(self):
    """ read configuration from config-file """

    # # section [MPG123]
    # self._vol_default = int(self.get_value(self._app.parser,"MPG123",
    #                                    "vol_default",30))
    # self._volume      = self._vol_default
    # self._vol_delta   = int(self.get_value(self._app.parser,"MPG123",
    #                                    "vol_delta",5))
    # self._mpg123_opts = self.get_value(self._app.parser,"MPG123",
    #                                    "mpg123_opts","")
    pass

  # --- register APIs   ------------------------------------------------------

  def register_apis(self):
    """ register API-functions """

    self._api.bluetooth_start = self.bluetooth_start
    self._api.bluetooth_stop  = self.bluetooth_stop

    self.msg("Bluetooth APIs registered")

  # --- return persistent state of this class   -------------------------------

  def get_persistent_state(self):
    # """ return persistent state (overrides SRBase.get_pesistent_state()) """
    # return {
    #   'volume': self._volume if not self._mute else self._vol_old
    #   }
    pass

  # --- restore persistent state of this class   ------------------------------

  def set_persistent_state(self,state_map):
    # """ restore persistent state (overrides SRBase.set_pesistent_state()) """

    # self.msg("Mpg123: restoring persistent state")
    # if 'volume' in state_map:
    #   self._volume = state_map['volume']
    # else:
    #   self._volume = self._vol_default
    # self.msg("Mpg123: volume is: %d" % self._volume)
    pass

  
  # --- start bluetooth   ----------------------------------------------------

  def bluetooth_start(self):
    """ start bluetooth """
    self.msg("Starting Bluetooth ...")
    # TODO: add code
    pass

  # --- stop bluetooth   ----------------------------------------------------

  def bluetooth_stop(self):
    """ stop bluetooth """
    self.msg("Stopping Bluetooth ...")
    # TODO: add code
    pass
