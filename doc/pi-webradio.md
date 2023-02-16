pi-webradio.py
==============

The python-script `pi-webradio.py` is the main script providing all
the services of the webradio. After installation, you will find it
in `/usr/local/bin`.

Normally, the script is started by the systemd-service `pi-webradio.service`,
see `/etc/systemd/system/pi-webradio.service`. In this mode, the
script starts a webserver (based on Flask) and waits for incoming
requests.

Besides this normal mode of operation, the script supports a number of
other use-cases.


Debugging
---------

To debug problems, stop the regular systemd-service and start
the script in the foreground:

    pi-webradio.py -d

This will log various messages to standard-error.


Listing Channels
----------------

To get a list of all configured channels, run

    > pi-webradio.py -l
    Senderliste
     1: SWR3
     2: SWR3 Lyrix
     3: DASDING
     4: DASDING Rap, sonst nichts
     5: BigFM
     6: SWR1 BW
     7: SWR1 RP
     8: SWR1 Musik Klub Deutsch
     9: SWR2
    10: SWR Aktuell
    11: SWR4 BW
    12: SWR4 SWR Schlager
    13: antenne 1
    14: antenne 1 Schlager
    15: antenne 1 Deutsch-Pop
    16: antenne 1 Party-Kracher
    17: antenne 1 Weihnachts-Hits
    18: Die Sendung mit der Maus
    19: Neckaralb Live
    20: BarbaRadio
    21: Bayern 1
    22: Bayern 2
    23: Bayern 3
    24: BR Klassik
    25: BR Schlager
    26: BR 24
    27: BR 24 live

Listing channels is a way to check your channel-file is correct.


Direct Play
-----------

To test an url (e.g. from channel 5), you can run the command

    pi-webradio.py -p 5

Hit CTRL-C to quit. This mode does not start the
webserver and you don't have any additional controls, so it is mainly
useful for testing purposes (correct channel-configuration, correct url).


Recording
---------

The web-gui allows for spontaneous recordings using the record-button
(rightmost button in the first row beneath the logo).

Recordings can also be started from the commandline. The command

    pi-webradio.py -r 4 120

records channel 4 for 120 minutes. You can override the default
target-directory configured in `/etc/pi-webradio.conf` with the
option `-t dir`.

For planned recordings, you should install the package *at* and use
the following command:

    echo "/usr/local/bin/pi-webradio.py -r 4 120" | at 20:00 31.10.21

The at-command accepts various date/time formats, see the manpage
for details. You can plan regular recordings from the crontab or
by defining a systemd-timer.

