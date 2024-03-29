#!/usr/bin/python3


'''
goDASHBed

Highly customizable framework for realistic large scale experimentation with two different types of traffic


          - Supported traffic types:
            -- Video: HTTP Adaptive Streaming traffic with support for two transportation modes TCP and QUIC
            -- VoIP: Realistic VoIP traffic generation (through D-ITG traffic generator[1])


Requirements:
 - Mininet (http://mininet.org/)
 - goDash (https://github.com/uccmisl/godash.git)
 - D-ITG (https://traffic.comics.unina.it/software/ITG/download.php)


References:

1. Alessio Botta, Alberto Dainotti, and Antonio Pescap;. 2012. A tool for the generation of realistic network workload for emerging networking scenarios. Comput. Netw. (October 2012)

example call to goDashBed.py
sudo python3 ./goDashBed.py -b 10 --videoclients 3 --duration 40 --voipclients 1 --debug "on" --numruns 1 --tm "quic" --terminalPrint "on" --server "WSGI"  --collaborative "on" --cli "off"

sudo python3 ./goDashBed.py -b 10 --videoclients 3 --duration 40 --voipclients 1 --debug "off" --numruns 1 --tm "tcp" --terminalPrint "off" --server "ASGI" --collaborative "off" --cli "off"

--cli "on" - turns on mininet command line interface and stops webservers from running - permitting the user to run the server and clients via terminal windows in mininet.
'''


from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink, Intf
from mininet.node import Controller, OVSKernelSwitch
from mininet.net import Mininet
from mininet.log import setLogLevel, info, error, lg
from mininet.util import dumpNodeConnections
from mininet.cli import CLI
from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser
import subprocess
import sys
import os
import random
from time import sleep, time
from subprocess import *
import re
import pandas as pd
from os import listdir
from os.path import isfile, join
import datetime
from urls.mpdURL import *
from urls.mpdURLquic import *
from random import randint
import io
import json
import threading
from threading import Thread
# Parse arguments

parser = ArgumentParser(description="goDASHBed - Better than sliced bread")


parser.add_argument('--bw-net', '-b',
                    dest="bw_net",
                    type=float,
                    action="store",
                    help="Bandwidth of bottleneck link",
                    required=True)

parser.add_argument('--delay',
                    dest="delay",
                    type=float,
                    help="Delay in milliseconds of bottleneck link",
                    default=10)

parser.add_argument('--numruns',
                    dest="numruns",
                    help="Number of times experiment will be repeated, based on number of trace files in the 'traces' folder",
                    default=1)

parser.add_argument('--voipclients',
                    dest="voipclients",
                    help="number of voip clients",
                    default=0)

parser.add_argument('--videoclients',
                    dest="videoclients",
                    help="number of video clients",
                    default=0)

parser.add_argument('--tm',
                    dest="transport_mode",
                    default="tcp",
                    help="Transport mode (TCP - HTTP/HTTP2 or QUIC - HTTPS)")

parser.add_argument('--duration',
                    dest="duration",
                    help="Duration of experiment (in seconds.)",
                    default=0)

parser.add_argument('--bwKPI',
                    dest="bwKPI",
                    default="DL_bitrate",
                    help="Name of the column indicating throughput")

parser.add_argument('--debug',
                    dest="debug",
                    help="print output of goDASH to the log file",
                    default="on")

parser.add_argument('--terminalPrint',
                    dest="terminalPrint",
                    help="print output of goDASH to the terminal screen",
                    default="on")

parser.add_argument('--server',
                    dest="serverType",
                    help="Choice of Web server - WSGI (Caddy and QUIC) or ASGI (Hypercorn)",
                    default="WSGI")

parser.add_argument('--collaborative',
                    dest="collaborative",
                    help="run network in collaborative mode",
                    default="off")

parser.add_argument('--cli',
                    dest="cliBoolean",
                    help="stop mininet and enter cli (command line interface)",
                    default="off")

# Expt parameters
args = parser.parse_args()

