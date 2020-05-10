# goDashbed Application

Current release version : 1.1.5

We kindly ask that should you mention godash or goDASHbed, or use our code, in your publication, that you would reference the following paper:

D. Raca, M. Manifacier, and J.J. Quinlan.  goDASH - GO accelerated HAS framework for rapid prototyping. 12th International Conference on Quality of Multimedia Experience (QoMEX), Athlone, Ireland. 26th to 28th May, 2020 [CORA](http://hdl.handle.net/10468/9845 "CORA") (To Appear)

## General Description

GoDASHbed is a highly customizable framework for realistic large scale experimentation with two different types of supported traffic:

    -- Video: HTTP Adaptive Streaming traffic with support for two transportation modes TCP and QUIC
    -- VoIP: Realistic VoIP traffic generation (through D-ITG traffic generator[1])


Requirements:
 - [Mininet](http://mininet.org/)
 - [godash](https://github.com/uccmisl/godash.git)
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
/var/www/html/<folder> -> "http://www.godashbed.org/<folder>"
```
You may also need to update the `configure.json` file in goDASHbed/config, and change url to point to the content downloaded

The clients will randomly choose one URL from the `urls/mpdURL.py` file.

if using tcp with https - change http to https in the configure.json file
if using QUIC - change http to https in the configure.json file

to use tcp https in goDASHbed, you need to modify the following file:
`goDASHbed/caddy-config/TesbedTCP/Caddyfile`

on line 10, chage the following:
```
tls <godash folder location>/godash/http/certs/cert.pem <godash folder location>/godash/http/certs/key.pem
```
add the folder location that you downloaded goDASH to.
Easiest way to find this location, is to open the folder that you added `godash` to, then open a terminal, type `pwd` and the reply is the folder location.  Add this output text into the `Caddyfile` replacing `<godash folder location>` as shown above.

--------------------------------------------------------

## Print help about parameters:

```
./goDASHbed --help
```
Flags for goDASH:
```
  -h, --help            Show this help message and exit
  --bw-net, -b          Bandwidth of bottleneck link - required parameter
  --delay               Delay in milliseconds of bottleneck link (default 40ms)
  --numruns             Number of times experiment will be repeated (default 1)
                        Based on number of trace files in the 'traces' folder
  --voipclients         Number of voip clients (default 0)
  --videoclients        Number of video clients (default 0)
  --tm                  Transport mode (TCP - HTTP/HTTP2 or QUIC - HTTPS)
  --duration            Duration of experiment (in seconds.) (default 0s)
  --bwKPI               Name of the column indicating throughput (default="DL_bitrate")
  --debug               Print output of goDASH to the log file (default 'on')
  --terminalPrint       Print output of goDASH to the terminal screen (default 'on')
  --server              Choice of Web server - WSGI (Caddy and QUIC) or ASGI (Hypercorn - currently only TCP)
```
--------------------------------------------------------

## Examples to launch the app :
run godashbed on a 10Mbit link with 3 video clients for 40 seconds, with 1 VOIP client, with no debug or terminal print outs, once for each trace in the 'traces' folder, using TCP as the transport mode and the ASGI Hypercorn/Quart Server
```
sudo python3 ./goDashBed.py -b 10 --videoclients 3 --duration 40 --voipclients 1 --debug "off" --numruns 1 --tm "tcp" --terminalPrint "off" --server "ASGI"
```

run godashbed on a 10Mbit link with 3 video clients for 40 seconds, with 1 VOIP client, with debug or terminal print outs, once for each trace in the 'traces' folder, using QUIC as the transport mode and the WSGI Caddy/Example Server(s)
```
sudo python3 ./goDashBed.py -b 10 --videoclients 3 --duration 40 --voipclients 1 --debug "on" --numruns 1 --tm "quic" --terminalPrint "on" --server "WSGI"
```
