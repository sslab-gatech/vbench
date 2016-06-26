__all__ = ["primaryHost"]

from mparts.host import Host

primaryHost = Host("optimus.gtisc.gatech.edu")

"""clientHosts = ["headstrong.gtisc.gatech.edu", #16 core
        "pareto.gtisc.gatech.edu", #80 core
        #"bumblebee.gtisc.gatech.edu", #12 core
        #"goldbug.gtisc.gatech.edu", #32 core
        #"thrust.gtisc.gatech.edu", #8 core
        #"bombshell.gtisc.gatech.edu" #32 core
        ]
anotherClients = ["172.30.130.70"] # this is headstrong

clients = dict((hostname.split(".",1)[0], Host(hostname))
        for hostname in clientHosts)

for host in clients.values():
    host.addRoute(primaryHost, "172.30.130.71")

host.addRoute(primaryHost, anotherClients[0])

# Postgres
#postgresClient = clients["pareto"]"""