# ouptut folder structure
# output
output_folder_name = "/output"
# - config
config_folder_name = "/config"
# - files
log_folder_name = "/files"

# get all the possible DASH MPD files from the H264 UHD dataset
# set the port number of the server based on the transport portocol
if args.transport_mode == "quic":
    urls = full_url_list_quic+main_url_list_quic+live_url_list_quic + \
        full_byte_range_url_list_quic+main_byte_range_url_list_quic
else:
    urls = full_url_list+main_url_list+live_url_list + \
    full_byte_range_url_list+main_byte_range_url_list

# get all the possible DASH MPD files from the H264 UHD dataset


def clean_up(voip_host):
    # clean up the main godashbed folder if the script stops abruptly
    voip_host.popen("rm voipclients")


def create_dict_from_json(config_file):
    # create a dictionary from the default config file
    with open(config_file) as json_file:
        test_dict = json.load(json_file)
    return test_dict


def create_dict(config_file):
    # lets read in the original config file and create a dictionary we can use
    dict = {}
    # open the original config file
    with io.open(config_file, encoding='utf-8-sig') as fp:
        # read line by line
        line = fp.readline().strip()
        while line:
            # do not split around the brackets
            if line != "{" and line != "}":
                # split around the colon, but not the colon in http :)
                key, val = line.split(' : ')
                key = key.strip()
                val = val.strip()
                dict[key] = val
                line = fp.readline().strip()
            else:
                # otherwise, just read the line
                line = fp.readline().strip()

    # return the dictionary
    return dict


def modify_dict(_dict, i, run, **params):
    for k, v in _dict.items():
        # changed for godashbed v2
        # if k == "storeDash":
        if k == "outputFolder":
            _dict[k] = params["client_name"]
        elif k == "logFile":
            _dict[k] = str(str(v)[:8]+"_client"+str(i))
        elif k == "terminalPrint":
            _dict[k] = args.terminalPrint
        elif k == "debug":
            _dict[k] = args.debug
        elif k == "serveraddr":
            _dict[k] = args.collaborative
        elif k == "storeDash":
            if args.collaborative == "on":
                _dict[k] = args.collaborative
            else:
                _dict[k] = str(v)
        elif k == "streamDuration":
            _dict[k] = int(args.duration)
        elif k == "quic":
            if args.transport_mode == "quic":
                _dict[k] = "on"
            else:
                _dict[k] = "off"
        elif k == "url":
            value = randint(0, len(urls)-1)
            _dict[k] = urls[value]
        elif k == "getHeaders":
            if v != "off":
                getHeaders = True
    fout = params["config_folder"]+params["client_config"]
    # print(params["config_folder"])
    with open(fout, 'w') as json_file:
        json.dump(_dict, json_file)


def readCsvThr(file_path):
    pdf = pd.read_csv(file_path, usecols=[args.bwKPI])
    time_interval = 1000
    time_bw_array = []
    for index, row in pdf.iterrows():
        time_bw_array.append([time_interval, row[args.bwKPI]])
    m_time_bw_array = modify_zero_thr2(time_bw_array)

    return m_time_bw_array


def modify_zero_thr2(bw_array):
    zero_array = []
    for i in range(len(bw_array)):
        if bw_array[i][1] <= 1:
            zero_array.append(bw_array[i][1])
        else:
            len_z_a = len(zero_array)
            diff = 0
            if len_z_a > 0:
                one_packet_zero_range_kbit = ((1500*8)/1000.0)/len_z_a
                if one_packet_zero_range_kbit < 1:
                    diff = 1 - one_packet_zero_range_kbit
                    one_packet_zero_range_kbit = 1
                for j in range(1, len_z_a+1):
                    bw_array[i-j][1] = one_packet_zero_range_kbit
                sum_val = (len_z_a*one_packet_zero_range_kbit
                           - sum(zero_array)) + diff*len_z_a
                #print sum_val
                zero_array = []
                bw_array[i][1] = bw_array[i][1] - sum_val
                if bw_array[i][1] <= 1:
                    zero_array.append(bw_array[i][1])
    return bw_array

