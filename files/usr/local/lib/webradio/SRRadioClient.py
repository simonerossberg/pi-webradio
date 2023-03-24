#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Pi-Webradio: Implementierung der Klasse RadioClient
#
# Die Klasse RadioClient implementiert einen einfachen Python-Client für die Webradio-API.
#
# Quelle: (Author: Bernhard Bablok, License: GPL3, Website: https://github.com/bablokb/pi-webradio)
# Bearbeitet: Simone Roßberg
#
# ----------------------------------------------------------------------------

import urllib, requests, threading, time, json
import sseclient
import http.client as httplib

from webradio import Base

class RadioClient(Base):
  """ Python-Client für die Webradio-API """

  # --- Konstrukteur  --------------------------------------------------------

  def __init__(self,host,port,debug=False,timeout=10):
    """ Konstrukteur """

    self._host      = host
    self._port      = port
    self.debug      = debug
    self._request   = httplib.HTTPConnection(host,port,timeout)
    self._sseclient = None
    self._stop      = threading.Event()
    self._have_ev   = False
    self._api_list  = None

  # --- Anforderungsobjekt schließen   -----------------------------------------------

  def close(self):
    """ internes Anforderungsobjekt schließen """

    self._request.close()
    self._stop.set()
    if self._sseclient:
      self._sseclient.close()

  # --- Anfrage ausführen   ----------------------------------------------------

  def exec(self,api,params=None,close=False):
    """ API mit den angegebenen Parametern ausführen """

    if params and len(params):
      qstring = urllib.parse.urlencode(params,quote_via=urllib.parse.quote)
      url = '/api/{0}?{1}'.format(api,qstring)
    else:
      url = '/api/'+api

    # Senden, Abrufen und Analysieren der Antwort
    try:
      self._request.request("GET",url)
      response = self._request.getresponse()
      data = (response.status,response.reason,response.read())
    except Exception as ex:
      self.msg("RadioClient: exception: %s" % ex)
      self._request = httplib.HTTPConnection(self._host,self._port)
      data = (-1,"connect error",None)

    if close:
      self.close()

    return data

  # --- Rückgabe-Stopp-Ereignis   --------------------------------------------------

  def get_stop_event(self):
    """ Rückgabe-Stopp-Ereignis """

    return self._stop

  # --- SSE einrichten und Generator zurückgeben  ------------------------------------

  def get_events(self):
    """ Richten Sie den SSE-Client ein und geben Sie die Ereigniswarteschlange zurück """

    url      = 'http://{0}:{1}/api/get_events'.format(self._host,self._port)
    headers  = {'Accept': 'text/event-stream'}

    try:
      response = requests.get(url,stream=True,headers=headers)
      self._sseclient = sseclient.SSEClient(response)
      return self._sseclient.events()
    except Exception as ex:
      self.msg("RadioClient: Ausnahme: %s" % ex)
      return None

  # --- API-Liste abfragen  -----------------------------------------------------

  def get_api_list(self):
    """ API-Liste abfragen """

    if self._api_list:
      return self._api_list
    else:
      _1,_2,apis = self.exec("get_api_list")
      self.msg("RadioClient: API-Liste: %r" % (apis,))
      if apis:
        self._api_list = json.loads(apis)
        return self._api_list
      else:
        return ""

  # --- Ereignisse verarbeiten   -----------------------------------------------------

  def _process_events(self,callback):
    """ Ereignisse verarbeiten """

    try:
      while True and not self._stop.is_set():
        events = self.get_events()
        self.msg("RadioClient: Ereignis: %r" % (events,))
        if not events:
          time.sleep(3)
          continue
        self._have_ev = True
        for event in events:
          if callback:
            callback(event)
          if self._stop.is_set():
            return
    except:
      pass

  # --- Ereignisverarbeitung starten  ---------------------------------------------

  def start_event_processing(self,callback=None):
    """ Ereignisverarbeitung erstellen und starten """

    threading.Thread(target=self._process_events,args=(callback,)).start()
    while not self._have_ev:
      # noch keine Ereignisse vom Server, also warten
      time.sleep(0.1)
    self.msg("RadioClient: Ereignisverarbeitung aktiviert")
    return self._stop
