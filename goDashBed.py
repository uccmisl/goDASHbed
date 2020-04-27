#!/usr/bin/python3


'''
goDASHBed

Highly customizable framework for realistic large scale experimentation with two different types of traffic


          - Supported traffic types:
            -- Video: HTTP Adaptive Streaming traffic with support for two transportation modes TCP and QUIC
            -- VoIP: Realistic VoIP traffic generation (through D-ITG traffic generator[1])


Requirements:
 - Mininet (http://mininet.org/)
 - goDash (https://github.com/uccmisl/goDASH.git)
 - D-ITG (www.grid.unina.it/software/ITG//download.php)


References:

1. Alessio Botta, Alberto Dainotti, and Antonio Pescap;. 2012. A tool for the generation of realistic network workload for emerging networking scenarios. Comput. Netw. (October 2012)

example call to goDashBed.py
sudo python3 ./goDashBed.py -b 10 --videoclients 3 --duration 40 --voipclients 1 --debug "off" --numruns 1 --tm "tcp" --terminalPrint "off"
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
from random import randint
import io
import json
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
                    default=40)

# parser.add_argument('--cong',
#                     dest="cong",
#                     help="Congestion control algorithm to use",
#                     default="reno")

parser.add_argument('--numruns',
                    dest="numruns",
                    help="Numbe of times experiment needs to be repeated",
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
                    help="Transport mode (tcp or quic")

parser.add_argument('--duration',
                    dest="duration",
                    help="Duration of experiment (in seconds.)",
                    default=0)

parser.add_argument('--scenarioname',
                    dest="scenarioname",
                    help="Scenario name for experiment",
                    default="test")

parser.add_argument('--sched',
                    dest="sched",
                    default="fifo",
                    help="Queueing scheduler")

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
urls = full_url_list+main_url_list+live_url_list + \
    full_byte_range_url_list+main_byte_range_url_list


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
        if k == "storeDash":
            _dict[k] = params["client_name"]
        elif k == "logFile":
            _dict[k] = str(str(v)[:8]+"_client"+str(i))
        elif k == "terminalPrint":
            _dict[k] = args.terminalPrint
        elif k == "debug":
            _dict[k] = args.debug
        elif k == "streamDuration":
            _dict[k] = args.duration
        elif k == "quic":
            if args.transport_mode == "quic":
                _dict[k] = "on"
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


def throttleLink(bw_a):
    print("Throttling the link")
    num_of_sec = 0
    sec_step = 0

    for i in range(len(bw_a)):
        print("BW: " + str(bw_a[i][1]))
        os.system("tc class change dev s1-eth1 parent 1:0 classid 1:1 htb rate %fkbit ceil %fkbit" %
                  (bw_a[i][1], bw_a[i][1]))
        num_of_sec = num_of_sec + bw_a[i][0]/1000

        # print "Time: " +str(num_of_sec)
        if num_of_sec > int(args.duration)+5:
            print("Over "+str(args.duration) + "...")
            os.system(
                "tc class change dev s1-eth1 parent 1:0 classid 1:1 htb rate %fkbit ceil %fkbit" % (10000, 10000))
            return
        else:
            sleep(bw_a[i][0]/1000)


def monitor_devs_ng(fname="%s/txrate.txt" % ".", interval_sec=0.01):
    """Uses bwm-ng tool to collect iface tx rate stats.  Very reliable."""
    cmd = ("sleep 1; bwm-ng -I s1-eth1 -t %s -o csv "
           "-u bits -T rate -C ',' > %s" %
           (interval_sec * 1000, fname))
    Popen(cmd, shell=True).wait()


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


def rmon(pat):
    monitor = Process(target=monitor_devs_ng, args=(
        '%s_bytes_sent.txt' % pat, 1.0))
    monitor.start()
    print("Monitoring Rate")

    return monitor


def ping_latency(net, host):
    "(Incomplete) verify link latency"
    h1 = net.getNodeByName(host)
    h1.sendCmd('ping -c 20 10.0.0.7')
    result = h1.waitOutput()
    print("Ping result:")
    print(result.strip())


def start_video_clients(num_video, algorithm, buffer_level, server_ip, net, subf, run, **params):

    # we use fixed movie - TODO: add url as argument

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
        temp_host.cmd("cd " + log_folder+"../")

        cmd = params["cwd"]+"/../goDASH/godash/godash --config " + \
            params["output_folder"]+"/R" + \
            str(run)+params["current_folder"]+config_folder_name+client_config
        print(cmd)
        temp_host.cmd(cmd + " &")
        sleep(1)
        print("Started: " + str(i))


def start_voip_clients(server_host, client_host, num, subfolder, run):
    print("server voip " + server_host.name)
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


def prepare_voip_clients(num_voip, host, dur):
    ip_address = host.cmdPrint(
        "ifconfig %s-eth0 | grep inet | awk '{print $2}' | sed 's/addr://'" % host.name).split()[0]
    print("-----------")
    print("VOIP clients", ip_address)
    print("-----------")
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

        # create client nodes for video, web and voip
        for i in range(total_num_hosts-1):
            self.addHost('h%d' % (i+2), ip='10.0.0.%d/8' % (i+2))

        # Create two switches
        s0 = self.addSwitch('s0')
        s1 = self.addSwitch('s1')

        # bottleneck link
        self.addLink('s1', 's0', bw=100)

        # add link between server and switch
        self.addLink('h1', 's1', bw=100)

        # add links between hosts and a switch s1
        for i in range(total_num_hosts-1):
            self.addLink('h%d' % (i+2), 's0', bw=100)


def goDashBedNet():
    "Create network and run experiment"

    print("preparing config files for goDASH")
    # lets read in the goDASH config file
    cwd = os.getcwd()
    config_direct = cwd + "/config"
    config_file = config_direct+"/configure.json"
    # lets read in the original config file and create a dictionary we can use
    _dict = create_dict(config_file)
    # print("How this dict looks alike: ")
    test_dict = create_dict_from_json(config_file)
    # print(test_dict)
    print("---- end dict ------")
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
            print('h%d' % (total_num_hosts))
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

            # stop the apache server
            tt4 = serverHost.cmd("sudo systemctl stop apache2.service")

            if args.transport_mode == "quic":
                print("Starting QUIC server")
                #tt = serverHost.cmd("./caddy -host %s -port 8081 -quic -root ./ &"%ip_address_sh)
                #tt4 = serverHost.cmd("sudo systemctl stop apache2.service")
                #tt = serverHost.cmd("sudo setcap CAP_NET_BIND_SERVICE=+eip caddy")
                #tt1 = serverHost.cmd("./caddy -conf ./caddy-config/Testbed/Caddyfile -quic &")
                #tt1 = serverHost.cmd("./caddy -conf ./caddy-config/Caddyfile -quic &")
                tt2 = serverHost.cmd("sudo setcap CAP_NET_BIND_SERVICE=+eip example")
                # tt1 = serverHost.cmd("./example -conf ./caddy-config/Caddyfile -quic &")
                tt = serverHost.cmd(
                    "./example '-bind=www.godashbed.org:443' '-www=/var/www/html' &")
            elif args.transport_mode == "tcp":
                print("Starting TCP server")
                tt2 = serverHost.cmd("sudo setcap CAP_NET_BIND_SERVICE=+eip caddy")
                #tt = serverHost.cmd('./caddy -host %s -port 8080 -root /var/www/html &'%ip_address_sh)
                tt = serverHost.cmd(
                    './caddy -conf ./caddy-config/TestbedTCP/Caddyfile &')
            #print(tt)
            sleep(3)
            #print (tt)
            #pid_python = int(tt.split()[1])
            # get ip address of server host
            s1 = net.getNodeByName('s1')
            s0 = net.getNodeByName('s0')
            print(s1.intfList())
            print(s0.intfList()[2:])
            subfolder = args.scenarioname + "_R" + \
                str(args.numruns) + '/godash_' + test_dict['adapt'] + \
                '_' + str(total_num_hosts).zfill(3)
            os.system("mkdir -p %s" % subfolder)

            print("Load bw values from trace: " + trace_file)
            if ".csv" in trace_file:
                bw_a = readCsvThr(trace_file)
            # creating bottleneck
            print("exec tc_q_drr.sh")
            print(serverHost.nameToIntf)
            print("-----------")
            print("Video server", serverHost.params["ip"].split("/")[0])
            print("-----------")
            if args.sched == "fifo":
                print("fifo")
                getVersion = subprocess.Popen("bash tc_fifo.sh %s %d" % (
                    "s1-eth1", args.bw_net), shell=True, stdout=subprocess.PIPE).stdout
            for intf in s0.intfList()[2:]:
                getVersion2 = subprocess.Popen("bash tc_delay.sh %s %d" % (
                    intf.name, args.delay), shell=True, stdout=subprocess.PIPE).stdout
            sleep(5)


            # create a folder based on date and time for each run
            current_folder = "/" + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

            # - config
            config_folder = output_folder+"/R" + \
                str(run)+current_folder+config_folder_name
            print(config_folder)

            # lets create the output folder structure
            if not os.path.exists(config_folder):
                os.makedirs(config_folder)

            #continue

            # start voip clients
            start_voip_clients(serverHost, voip_host,  int(
                args.voipclients), subfolder, run)
            # start video clients
            print("IP address something: " + ip_address_sh)
            start_video_clients(args.videoclients, test_dict['adapt'], 30, ip_address_sh, net, subfolder, run, num_clients=total_num_hosts,
                                output_folder=output_folder, current_folder=current_folder, config_folder=config_folder, dic=test_dict, cwd=cwd)
            #start_iperf(net)
            print("sleeping")
            throttleLink(bw_a)
            os.system(
                "tc class change dev s1-eth1 parent 1:0 classid 1:1 htb rate %fkbit ceil %fkbit" % (1000, 1000))
            sleep(int(args.duration)+10)
            # Popen("pgrep -f dashc | xargs kill -9", shell=True).wait()
            # Popen("killall -9 cat", shell=True).wait()
            #sleep(15)
            genstats_voip_clients(serverHost, voip_host,  int(
                args.voipclients), subfolder, run, current_folder)
            #sleep(5)
            #CLI(net)

            net.stop()
            if args.transport_mode == "tcp":
                Popen("pgrep -f caddy | xargs kill -9", shell=True).wait()
            if args.transport_mode == "quic":
                Popen("pgrep -f example | xargs kill -9", shell=True).wait()
            #Popen("pgrep -f godash | xargs kill -9", shell=True).wait()
            #Popen("killall -9 MP4Client", shell=True).wait()


if __name__ == '__main__':
    os.system("mn -c")
    setLogLevel('output')
    goDashBedNet()
    os.system("chmod 777 -R *")
