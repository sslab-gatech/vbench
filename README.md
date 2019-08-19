### VBench

VBENCH is a fork of MOSBENCH but allows running benchmarks inside
VM as well.

## Supported benchmarks:

- Currently, we have included the following benchmarks for evaluation:
  - Gmake: Fork intensive, but spends most of the time in the userspace.
  - Exim: Crazily stresses `mm`, `fs`, and `process` sub-systems.
  - Psearchy: Stresses the interrupt service, used to stress the writer side of the `mmap_rwsem`.
  - Metis: Stresses the reader side of the `mmap_sem`.
  - Hist: Stresses the reader side of the `mmap_sem`.

## Setup environment

- First compile the relevant benchmarks as follows:
  - Exim: `make all-exim`
  - Psearchy: `make all-psearchy`
  - Metis: `make all-metis`
  - Hist: `make all-hist`

- Configure the following variables in the `config.py`:
```python
    ROOT = "~/vbench" # Provide the relative path (this is also used in the VM)
    CPU_CNTS = 160 # Total number of cores (cores * sockets)
    CORES_PER_SOCKET = 10
    CPU_STEP = 10 # Numbers of cores to increase until CPU_CNTS in each run
```

- Modify the hostname in the hosts.py. You can set it to `127.0.0.1` and disable sanity check in `mparts/host.py`

- Create multiple `tmpfs` partitions with the following command:
```bash
  $ sudo ./mkmounts tmpfs-separate # sudo is mandatory
```

- After this, you can use `config.py` to execute benchmarks.
```bash
 $ ./config.py -h

Options:
  -h, --help            show this help message and exit
  -d, --dryrun          dry run (default: sanityRun = False)
  -t TRIALS, --trials=TRIALS
                        trials (default: TRY = 1)
  -c CORES, --cores=CORES
                        number of cores for dryrun, default = 80
  -n, --profile-nos     get numbers using perf stat
  -r, --perf-record     record all functions
  --kvm-record          perf record for guest, only works with -r option
  --guest-only-record   only records the guest, no host side recording
  -p, --pin             pin all the tasks in qemu process
  -l, --lockstats       get lock stats
  -m, --multivm         run two VMs simultaneously
  --kvm-stat            get the kvm stats if possible (only possible for PVM)
  --trace-kvm           get the results using trace-cmd
```

### Executing a benchmark
- To run a benchmark, here `exim`, across all cores, execute the following:
```bash
 $ ./config.py exim # runs the exim benchmark from core 1 to core 160.
```

- After running the benchmark, results are displayed on the terminal
  and are stored in the results folder, which can be used for plotting
  by using the `./graph` script.
