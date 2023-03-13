<!--
# ----------------------------------------------------------------------------
# Web-interface für Radio.
#
# Navigations-Menü
#
# Quelle: (Author: Bernhard Bablok, License: GPL3, Website: https://github.com/bablokb/pi-webradio)
# Angepasst: Simone Roßberg 23.02.2023
# ----------------------------------------------------------------------------
-->

<div id="menu">
  <a id="tab_clock_link" class="tablink menu_active" href="#"
         onclick="openTab('tab_clock')"><i class="fas fa-calendar"></i></a>
  <a id="tab_channels_link" class="tablink" href="#"
        onclick="openTab('tab_channels')">
        <i class="fas fa-smile-wink"></i></a>
  <a id="tab_play_link" class="tablink" href="#"
        onclick="openTab('tab_play')"><i class="fas fa-music"></i></a>
  <a id="tab_bluetooth_link" class="tablink" href="#"
        onclick="openTab('tab_bluetooth')"><i class="fab fa-bluetooth"></i></a>
</div>