# Class to start the throttle link thread


class ThrottleLink:

    def __init__(self):
        self._running = True
        self._stop_me = False

    def terminate(self):
        self._running = False
        self._stop_me = True

    def run(self, bw_a):
        print("Throttling the link")
        num_of_sec = 0
        sec_step = 0

        for i in range(len(bw_a)):
            print("BW: " + str(bw_a[i][1]))
            os.system("tc class change dev s1-eth1 parent 1:0 classid 1:1 htb rate %fkbit ceil %fkbit" %
                      (bw_a[i][1], bw_a[i][1]))

            # if stop is True, then return
            if self._stop_me:
                return
            # otherwise keep printing the bandwidth
            else:
                sleep(bw_a[i][0]/1000)


def video_clients_completed(processes, tl):
    # for all the clients, work out when they finish
    for p in processes:
        # lets stop when the processes complete
        if p.cmd('wait', p.lastPid) != 0:
            print("Client at " + str(p) + " has completed streaming")
            continue
    return


def monitor_devs(dev_pattern='^s', fname="%s/bytes_sent.txt" %
                 ".", interval_sec=0.01):
    """Aggregates (sums) all txed bytes and rate (in Mbps) from
       devices whose name matches @dev_pattern and writes to @fname"""
    pat = re.compile(dev_pattern)
    spaces = re.compile('\s+')
    open(fname, 'w').write('')
    prev_tx = {}
    print("bytes: " + fname)
    while 1:
        lines = open('/proc/net/dev').read().split('\n')
        t = str(time())
        total = 0
        for line in lines:
            line = spaces.split(line.strip())
            iface = line[0]
            if pat.match(iface) and len(line) > 9:
                tx_bytes = int(line[9])
                total += tx_bytes - prev_tx.get(iface, tx_bytes)
                prev_tx[iface] = tx_bytes
        open(fname, 'a').write(','.join([t,
                                         str(total * 8 / interval_sec / 1e6), str(total)]) + "\n")
        sleep(interval_sec)
    return


def monitor_qlen(iface, interval_sec=0.01, fname='qlen.txt'):
    pat_queued = re.compile(r'backlog\s[^\s]+\s([\d]+)p')
    pat_dropped = re.compile(r'dropped\s([\d]+),')
    cmd = "tc -s qdisc show dev %s" % (iface)
    open(fname, 'w+').write('')
    fname2 = fname.split(".txt")[0] + "_DT.txt"
    open(fname2, 'w').write('')
    while 1:
        p = Popen(cmd, shell=True, stdout=PIPE)
        output = p.stdout.read()
        matches = pat_queued.findall(output)
        matches_d = pat_dropped.findall(output)
        if matches and len(matches) > 1:
            t = "%f" % time()
            open(fname, 'a').write(
                t + ',' + matches[-2] + ',' + matches_d[-2] + '\n')
            open(fname2, 'a').write(
                t + ',' + matches[-1] + ',' + matches_d[-1] + '\n')
        sleep(interval_sec)
    return


def qmon(pat):
    monitor = Process(target=monitor_qlen, args=(
        "s1-eth1", 0.01, '%s_sw0-qlen.txt' % pat))
    monitor.start()
    print("Monitoring Queue Occupancy ... will save it to %s_sw0-qlen.txt " % "qlen_test")

    return monitor


def ping_latency(net, host):
    "(Incomplete) verify link latency"
    h1 = net.getNodeByName(host)
    h1.sendCmd('ping -c 20 10.0.0.7')
    result = h1.waitOutput()
    print("Ping result:")
    print(result.strip())


