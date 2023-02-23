<!--
# ----------------------------------------------------------------------------
# Web-interface Radio
#
# Homepage Uhr
#
# Quelle: https://codepen.io/eehayman/pen/jVPKpN
#
#
# ------------------------------------------------------------------------------>

<div id="tab_clock">
 -for(var j = 0; j < 6; j++)
	 .column
		 -for(var i = 0; i < (j === 0 ? 3 : (10 - !(j % 2) * 4)); i++)
			 .num=i
	 -if(j % 2 === 1 && j < 5)
		 .colon

<script>
function getClock()
</script>
