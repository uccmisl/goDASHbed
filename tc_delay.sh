#!/bin/bash
dev=$1
delay=$2ms
function add_qdisc_host {

    tc qdisc del dev $dev root
    echo qdisc removed

    # add qdisc to s0-eth1/s0-eth2 with htb and default class 1:1
    #tc qdisc add dev $dev root handle 1:0 htb default 1
    #echo qdisc added

    echo tc qdisc add dev $dev root netem delay $delay
    tc qdisc add dev $dev root netem delay $delay

    echo delay $delay added
}




add_qdisc_host
