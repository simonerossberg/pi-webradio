#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Hauptanwendungsprogramm für das Pi-webradio
#
# Dieses Programm startet die Anwendung entweder im synchronen Modus oder in
# Servermodus. Letzteres wird normalerweise von einem systemd-Dienst ausgeführt.
# Der synchrone Modus dient zum Auflisten von Kanälen, direkter Aufnahme und direkt
# spielen. Beachten Sie, dass direktes Spielen keine Interaktion zulässt, also
# Diese Funktion ist hauptsächlich für die Entwicklung und das Debugging nützlich.
#
#
# ----------------------------------------------------------------------------

import locale, os, sys, signal, queue, threading
from   argparse import ArgumentParser

# --- Anwendungsimporte   --------------------------------------------------

sys.path.append(os.path.join(
  os.path.dirname(sys.argv[0]),"../lib"))

from webradio import *

# --- Hilfsklasse für Optionen   --------------------------------------------

class Options(object):
  pass

# --- Komandozeile-Parser   ------------------------------------------------------

def get_parser():
  """ konfigurieren Komandozeile-Parser """

  parser = ArgumentParser(add_help=False,description='Pi-Webradio')

  parser.add_argument('-p', '--play', action='store_true',
    dest='do_play', default=False,
    help="play radio/file (direct, no web-interface, needs channel/file as argument)")

  parser.add_argument('-l', '--list', action='store_true',
    dest='do_list', default=False,
    help="display radio-channels")

  parser.add_argument('-r', '--record', action='store_true',
    dest='do_record', default=False,
    help="record radio (direct, no webinterface, needs channel as argument)")
  parser.add_argument('-t', '--tdir', nargs=1,
    metavar='target directory', default=None,
    dest='target_dir',
    help='target directory for recordings')

  parser.add_argument('-d', '--debug', action='store_true',
    dest='debug', default=False,
    help="force debug-mode (overrides config-file)")
  parser.add_argument('-q', '--quiet', action='store_true',
    dest='quiet', default=False,
    help="don't print messages")
  parser.add_argument('-h', '--help', action='help',
    help='print this help')

  parser.add_argument('channel', nargs='?', metavar='channel',
    default=0, help='channel number/filename')
  parser.add_argument('duration', nargs='?', metavar='duration',
    default=0, help='duration of recording')
  return parser

# --- Optionen validieren und korrigieren   ---------------------------------------------

def check_options(options):
  """ Optionen validieren und korrigieren """

  # record benötigt eine Kanalnummer
  if options.do_record and not options.channel:
    print("[ERROR] record-option (-r) needs channel nummber as argument")
    sys.exit(3)

# --- Ereignisse verarbeiten   -------------------------------------------------------

def process_events(app,options,queue):
  while True:
    ev = queue.get()
    if ev:
      if not options.quiet and not ev['type'] == 'keep_alive':
        print(ev['text'])
      queue.task_done()
      if ev['type'] == 'eof' and options.do_play:
        break
      if ev['type'] == 'sys':
        break
    else:
      break
  app.msg("pi-webradio: abgeschlossene Verarbeitungsereignisse")
  try:
    os.kill(os.getpid(), signal.SIGTERM)
  except:
    pass

# --- Hauptprogramm   ----------------------------------------------------------

if __name__ == '__main__':

  # Lokal von der Umgebung auf Standard setzen
  locale.setlocale(locale.LC_ALL, '')

  # Befehlszeilenargumente parsen
  opt_parser     = get_parser()
  options        = opt_parser.parse_args(namespace=Options)
  options.pgm_dir = os.path.dirname(os.path.abspath(__file__))
  check_options(options)

  app = WebRadio(options)

  # Signal-Handler einrichten
  signal.signal(signal.SIGTERM, app.signal_handler)
  signal.signal(signal.SIGINT,  app.signal_handler)

  if options.do_list:
    if not options.quiet:
      app.msg("Senderliste: %s " % app.api.get_version(),force=True)
    channels = app.api.radio_get_channels()
    PRINT_CHANNEL_FMT="{0:2d}: {1}"
    for channel in channels:
      print(PRINT_CHANNEL_FMT.format(channel['nr'],channel['name']))
  else:
    ev_queue = app.api._add_consumer("main")
    threading.Thread(target=process_events,args=(app,options,ev_queue)).start()
    if options.do_record:
      app.api.rec_start(nr=int(options.channel),sync=True)
      app.cleanup()
    elif options.do_play:
      try:
        nr = int(options.channel)
        app.api.radio_play_channel(nr)
      except ValueError:
        app.api.player_play_file(options.channel) # davon ausgehen, dass das Argument ein Dateiname ist
      signal.pause()
    else:
      app.run()
      signal.pause()
    app.api._del_consumer("main")
  sys.exit(0)
