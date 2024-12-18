echo ".......................................+=.......................................
......................................+.+,......................................
.....................................+...+......................................
....................................+.....+.....................................
...................................+.......+....................................
..................................+.........=...................................
.................................+:..........+..................................
................................+=............+.................................
...............................=+..............+................................
...............................+................+...............................
..............................+.................~+..............................
.............................+...................++.............................
............................+.....................=~............................
...........................+.......................+,...........................
..........................+......IIIIIIIIIIIIII.....+...........................
.........................+......+.IIII.IIIII.I.......+..........................
........................+.........I?I=.IIIII.I........+.........................
.......................+,........IIIIIIIIIIIIII........+........................
......................+~.........II..=IIII:..I=.........+.......................
.....................=+.........IIIIIIIIIIIIIIII.........+......................
....................,+.......IIIIIIIIIIIIIIIII????I.......+.....................
....................+.......IIIIIIIIIIIIIII?????????......,+....................
...................+.......IIIIIIIIIIIII????????????.......=+...................
..................+........IIIIIIIIII???????????????........=+..................
.................+.........IIIIIIIII????????????????.........+..................
................+..........IIIII??????++????????????..........+.................
...............+...........III???????++++????????+++...........+................
..............+............I?????????+?++++???++++++............+...............
.............+.............??????????+???+++++++++++.............+..............
............+~.............??????????I??++++++++++++..............+.............
...........=+..............????????????++?++++++++++...............+............
..........~+...............????????+++++++++++++++++................+...........
..........+................?????++++++++++++++++++++................,+..........
.........=..................?+++++++++++++++++++++++.................:+.........
........+....................+++++++++++++++++++=++...................++........
.......+.......................++++++++++++++===.......................+~.......
......+.........................++++++++++======........................+.......
.....+.............................=+++++===.............................+......
....+.....................................................................+.....
...+.......................................................................+....
..+~........................................................................=...
.+=..........................................................................+..
+=............................................................................+.
++++++++++++++++++++============================================================"
echo " "
echo "Propane Installation!"
echo " "
echo "WARNING: This setup script only supports Apache2 installs with a webroot location of /var/www/html. Any other configurations will need to manually copy and edit the relevant server and configuration files."
echo "Installing Propane to: /var/www"
echo "<================================================>"
echo "Restoring backup if it exists..."
cp Propane/propane_config.ini.bak Propane/propane_config.ini
echo "Making backup of propane_config.ini"
cp Propane/propane_config.ini Propane/propane_config.ini.bak
echo "Enabling Apache2"
service apache2 start
echo "Setting install dir in propane_config.ini"
sed -i "s|changeme/|/var/www/html/|" Propane/propane_config.ini  
echo "Moving propane files to specified webroot up one dir"
cp -r Propane/* /var/www/.
program_dir="/var/www/propane.py"
chmod +x  $program_dir
echo "Installation Complete..."
echo "Run \"./propane.py\" from" \"$program_dir\" "to start the program."