#!/usr/bin/env python2

import os
import multiprocessing
import optparse
import subprocess

from mparts.configspace import ConfigSpace
from mparts.util import initializeDisk, deinitializeDisk

import hosts

# https://www.kernel.org/pub/linux/kernel/v3.x/linux-3.18.tar.xz
ROOT  = "~/bench/vm-scalability/bench"
LINUX = os.path.join(ROOT, "tmp", "linux-3.18")
LINUXSRC = os.path.join(ROOT, "..", "src", "linux")
VMROOT = "/root/bench/vm-scalability/bench"
VMLINUX = os.path.join(VMROOT, "tmp", "linux-3.18")
PERFBIN = os.path.join("~/linux/tools/perf/perf")
TRY   = 1
CPU_STEP = 10
CPU_CNTS = 80
CORES_PER_SOCKET = 10

# If set to True, do as few experiments as quickly as possible to test
# the setup.  This is useful to do before the full benchmark suite
# because it will almost certainly uncover misconfigurations that
# could halt a lengthy full benchmark part way through.

parser = optparse.OptionParser(__doc__.strip() if __doc__ else "")
parser.add_option("-d", "--dryrun",
        help="dry run (default: sanityRun = False)",
        action="store_true", default=False)
parser.add_option("-t", "--trials",
        help="trials (default: TRY = 1)",
        default="%d" % TRY)
parser.add_option("-c", "--cores",
        help="number of cores for dryrun, default = 80",
        default="80")
parser.add_option("-n", "--profile-nos",
        help="get numbers using perf stat",
        default=False, action="store_true", dest="pstat")
parser.add_option("-r", "--perf-record",
        help="record all functions",
        default=False, action="store_true", dest="precord")
parser.add_option("--kvm-record",
        help="perf record for guest, only works with -r option",
        default=False, action="store_true", dest="perfKVMRec")
parser.add_option("--guest-only-record",
        help="only records the guest, no host side recording",
        default=False, action="store_true", dest="perfGuestRec")
parser.add_option("-p", "--pin",
        help="pin all the tasks in qemu process",
        default=False, action="store_true", dest="qpin")
parser.add_option("-l", "--lockstats",
        help="get lock stats",
        default=False, action="store_true", dest="lockStats")
parser.add_option("-m", "--multivm",
        help="run two VMs simultaneously",
        action="store_true", default=False)
parser.add_option("--fs-type", dest="fsType",
        help="Specify fs type", default="")
parser.add_option("--medium", dest="medium",
        help="Specify the medium to perform benchmarking",
        default="tmpfs")
parser.add_option("--base-dir", dest="baseFSPath",
        help="Specify the path on which the experiment needs " \
              "to be done, it must exist, else the experiment will fail",
        default="")
parser.add_option("--no-caching", dest="noCaching",
        help="No caching of the files in the buffer cache",
        action="store_true", default=False)
parser.add_option("--kvm-stat", dest="kvmStat",
        help="get the kvm stats if possible (only possible for PVM)",
        action="store_true", default=False)
parser.add_option("--trace-kvm", dest="kvmTrace",
        help="get the results using trace-cmd",
        action="store_true", default=False)
parser.add_option("--probe", dest="perfProbe",
        help="use probing to know the stats",
        action="store_true", default=False)
(opts, args) = parser.parse_args()

sanityRun = opts.dryrun
trials = int(opts.trials)

if sanityRun:
    trials = 1

# For an explanation of configuration spaces and a description of why
# we use '*' and '+' all over this file, see the module documentation
# for mparts.configspace.  In short, * combines configuration options,
# while + specifies alternate configurations.  Likewise, passing a
# list to mk creates a set of alternate configurations.

mk = ConfigSpace.mk

##################################################################
# Shared configuration
#

shared = ConfigSpace.unit()

# The primary host that will run the benchmark applications.
shared *= mk(primaryHost = hosts.primaryHost)

# benchRoot specifies the directory on the primary host where MOSBENCH
# was checked out or unpacked.
shared *= mk(benchRoot = ROOT)

# textRoot specifies the directory on the primary host where the text
# to use for the Psearchy indexing benchmark can be found.  To
# reproduce the results in the paper, this should be a pristine check
# out of Linux 2.6.35-rc5.
shared *= mk(textRoot = LINUX)
# Since, the hash generated for the VM will be different,
# therefore an extra option
shared *= mk(vmTextRoot = VMLINUX)

# kernelRoot specifies the directory on the primary host where the
# kernel source to use for the gmake benchmark can be found.  To
# reproduce the results in the paper, this should be a check out of
# Linux 2.6.35-rc5.  This can be the same directory used for textRoot
# above.
shared *= mk(kernelRoot = LINUX)

# adding perf path as well
shared *= mk(linuxSrc = LINUXSRC)

# adding VM path to the configuration to be used by all benchsuites
shared *= mk(vmBenchRoot = VMROOT)

# this one is needed for running on different IO devices
shared *= mk(baseFSPath = opts.baseFSPath)

# Do we really need caching? (True or False)
shared *= mk(noCaching = opts.noCaching)

# fs specifies which type of file system to use.  This can be any file
# system type known to mkmounts except hugetlbfs.
if opts.fsType is "":
    shared *= mk(fs = "tmpfs-separate")
else:
    initializeDisk(opts.fsType, opts.medium, CPU_CNTS)
    shared *= mk(fs = opts.fsType)

