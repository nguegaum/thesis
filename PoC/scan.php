<?php
 
          $old_path = getcwd();
	
         chdir('/root/BashScripts/');
	 shell_exec('sudo -S ./AutomaticNmapScan.sh');
         chdir($old_path);

?>

