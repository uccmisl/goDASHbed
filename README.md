# goDashbed Application

current version : 1.0

GoDASHbed is a testbed framework for goDASH


download dash content to <content_folder>, using "get_your_movies.sh"
sudo mv <content_folder> /var/www/html

sudo adduser $USER www-data
sudo chown $USER:www-data -R /var/www
sudo chmod u=rwX,g=srX,o=rX -R /var/www

update the url lists in "urls/mpdURL.py" to reflect the content downloaded
/var/www/html/<folder> -> "http://www.goDASHbed.org/<folder>"

You may also need to update the "configure.json" file in goDASHbed/config, and change url to point to the content downloaded

if using tcp with https - change http to https in the configure.json file
if using quic - change http to https in the configure.json file

to use tcp https in goDASHbed, you need to modify the following file:
goDASHbed/caddy-config/TesbedTCP/Caddyfile

on line 10, chage the following:
tls <godash folder location>/goDash/DashApp/src/goDASH/http/certs/cert.pem <godash folder location>/goDash/DashApp/src/goDASH/http/certs/key.pem

add the folder location that you downloaded goDASH to
Easiest way to find this location, is to open the folder that you added goDASH to, then open a terminal, type "pwd" and the reply is the folder location.  Add this output text into the "Caddyfile" replacing "<godash folder location>"
