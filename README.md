# goDashbed Application

Current release version : 2.0.6 - updated for goDASHbed to golang 1.20+

We kindly ask that should you mention [goDASH](https://github.com/uccmisl/godash) or [goDASHbed](https://github.com/uccmisl/godashbed), or use our code, in your publication, that you would reference the following papers:

D. Raca, M. Manifacier, and J.J. Quinlan.  goDASH - GO accelerated HAS framework for rapid prototyping. 12th International Conference on Quality of Multimedia Experience (QoMEX), Athlone, Ireland. 26th to 28th May, 2020 [CORA](http://hdl.handle.net/10468/9845 "CORA")

John O’Sullivan, D. Raca, and Jason J. Quinlan.  Demo Paper: godash 2.0 - The Next Evolution of HAS Evaluation. 21st IEEE International Symposium On A World Of Wireless, Mobile And Multimedia Networks (IEEE WoWMoM 2020), Cork, Ireland. August 31 to September 03, 2020 [CORA](https://cora.ucc.ie/handle/10468/10145 "CORA")

--------------------------------------------------------
## Docker Containers

With the release of version 2.0.5, we are also releasing amd64 docker containers for both [goDASH](https://hub.docker.com/r/jjq52021/godash) or [goDASHbed](https://hub.docker.com/r/jjq52021/godashbed).

An arm64 version of [goDASH](https://hub.docker.com/r/jjq52021/godash_arm64) is also available.

In the coming weeks/months/years we will also release a network build script, so as to permit a full evaluation of DASH algorithms and associated TCP and QUIC transport protocols within a Docker test framework.

--------------------------------------------------------
## General Description

GoDASHbed is a highly customizable framework for realistic large scale experimentation with two different types of supported traffic:

    -- Video: HTTP Adaptive Streaming traffic with support for two transportation modes TCP and QUIC
    -- VoIP: Realistic VoIP traffic generation (through D-ITG traffic generator[1])

In collaboration with [godash](https://github.com/uccmisl/godash.git), goDASHbed provides a framework for HAS video analysis.

Requirements:
 - [Mininet](http://mininet.org/) Does not work on M1 or M2 apple machine natively :(
 - [godash](https://github.com/uccmisl/godash.git) Version 2.0 or later
 - [D-ITG](https://traffic.comics.unina.it/software/ITG/download.php)

 To use the hypercorn webserver, you need to install trio, quart, quart_trio and hypercorn, type ```python3.10 -m pip install trio``` in terminal, replacing ```python3.10``` with the version of python3 you are using, and ```trio``` with the git repo you want to install.

### Legacy
Version 2.0 of `goDASHbed` is a major write of the code, and versions of `goDASHbed` from version 2.0 onwards will only work with versions of `godash` from  version 2.0 onwards.  If you are using a  version 1 release of `godash`, please use a version 1 release of `goDASHbed`.

--------------------------------------------------------
## Install Steps
The easiest way to install goDASHbed is to use the install script available at the UCC Mobile and Internet System Lab [MISL](http://cs1dev.ucc.ie/misl/godash2.0)

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
update the url lists in `urls/mpdURL.py` and in `urls/mpdURLquic.py` to reflect the content downloaded
```
/var/www/html/<folder> -> "http://www.godashbed.org/<folder>"
```
You may also need to update the `configure.json` file in goDASHbed/config, and change url to point to the content downloaded

The clients will randomly choose one URL from the `urls/mpdURL.py` or `urls/mpdURLquic.py` file (depending on TCP/QUIC).

if using tcp with https - change http to https in the configure.json file

If you did not use the install script:
to use HTTPS in goDASHbed, you need to modify the following files:
`goDASHbed/caddy-config/TesbedTCP/CaddyFilev2TCP`
`goDASHbed/caddy-config/TesbedTCP/CaddyFilev2QUIC`

change the following line:
```
tls <godash folder location>/godash/http/certs/cert.pem <godash folder location>/godash/http/certs/key.pem
```
add the folder location that you downloaded goDASH to.
Easiest way to find this location, is to open the folder that you added `godash` to, then open a terminal, type `pwd` and the reply is the folder location.  Add this output text into the `CaddyfileCaddyFilev2TCP` and `CaddyFilev2QUIC` replacing `<godash folder location>` as shown above.

--------------------------------------------------------
## Print help about parameters:

```
./goDASHbed --help
```
Flags for goDASHbed:
```
  -h, --help            Show this help message and exit
  --bw-net, -b          Bandwidth of bottleneck link - required parameter
  --delay               Delay in milliseconds of bottleneck link (default 40ms)
  --numruns             Number of times experiment will be repeated (default 1)
                        Based on number of trace files in the 'traces' folder
  --voipclients         Number of voip clients (default 0)
  --videoclients        Number of video clients (default 0)
  --tm                  Transport mode (TCP - HTTP/HTTPS or QUIC - HTTPS)
  --duration            Duration of experiment (in seconds.) (default 0s)
  --bwKPI               Name of the column indicating throughput (default="DL_bitrate")
  --debug               Print output of goDASH to the log file (default 'on')
  --terminalPrint       Print output of goDASH to the terminal screen (default 'on')
  --server              Choice of Web server - WSGI (Caddy - TCP/QUIC) or ASGI (Hypercorn - TCP/QUIC)
  --collaborative       Run the evaluation in collaborative mode, and share content between the clients (based only on client requests)
  --cli                 Turns on mininet command line interface and stops web-servers from running - permitting the user to run the server and clients via terminal windows directly in mininet (default 'off')
```
--------------------------------------------------------

## Examples to launch the app :
run godashbed on a 10Mbit link with 3 video clients for 40 seconds, with 1 VOIP client, with no debug or terminal print outs, once for each trace in the 'traces' folder, using TCP as the transport mode and the ASGI Hypercorn/QuartTrio Server, without collaborative streaming
```
sudo python3 ./goDashBed.py -b 10 --videoclients 3 --duration 40 --voipclients 1 --debug "off" --numruns 1 --tm "tcp" --terminalPrint "off" --server "ASGI" --collaborative "off" --cli "off"
```

run godashbed on a 10Mbit link with 3 video clients for 40 seconds, with 1 VOIP client, with debug or terminal print outs, once for each trace in the 'traces' folder, using QUIC as the transport mode and the WSGI Caddy Server, with collaborative streaming
```
sudo python3 ./goDashBed.py -b 10 --videoclients 3 --duration 40 --voipclients 1 --debug "on" --numruns 1 --tm "quic" --terminalPrint "on" --server "WSGI"  --collaborative "on" --cli "off"
```
