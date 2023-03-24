#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Pi-Webradio: Implementierung der Klasse RadioEvents
#
# Die Klasse RadioEvents multiplext Ereignisse an mehrere Verbraucher.
#
# Quelle: (Author: Bernhard Bablok, License: GPL3, Website: https://github.com/bablokb/pi-webradio)
# Bearbeitet: Simone Roßberg
#
# -----------------------------------------------------------------------------

import queue, threading, datetime, sys

from webradio import Base
from webradio import EventFormatter

class RadioEvents(Base):
  """ Multiplex-Ereignisse für Verbraucher """

  QUEUE_SIZE          = 20   # Größe der Client-Ereigniswarteschlangen
  KEEP_ALIVE_INTERVAL = 15   # sende Keep-Alive alle x Sekunden

  def __init__(self,app):
    """ Initialisierung """

    self._api         = app.api
    self.debug        = app.debug
    self._stop_event  = app.stop_event
    self._input_queue = queue.Queue()
    self._lock        = threading.Lock()
    self._consumers   = {}
    self._formatter   = EventFormatter()
    self.register_apis()
    threading.Thread(target=self._process_events).start()

  # --- Register APIs   ------------------------------------------------------

  def register_apis(self):
    """ register API-functions """

    self._api._push_event   = self.push_event
    self._api._add_consumer = self.add_consumer
    self._api._del_consumer = self.del_consumer

  # --- Pushen Sie ein Ereignis in die Eingabewarteschlang   -----------------------------------

  def push_event(self,event):
    """ Push-Ereignis in die Eingabewarteschlange """

    self._input_queue.put(event)

  # --- Verbraucher hinzufügen   -----------------------------------------------------

  def add_consumer(self,id):
    """ Hinzufügen eines Verbrauchers zur Liste der Verbraucher """

    if id in self._consumers:
      self.msg("RadioEvents: Wiederverwendung der Verbraucherwarteschlange mit id %s" % id)
      return self._consumers[id]
    else:
      self.msg("RadioEvents: Verbraucher hinzufügen mit id %s" % id)
      with self._lock:
        self._consumers[id] = queue.Queue(RadioEvents.QUEUE_SIZE)
      try:
        ev = {'type': 'version','value': self._api.get_version()}
        ev['text'] = self._formatter.format(ev)
        self._consumers[id].put_nowait(ev)
        ev = {'type': 'state','value': self._api.get_state()}
        ev['text'] = self._formatter.format(ev)
        self._consumers[id].put_nowait(ev)
        return self._consumers[id]
      except:
        with self._lock:
          del self._consumers[id]
        return None

  # --- einen Verbraucher entfernen   --------------------------------------------------

  def del_consumer(self,id):
    """ Löschen eines Verbrauchers aus der Liste der Verbraucher """

    if id in self._consumers:
      self._consumers[id].put(None)
      with self._lock:
        del self._consumers[id]

  # --- Multiplex-Ereignisse   ---------------------------------------------------

  def _process_events(self):
    """ Zieht Ereignisse aus der Eingabewarteschlange und verteilt sie an die Verbraucherwarteschlangen """

    self.msg("RadioEvents: Ereignisverarbeitung starten")
    count = 0
    while not self._stop_event.is_set():
      try:
        event = self._input_queue.get(block=True,timeout=1)   # block 1s
        self._input_queue.task_done()
        self.msg("RadioEvents: erhaltenes Ereignis: %r" % (event,))
        count = 0
      except queue.Empty:
        count = (count+1) % RadioEvents.KEEP_ALIVE_INTERVAL
        if count > 0:
          continue
        else:
          event = {'type': 'keep_alive', 'value':
                   datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

      event['text'] = self._formatter.format(event)
      stale_consumers = []
      for id, consumer in self._consumers.items():
        try:
          consumer.put_nowait(event)
        except queue.Full:
          stale_consumers.append(id)

      # veraltete Verbraucher löschen
      with self._lock:
        for id in stale_consumers:
          self.msg("RadioEvents: Löschen veralteter Warteschlangen mit id %s" % id)
          del self._consumers[id]

    self.msg("RadioEvents: Stoppen der Ereignisverarbeitung")
    for consumer in self._consumers.values():
      try:
        consumer.put_nowait(None)
      except:
        pass
    self.msg("RadioEvents: Ereignisverarbeitung abgeschlossen")
