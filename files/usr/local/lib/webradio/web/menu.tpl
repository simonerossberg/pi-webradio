<!--
# ----------------------------------------------------------------------------
# Web-interface for pi-webradio.
#
# This file defines the navigation-menu
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/pi-webradio
#
# ----------------------------------------------------------------------------
-->

<div id="menu">
  <a id="tab_clock_link" class="tablink menu_active" href="#"
         onclick="openTab('tab_clock')"><i class="fad fa-alarm-clock"></i></a>
  <a id="tab_channels_link" class="tablink" href="#"
        onclick="openTab('tab_channels')">
        <i class="fad fa-radio"></i></a>
  <a id="tab_play_link" class="tablink" href="#"
        onclick="openTab('tab_play')"><i class="fad fa-music"></i></a>
  <a id="tab_files_link" class="tablink" href="#"
        onclick="openTab('tab_files')"><i class="fas fa-bluetooth"></i></a>
  <a id="tab_special_link" class="tablink" href="#"
        onclick="openTab('tab_special')"><i class="fad fa-wrench"></i></a>
</div>
