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
PERFBIN = os.path.join("/home/sanidhya/research/linux/tools/perf/perf")
TRY   = 1
CPU_STEP = 10
CPU_CNTS = 160
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
    initializeDisk(opts.fsType, CPU_CNTS)
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
    shared *= mk(cores = range(CPU_CNTS, 0, -CPU_STEP) + [1], nonConst = True)

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

import fsgmake
fsgmake = mk(benchmark = fsgmake.runner, nonConst = True)

##################################################################
# Metis
#
# streamflow - Whether or not to use the Streamflow parallel
# allocator.
#
# model - The memory allocation model to use.  Either "default" to use
# 4K pages or "hugetlb" to 2M pages.  "hugetlb" requires the
# Streamflow allocator.
#
# order - The sequence to assign cores in.  "seq" or "rr".
# XXX: currently, hugetlb is not working, streamflow seg faults

import metis
metis = mk(benchmark = metis.runner, nonConst = True)
metis *= mk(streamflow = True)
metis *= mk(model = ["default"])
metis *= mk(order = ["rr"])


import metis_qemu
metis_qemu = mk(benchmark = metis_qemu.runner, nonConst = True)
metis_qemu *= mk(streamflow = True)
metis_qemu *= mk(model = ["default"])
metis_qemu *= mk(order = ["rr"])

##################################################################
# psearchy
#
# mode - The mode to run mkdb in.  Must be "thread" or "process".
#
# seq - The sequence to assign cores in.  Must be "seq" for sequential
# assignment or "rr" for round-robin assignment.
#
# mem - How much memory to allocate to the hash table on each core, in
# megabytes.
#
# dblim - The maximum number of entries to store per Berkeley DB file.
# None for no limit.
import psearchy

psearchy = mk(benchmark = psearchy.runner, nonConst = True)

if sanityRun:
    psearchy *= (mk(mode = ["thread"]) * mk(order = ["seq"]))#  +
#                 mk(mode = ["process"]) * mk(order = ["seq", "rr"]))
else:
    psearchy *= (mk(mode = ["thread"]) * mk(order = ["seq"])) # +
#                 mk(mode = ["process"]) * mk(order = ["seq", "rr"]))
psearchy *= mk(mem = 128)
psearchy *= mk(dblim = 200000)


# psearchy_qemu
import psearchy_qemu

psearchy_qemu = mk(benchmark = psearchy_qemu.runner, nonConst = True)

if sanityRun:
    psearchy_qemu *= (mk(mode = ["thread"]) * mk(order = ["seq"]))# +
#                 mk(mode = ["process"]) * mk(order = ["seq"]))
else:
    psearchy_qemu *= (mk(mode = ["thread"]) * mk(order = ["seq"]))# +
#                 mk(mode = ["process"]) * mk(order = ["seq", "rr"]))
psearchy_qemu *= mk(mem = 128)
psearchy_qemu *= mk(dblim = 200000)

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

#exim_qemu
import exim_qemu

exim_qemu = mk(benchmark = exim_qemu.runner, nonConst = True)

exim_qemu *= mk(eximBuild = "exim-mod")
exim_qemu *= mk(eximPort = 2526)
exim_qemu *= mk(clients = 160)

##################################################################
# Postgres
#
# rows - The number of rows in the database.
#
# partitions - The number of tables to split the database across.
#
# batchSize - The number of queries each client should send to
# Postgres at a time.  This causes the load generator to act like a
# connection pooler with query aggregation.
#
# randomWritePct - The percentage of queries that should be updates.
#
# sleep - The method Postgres uses to sleep when a lock is taken.  Can
# be "sysv" for SysV semaphores or "posix" for POSIX semaphores (that
# is, futexes on Linux).
#
# semasPerSet - For sysv sleep, the number of semaphores per SysV
# semaphore set.  In the kernel, each semaphore set is protected by
# one lock.  Ignored for posix sleep.
#
# lwScale - Whether or not to use scalable lightweight locks
# (read/write mutexes) in Postgres.
#
# lockScale - Whether or not to use scalable database locks in
# Postgres.  Enabling scalable database locks requires scalable
# lightweight locks.
#
# lockPartitions - The number of partitions for the database lock
# manager.  Each partition is protected by an underlying lightweight
# lock.  This must be a power of 2.  The Postgres default is 1<<4.
#
# malloc - The malloc implementation to use in Postgres.  Must be
# tcmalloc or glibc.  For tcmalloc, you'll need to install the
# tcmalloc library.
#
# bufferCache - The size of the Postgres buffer cache, in megabytes.

"""import postgres

postgres = mk(benchmark = postgres.runner, nonConst = True)

postgres *= mk(postgresClient = hosts.postgresClient)

postgres *= mk(rows = 10000000)
postgres *= mk(partitions = 0)
postgres *= mk(batchSize = 256)
if sanityRun:
    postgres *= mk(randomWritePct = [5])
else:
    postgres *= mk(randomWritePct = [0, 5])

pgopt = (mk(sleep = "sysv") * mk(semasPerSet = 16) *
         mk(lwScale = True) * mk(lockScale = True) *
         mk(lockPartitions = 1<<10))
pgstock = (mk(sleep = "sysv") * mk(semasPerSet = 16) *
           mk(lwScale = False) * mk(lockScale = False) *
           mk(lockPartitions = 1<<4))

postgres *= pgopt + pgstock
postgres *= mk(malloc = "glibc")
postgres *= mk(bufferCache = 8192)"""

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
        deinitializeDisk(opts.fsType)



