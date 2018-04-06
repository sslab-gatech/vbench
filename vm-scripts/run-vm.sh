#!/bin/bash

cores=$(($2 * $3))
taskset -c 0-${cores} qemu-system-x86_64 --enable-kvm \
	-m 128G \
	-device virtio-serial-pci,id=virtio-serial0,bus=pci.0,addr=0x6 \
	-drive file=$1,cache=none,if=none,id=drive-virtio-disk0,format=$7 \
	-device virtio-blk-pci,scsi=off,bus=pci.0,addr=0x7,drive=drive-virtio-disk0,id=virtio-disk0 \
	-netdev user,id=hostnet0,hostfwd=tcp::$4-:22 \
	-device virtio-net-pci,netdev=hostnet0,id=net0,bus=pci.0,addr=0x3 \
	-vnc :$6 \
	-cpu host \
        -numa node,nodeid=0,mem=16G,cpus=0-9 \
        -numa node,nodeid=1,mem=16G,cpus=10-19 \
        -numa node,nodeid=2,mem=16G,cpus=20-29 \
        -numa node,nodeid=3,mem=16G,cpus=30-39 \
        -numa node,nodeid=4,mem=16G,cpus=40-49 \
        -numa node,nodeid=5,mem=16G,cpus=50-59 \
        -numa node,nodeid=6,mem=16G,cpus=60-69 \
        -numa node,nodeid=7,mem=16G,cpus=70-79 \
	-qmp tcp:172.30.240.71:$5,server,nowait \
	-smp cores=$2,threads=1,sockets=$3 \
	-realtime mlock=off &



# start the vm
sleep 4
python /home/sanidhya/bench/vm-scalability/bench/vm-scripts/pin-vcpu.py $5 ${cores}
