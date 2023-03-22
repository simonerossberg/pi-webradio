import threading, subprocess, signal, os, shlex, re, traceback 
import bluetooth, pyatv

from webradio import Base

class Bluetooth(Base):
   """ Bluetooth-Steuerobjekt """

  def __init__(self,app):
    """ Initialisierung """

    self._app       = app
    self._api       = app.api
    self.debug      = app.debug
   

    self.read_config()
    self.register_apis()

  # --- Konfiguration lesen  --------------------------------------------------

  def read_config(self):
    """ Konfiguration aus config-fil lesene """

    # # section [MPG123]
    # self._vol_default = int(self.get_value(self._app.parser,"MPG123",
    #                                    "vol_default",30))
    # self._volume      = self._vol_default
    # self._vol_delta   = int(self.get_value(self._app.parser,"MPG123",
    #                                    "vol_delta",5))
    # self._mpg123_opts = self.get_value(self._app.parser,"MPG123",
    #                                    "mpg123_opts","")
    pass

  # --- Register APIs   ------------------------------------------------------

  def register_apis(self):
    """ Register API-Funktionen """

    self._api.bluetooth_start = self.bluetooth_start
    self._api.bluetooth_stop  = self.bluetooth_stop

    self.msg("Bluetooth APIs eingetragen")

  # --- gibt den persistenten Zustand dieser Klasse zurück   -------------------------------

  def get_persistent_state(self):
    # """ persistenten Zustand zurückgeben (overrides SRBase.get_pesistent_state()) """
    # return {
    #   'volume': self._volume if not self._mute else self._vol_old
    #   }
    pass

  # --- den persistenten Zustand dieser Klasse wiederherstellen   ------------------------------

  def set_persistent_state(self,state_map):
    # """ persistenten Zustand wiederherstellen (overrides SRBase.set_pesistent_state()) """

    # self.msg("Mpg123: restoring persistent state")
    # if 'volume' in state_map:
    #   self._volume = state_map['volume']
    # else:
    #   self._volume = self._vol_default
    # self.msg("Mpg123: volume is: %d" % self._volume)
    pass

  
  # --- Bluetooth Starten   ----------------------------------------------------

  def bluetooth_start(self):
    """ Start Bluetooth & Airplay """
    self.msg("Starte Bluetooth & Airplay...")
    
    # Suchen Sie im Netzwerk nach AirPlay-Geräten
    devices = pyatv.scan(timeout=5)

    # Verbindung mit dem ersten gefundenen Gerät
    device = devices[0]
    airplay = device.airplay
    
    target_name = "Raspberry Pi" # Name Bluetoothlautsprecher
    target_address = None

    nearby_devices = bluetooth.discover_devices()
    for addr in nearby_devices:
       if target_name == bluetooth.lookup_name(addr):
         target_address = addr
         break

    if target_address is not None:
      print("Zielgerät mit Adresse gefunden:", target_address)
    else:
      print("Zielgerät konnte nicht gefunden werden")

    #Verbindug mit Zielgerät
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((target_address, 1)) #Kanalnummer des Geräts
   

  # --- Stop Bluetooth & Airplay   ----------------------------------------------------

  def bluetooth_stop(self):
    """ Stop Bluetooth & Airplay """
    self.msg("Stop Bluetooth & Airplay...")
    airplay.stop()
    
    # Senden „Stopp“-Befehl an das Bluetooth-Gerät
    sock.send("STOP")
    # Schließen der Bluetooth-Verbindung
    sock.close()
   
