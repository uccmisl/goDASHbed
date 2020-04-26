# goDashbed Application

Current release version : 1.0

We kindly ask that should you mention goDASH or goDASHbed, or use our code, in your publication, that you would reference the following paper:

D. Raca, M. Manifacier, and J.J. Quinlan.  goDASH - GO accelerated HAS framework for rapid prototyping. 12th International Conference on Quality of Multimedia Experience (QoMEX), Athlone, Ireland. 26th to 28th May, 2020 [CORA](http://hdl.handle.net/10468/9845 "CORA") (To Appear)

## General Description

GoDASHbed is a highly customizable framework for realistic large scale experimentation with two different types of supported traffic:

    -- Video: HTTP Adaptive Streaming traffic with support for two transportation modes TCP and QUIC
    -- VoIP: Realistic VoIP traffic generation (through D-ITG traffic generator[1])


Requirements:
 - [Mininet](http://mininet.org/)
 - [goDASH](https://github.com/uccmisl/goDASH.git)
 - [D-ITG](www.grid.unina.it/software/ITG//download.php)

--------------------------------------------------------

## Install Steps
The easiest way to install goDASHbed is to use the install script available at the UCC Mobile and Internet System Lab [MISL](http://cs1dev.ucc.ie/misl/goDASH/)

After goDASHbed has been installed, follow these steps for all required dependencies

download dash content to `<content_folder>`, using the `get_your_movies.sh` bash script.
Then move the content to your system web folder
```
sudo mv <content_folder> /var/www/html
```
Then change the user permissions on this web folder
```
sudo adduser $USER www-data
sudo chown $USER:www-data -R /var/www
sudo chmod u=rwX,g=srX,o=rX -R /var/www
```
update the url lists in `urls/mpdURL.py` to reflect the content downloaded
```
/var/www/html/<folder> -> "http://www.goDASHbed.org/<folder>"
```
You may also need to update the `configure.json` file in goDASHbed/config, and change url to point to the content downloaded

if using tcp with https - change http to https in the configure.json file
if using QUIC - change http to https in the configure.json file

to use tcp https in goDASHbed, you need to modify the following file:
`goDASHbed/caddy-config/TesbedTCP/Caddyfile`

on line 10, chage the following:
```
tls <godash folder location>/goDash/DashApp/src/goDASH/http/certs/cert.pem <godash folder location>/goDash/DashApp/src/goDASH/http/certs/key.pem
```
add the folder location that you downloaded goDASH to.
Easiest way to find this location, is to open the folder that you added `goDASH` to, then open a terminal, type `pwd` and the reply is the folder location.  Add this output text into the `Caddyfile` replacing `<godash folder location>` as shown above.

--------------------------------------------------------

## Print help about parameters:

```
./goDASHbed -help
```
Flags for goDASH:
```
TODO
```

--------------------------------------------------------

## Examples to launch the app :
>sudo python3 ./goDashBed.py -b 10 --videoclients 3 --duration 40 --voipclients 1 --debug="off" --numruns 1 --tm "tcp"