def start_video_clients(num_video, algorithm, net, run, **params):

    ## we use fixed movie - TODO: add url as argument

    # our array of processes
    processes = []

    print("Num. of video clients: " + num_video)
    for i in range(2, 2+int(num_video)):
        temp_host = net.getNodeByName('h%d' % i)
        # lets create name for this client
        client_name = "client"+str(i)+"/"
        client_config = "/configure_"+str(i)+".json"
        # - files
        log_folder = params["output_folder"] + "/R" + \
            str(run) + params["current_folder"]+log_folder_name+"/"+client_name

        # lets create the file output folder structure
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        params["client_name"] = client_name
        params["client_config"] = client_config
        modify_dict(params["dic"], i, run, **params)

        # lets call each client from within its output folder
        temp_host.cmd("cd " + log_folder+"../../")

        cmd = params["cwd"]+"/../godash/godash/godash --config " + \
            params["output_folder"]+"/R" + \
            str(run)+params["current_folder"]+config_folder_name+client_config

        # print(cmd)
        sleep(2)

        temp_host.cmd(cmd + " &")
        processes.append(temp_host)

        print("Started video client ID " + str(i))

    return processes


def start_voip_clients(server_host, client_host, num, subfolder, run):

    voip_s1 = client_host.popen(
        "ITGRecv -l %s/recv_%d_log_R%d" % (subfolder, num, run))
    print("starting sending")
    server_host.popen("ITGSend voipclients -l sender_log_file1")


def genstats_voip_clients(server_host, client_host, num, subfolder, run, time_stamp):
    input_file = "%s/recv_%d_log_R%d" % (subfolder, num, run)
    out_file = "%s/out_%d_log_R%d" % (subfolder, num, run)
    summ_file = "%s/%s_summ_%d_log_R%d" % (subfolder, time_stamp[1:], num, run)
    voip_s1 = client_host.cmd("ITGDec %s > %s" % (input_file, summ_file))
    voip_s1 = client_host.popen("rm %s" % (input_file))
    voip_s1 = client_host.popen("rm sender_log_file1")
    voip_s1 = client_host.popen("rm voipclients")


def prepare_voip_clients(num_voip, host, dur):
    ip_address = host.cmdPrint(
        "ifconfig %s-eth0 | grep inet | awk '{print $2}' | sed 's/addr://'" % host.name).split()[0]
    with open("voipclients", "w+") as myfile:
        for i in range(num_voip):
            # currently hardcoded G.711
            myfile.write("-a %s -t %d -rp %d VoIP -x G.711.2 -h RTP -VAD\n" %
                         (ip_address, dur, 10001+i))


class TwoSwitchTopo(Topo):
    '''Two switches connected to n hosts (web+video+voip).'''

    def build(self, total_num_hosts=5):
        # creating server node
        serverHost = self.addHost('h1', ip='10.0.0.1/8')
        if args.collaborative == "on":
            consulHost = self.addHost('c1', ip='10.0.0.2/8')

        # create client nodes for video, web and voip
        for i in range(total_num_hosts-1):
            self.addHost('h%d' % (i+2), ip='10.0.0.%d/8' % (i+3))

        # Create two switches
        s0 = self.addSwitch('s0')
        s1 = self.addSwitch('s1')

        # bottleneck link
        self.addLink('s1', 's0', bw=1000, delay=str(args.delay)+'ms')

        # add link between server and switch
        self.addLink('h1', 's1', bw=1000, delay='5ms')

        if args.collaborative == "on":
            s2 = self.addSwitch('s2')
            # add links for consul
            self.addLink('c1', 's2', bw=1000, delay='5ms')
            self.addLink('s2', 's0', bw=1000, delay='5ms')

        # add links between hosts and a switch s1
        for i in range(total_num_hosts-1):
            self.addLink('h%d' % (i+2), 's0', bw=1000, delay='5ms')


