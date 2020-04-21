#!/bin/bash

dev=$1
rate=$2Mbit

function add_qdisc {
    
    echo $dev
    tc qdisc del dev $dev root
    echo qdisc removed

    # add qdisc to s0-eth1/s0-eth2 with htb and default class 1:1
    tc qdisc add dev $dev root handle 1: htb default 1
    echo qdisc added
    # create class 1:1 and limit rate to 6Mbit
    tc class add dev $dev parent 1: classid 1:1 htb rate $rate ceil $rate
    echo classes created
    tc qdisc add dev $dev parent 1:1 handle 2: pfifo limit 1000



    #tc filter add dev $dev  protocol ip  parent 2:0 prio 2 flowid 2:2
    
 
    
}

add_qdisc
