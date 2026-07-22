# Multigres High-Level Architecture Overview

Multigres is a distributed PostgreSQL system developed to behave as a drop-in replacement for PostgreSQL at planet scale. It splits data across multiple PostgreSQL database instances (shards) while presenting a single unified PostgreSQL interface to client applications.

---

## The 4 Core Components

### 1. `multigateway` (The Traffic Controller & Proxy)
* Receives standard PostgreSQL client connections and SQL statements.
* Parses SQL queries into Abstract Syntax Trees (ASTs).
* Figures out which shard(s) the query belongs to.
* Forwards sub-queries to `multipooler` instances and merges/streams the results back to the client application.

### 2. `multipooler` (The Connection Guard & Execution Manager)
* A daemon sitting directly in front of each PostgreSQL database instance.
* Maintains a warm, state-aware pool of database connections.
* Rotates and recycles connections efficiently (`clean` vs `states` stacks) to handle high-concurrency client workloads without exhausting database memory or CPU.

### 3. `pgctld` (The Process Manager Daemon)
* A process controller daemon running on the server hosting the PostgreSQL binary.
* Handles physical process lifecycle management: starting (`pg_ctl start`), stopping (`pg_ctl stop`), restarting, and editing configuration files (`postgresql.conf`).

### 4. `multiorch` (The Command Center & Cluster Orchestrator)
* The health monitor and consensus coordinator for the cluster.
* Continuously monitors node health and topology state stored in `etcd` (a fault-tolerant coordination service).
* If a primary PostgreSQL server fails, `multiorch` detects the failure within seconds, promotes a standby replica to become the new Primary, and notifies `multigateway` to route write traffic to the new leader.

---

```
Client App (psql / ORM) ──> multigateway (Proxy & Router)
                                │
                                ▼
                           multipooler (Connection Guard)
                                │
                        ┌───────┴───────┐
                        ▼               ▼
                     pgctld          PostgreSQL Instance
                        │
                        ▲
                     multiorch (Orchestrator & Health Monitor via etcd)
```
