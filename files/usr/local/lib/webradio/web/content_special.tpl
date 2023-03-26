<!--
# ----------------------------------------------------------------------------
# Ausschaltmenü für Web-interface von Radio.
#
# Diese Datei definiert die Inhaltsseite für spezielle Aktionen (z. B. Neustart)
#
# Quelle: (Author: Bernhard Bablok, License: GPL3, Website: https://github.com/bablokb/pi-webradio)
# Bearbeitet : Simone Roßberg
# ----------------------------------------------------------------------------
-->

<div id="tab_special" style="height: 100%; display: none" class="content_area">
  <div class="content_special">
    <a onclick="doStop()"><i class="fab fa-linux" alt="exit to OS"></i></a>
    <a onclick="doRestart()"><i class="fas fa-exchange-alt"></i></a>
    <a onclick="doReboot()"><i class="fas fa-undo"></i></a>
    <a onclick="doHalt()"><i class="fas fa-power-off"></i></a>
  </div>
</div>