# trials is the number of times to run each benchmark.  The best
# result will be taken.
shared *= mk(trials = trials)

# hotplug specifies whether or not to use CPU hotplug to physically
# disable cores not in use by the benchmark.  All cores should be
# re-enabled when the benchmark exits, even after an error.  Several
# of the benchmarks do not otherwise restrict which cores they use,
# and thus will give bogus results without this.
shared *= mk(hotplug = True)

# need the step count info for VM for it to be NUMA aware!
shared *= mk(coresPerSocket = CORES_PER_SOCKET)

# cores specifies the number of cores to use.  This must be
# non-constant and must be the last variable in the shared
# configuration for the graphing tools to work (which also means it
# generally shouldn't be overridden per benchmark).
if sanityRun:
    shared *= mk(cores = [int(opts.cores)], nonConst = True)
else:
    #shared *= mk(cores = [1] + range(0, CPU_CNTS+1, CPU_STEP)[1:], nonConst = True)
    shared *= mk(cores = range(CPU_CNTS, 0, -CPU_STEP) + [4] + [2] + [1], nonConst = True)

# perf record and perf stat option globally
shared *= mk(pstat = False if opts.precord is True else opts.pstat)
shared *= mk(precord = opts.precord)
shared *= mk(perfBin = PERFBIN)
shared *= mk(perfKVMRec = opts.perfKVMRec)
shared *= mk(perfGuestRec = opts.perfGuestRec)
shared *= mk(lockStats = opts.lockStats)
shared *= mk(multiVM = opts.multivm)
shared *= mk(kvmStat = opts.kvmStat)
shared *= mk(kvmTrace = opts.kvmTrace)
shared *= mk(perfProbe = opts.perfProbe)

# pinning task
shared *= mk(qpin = opts.qpin)

##################################################################
# gmake
#

import gmake
gmake = mk(benchmark = gmake.runner, nonConst = True)


# gmake_qemu
import gmake_qemu
gmake_qemu = mk(benchmark = gmake_qemu.runner, nonConst = True)

##################################################################
# Exim
#
# eximBuild - The build name of Exim to run.  Corresponds to a
# subdirectory of the exim/ directory that contains an Exim
# installation.
#
# eximPort - The port Exim should listen on.
#
# clients - The number of client load generators to run.
import exim

exim = mk(benchmark = exim.runner, nonConst = True)

exim *= mk(eximBuild = "exim-mod")
exim *= mk(eximPort = 2526)
exim *= mk(clients = 160)

##################################################################
# RocksDB
#
# benchmark - name of the benchmark to be selected
#
# duration - time to launch (40 seconds by default)
#
# disable_wal - write ahead logging (disabled by default)
#
# disable_data_sync - fsycn (disabled by default)
#
# compression_type - data compression (disabled)
#
# compression_level - level of data compression
#
# threads - client threads (2 is more than sufficient)
#
# max_background_compactions - #threads for data
# compression (#NCPUs)
#
# max_background_flushes - #threads for data flush (#NCPUs)
#
# value_size - size of the value corresponding to a key (8192 B)
#
# readwritepercent - read vs write percentage for
# readrandomwriterandom workload
import rocksdb

rocksdb = mk(benchmark = rocksdb.runner, nonConst = True)
rocksdb *= (mk(benchName = ["overwrite"]) +
           mk(benchName = ["appendrandom"]) +
           mk(benchName  = ["readrandomwriterandom"]))
rocksdb *= mk(duration = 40)
rocksdb *= mk(dataSync = False)
rocksdb *= mk(disableWAL = False)
rocksdb *= mk(compressionType = "none")
rocksdb *= mk(compressionLevel = 0)
rocksdb *= mk(clientThreads = 2)
rocksdb *= mk(valueSize = 8192)
rocksdb *= mk(rdwrPercent = 50)

##################################################################
# Complete configuration
#

# XXX Hmm.  Constant analysis is space-global right now, so combining
# spaces for different benchmarks may give odd results.

# We compute the product of the benchmark configurations with the
# shared configuration instead of the other way around so that we will
# perform all configurations of a given benchmark before moving on to
# the next, even if the shared configuration space contains more than
# one configuration.  Furthermore, instead of computing the regular
# product, we compute a "merge" product, where assignments from the
# left will override assignments to the same variables from the right.
# configSpace = ((gmake + gmake_docker).merge(shared))
#configSpace = exim.merge(shared)
#configSpace = memcached.merge(shared)
#configSpace = apache.merge(shared)
#configSpace = postgres.merge(shared)
#configSpace = gmake.merge(shared)
#configSpace = gmake_docker.merge(shared)
#configSpace = gmake_fakeroot.merge(shared)
#configSpace = psearchy.merge(shared)
#configSpace = metis.merge(shared)

suite = None
for a in args:
    s = eval(a)
    suite = suite + s if suite else s

if suite is None:
    print "Please specify benchmark to run:"
    print "  (e.g., gmake gmake_qemu)"

configSpace = suite.merge(shared)

##################################################################
# Run
#

if __name__ == "__main__":
    from mparts.manager import generateManagers
    from mparts.rpc import print_remote_exception
    import sys
    sys.excepthook = print_remote_exception
    for (m, cfg) in generateManagers("sanity" if sanityRun else "results", configSpace):
        cfg.benchmark.run(m, cfg)
    # its cleanup time!
    if opts.fsType is not "":
        deinitializeDisk(opts.fsType, opts.medium)
