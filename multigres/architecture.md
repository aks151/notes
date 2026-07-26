Multigres

- what is it? a distributed db? will see
- they say, close drop-in replacement of PostgreSQL
- sharded system with proxies in front
- manages replicas on its own



# Approcachability
# Opinioniated


Components
#Multigateway
- provides PostgreSQL-compatible interface to users

discover and keep track of ->
- Multipoolers (db)
- current primary for each shard
- analyze incoming queries
- break them into smaller parts to outsource them 
to various shards
- and return consolidated result to user
- smoothly redirect traffic to new primary if there's
a failover

#Multipooler
- connection pooling 
- take backup of the current instance
- restore backup when a new instance is started
- implements parts of Multigres consensus protocol
- support for materilaization services

# Pgctld
- lightweight component
- allow Postgres to be run in a diff container
than the Multipooler
- allows for the Postgres to be provisioned 
independently from Multipooler. 
- Multipooler uses pgctld to start and stop
Postgres as needed.

#Multitorch
- manage failovers
- orchestrates initial bootstrap of a cluster
- what is a cluster (db)

#Multiadmin
- expose admin endpoints for cluster management.
- serves HTTP and gRPC APIs used by
multiadmin web ui and by operators


# Operator
- K8s operator
- provision resources for a cluster
- and bring up all the required multigres components

# Toposervers
- etcd clusters store runtime info for a multigres cluster
- Global toposerver - list of cells and info for corresponding local toposerver.
                        - list of db for each cluster
                        - under each db, stores durability policy and backup location
- Local toposerver - one local toposerver cluster per cell
- for component discovery
- Multipoolers register themselves with the local toposerver, which allows multigateways 
to discover them


# Multishema
- sharding related data is stored in postgres itself
- can be viewed as logical extenstion of postgres schema that
is multigres specific