def goDashBedNet():
    "Create network and run experiment"

    # lets start to check on the script arguements:
    if args.serverType != "ASGI" and args.serverType != "WSGI":
        print("\n**** Incorrect Web Server has been choosen ****")
        print("**** Please choose either ASGI (Hypercorn) or WSGI (Caddy and QUIC) ****\n")
        sys.exit(0)

    print("preparing config files for goDASH")
    # lets read in the goDASH config file
    cwd = os.getcwd()
    config_direct = cwd + "/config"
    config_file = config_direct+"/configure.json"
    # lets read in the original config file and create a dictionary we can use
    _dict = create_dict(config_file)
    # print("How this dict looks alike: ")
    test_dict = create_dict_from_json(config_file)

    # lets create the log and config folder locations
    output_folder = cwd+output_folder_name

    print("starting mininet ....")

    # all voip clients are run one one mininet node with different ports
    if int(args.voipclients) > 0:
        num_voip = 1
    else:
        num_voip = 0
    # all voip clients will be handled by one host, plus one host storing video content
    # TODO: add support for web traffic
    total_num_hosts = int(args.videoclients) + num_voip + 1
    print("Total number of host : " + str(total_num_hosts))

    # for each run
    for run in range(1, 1+int(args.numruns)):

        trace_files = ["traces/"
                       + f for f in listdir("traces/") if isfile(join("traces/", f))]
        # for each trace file
        for trace_file in trace_files:

            # Create topology
            topo = TwoSwitchTopo(total_num_hosts=total_num_hosts)
            net = Mininet(controller=Controller, link=TCLink, topo=topo)

            net.start()

            # get voip client host - it is the last
            voip_host = net.getNodeByName('h%d' % (total_num_hosts))
            # leaverage D-ITG capabilites
            prepare_voip_clients(int(args.voipclients), voip_host,
                                 1000*int(args.duration))

            # wait for 5 seconds
            sleep(5)
            dumpNodeConnections(net.hosts)

            #print (pid_python)
            serverHost = net.getNodeByName('h1')
            ip_address_sh = serverHost.cmdPrint(
                "ifconfig %s-eth0 | grep inet | awk '{print $2}' | sed 's/addr://'" % serverHost.name).split()[0]

            # start consul
            if args.collaborative == "on":
                consul = net.getNodeByName('c1')
                #consul.cmd("consul -force-leave")
                print("starting consul")
                ttt = consul.cmd(
                    "consul agent -dev -client 10.0.0.2 > ./output/consul_log.out &")
                sleep(5)

            # stop the apache server
            tt4 = serverHost.cmd("sudo systemctl stop apache2.service")

            # check to see if Caddy/Example or Hypercorn is being used
            if args.serverType == "WSGI":
                print("Calling WSGI Server...", end=" ")
                if args.transport_mode == "quic":
                    tt = serverHost.cmd(
                        "sudo setcap CAP_NET_BIND_SERVICE=+eip caddy")
                    if args.cliBoolean == "off":
                        print("- QUIC enabled...")
                        tt2 = serverHost.cmd(
                            'caddy start --config ' +
                            './caddy-config/TestbedTCP/CaddyFilev2QUIC ' +
                            '--adapter caddyfile')

                elif args.transport_mode == "tcp":
                    tt = serverHost.cmd(
                        "sudo setcap CAP_NET_BIND_SERVICE=+eip caddy")
                    if args.cliBoolean == "off":
                        print("- TCP HTTPS enabled...")
                        tt2 = serverHost.cmd(
                            'caddy start --config ' +
                            './caddy-config/TestbedTCP/CaddyFilev2TCP ' +
                            '--adapter caddyfile')

            elif args.serverType == "ASGI":
                print("Calling Hypercorn ASGI Server...", end=" ")
                tt1 = serverHost.cmd(
                    "sudo setcap CAP_NET_BIND_SERVICE=+eip hypercorn")
                if args.cliBoolean == "off":
                    if args.transport_mode == "quic":
                        print("- QUIC enabled...")
                        # print("For ASGI, please select --tm \"tcp\"\n")
                        # clean_up(voip_host)
                        # sys.exit(0)
                        tt = serverHost.cmd(
                            "hypercorn"
                            " hypercorn_goDASHbed_quic:app &")
                    elif args.transport_mode == "tcp":
                        # this permits http to https redirection - if we need it
                        # tt = serverHost.cmd(
                        #     "hypercorn"\
                        # " --certfile ../goDASH/godash/http/certs/cert.pem"\
                        # " --keyfile ../goDASH/godash/http/certs/key.pem"\
                        # " --bind www.goDASHbed.org:443"\
                        # " --insecure-bind www.goDASHbed.org:80"\
                        # " hypercorn_goDASHbed:redirected_app &")

                        # lets do this dependent on the structure of the input urls
                        if "https" in urls[0]:
                            print("- TCP HTTPS enabled...")
                            tt = serverHost.cmd(
                                "hypercorn"
                                # " --certfile ../goDASH/godash/http/certs/cert.pem"
                                # " --keyfile ../goDASH/godash/http/certs/key.pem"
                                # " --bind www.goDASHbed.org:443"
                                " hypercorn_goDASHbed:app &")
                        else:
                            print("- TCP HTTP enabled...")
                            tt = serverHost.cmd(
                                "hypercorn"
                                # " --bind www.goDASHbed.org:80"
                                " hypercorn_goDASHbed:app &")

            sleep(3)

            # get ip address of server host
            s1 = net.getNodeByName('s1')
            s0 = net.getNodeByName('s0')

            print("Load bw values from trace: " + trace_file)
            if ".csv" in trace_file:
                bw_a = readCsvThr(trace_file)

            print("Setting fifo queueing discipline")
            getVersion = subprocess.Popen("bash tc_fifo.sh %s %d" % (
                    "s1-eth1", args.bw_net), shell=True, stdout=subprocess.PIPE).stdout
            for intf in s0.intfList()[2:]:
                getVersion2 = subprocess.Popen("bash tc_delay.sh %s %d" % (
                    intf.name, 10), shell=True, stdout=subprocess.PIPE).stdout
            sleep(5)

            # create a folder based on date and time for each run
            current_folder = "/" + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

            # - config
            config_folder = output_folder+"/R" + \
                str(run)+current_folder+config_folder_name

            # lets create the output folder structure
            if not os.path.exists(config_folder):
                os.makedirs(config_folder)

            print('output_folder: ' + output_folder)
            print('current folder: ' + current_folder)
            subfolder = output_folder+'/R'+str(run)+current_folder+'/voip/'
            if not os.path.exists(subfolder):
                os.system("mkdir -p %s" % subfolder)
            # start voip clients
            start_voip_clients(serverHost, voip_host,  int(
                args.voipclients), subfolder, run)

            # start the video clients and save as an array of processes
            processes = start_video_clients(args.videoclients, test_dict['adapt'], net, run, num_clients=total_num_hosts,
                                            output_folder=output_folder, current_folder=current_folder, config_folder=config_folder, dic=test_dict, cwd=cwd)

            if args.cliBoolean == "on":
                CLI(net)

            # lets start throttling the link
            tl = ThrottleLink()
            t = Thread(target=tl.run, args=(bw_a, ))
            t.start()
            # lets check if the client have completed
            vc = threading.Thread(
                target=video_clients_completed(processes, tl), daemon=True)
            vc.start()
            #  once the client complete, lets stop the throttling
            tl.terminate()

            sleep(2)
            print("all godash clients have finished streaming")
            # reset the system network
            os.system(
                "tc class change dev s1-eth1 parent 1:0 classid 1:1 htb rate %fkbit ceil %fkbit" % (10000, 10000))

            genstats_voip_clients(serverHost, voip_host,  int(
                args.voipclients), subfolder, run, current_folder)

            net.stop()
            if args.transport_mode == "tcp" and args.serverType == "WSGI":
                Popen("pgrep -f caddy | xargs kill -9", shell=True).wait()
                caddy_s1 = serverHost.popen("rm ./output/caddy_access.log")
            if args.transport_mode == "quic" and args.serverType == "WSGI":
                Popen("pgrep -f example | xargs kill -9", shell=True).wait()
            if args.collaborative == "on":
                # lets stop consul
                os.system("killall -9 consul")


if __name__ == '__main__':
    os.system("mn -c")
    setLogLevel('output')
    goDashBedNet()
    os.system("chmod 777 -R *")
