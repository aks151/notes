# Multigres Distributed Systems Learning Journey

**Owner:** AKS  
**Goal:** Master distributed systems and high-performance backend engineering by learning and contributing to Multigres.  
**Repository Location:** `/Users/aks/Desktop/multigres`  
**Git Setup:**
* `origin` $\rightarrow$ `https://github.com/aks151/multigres.git` (Personal Fork)
* `upstream` $\rightarrow$ `https://github.com/multigres/multigres.git` (Main Open-Source Repo)

---

## 1. What is Multigres?

**Multigres** is "Vitess for PostgreSQL." It provides horizontal scaling, transparent sharding, connection pooling, and automated consensus-driven failover for PostgreSQL.

### History of Scaling Relational Databases
1. **Vertical Scaling:** Bigger servers (CPUs/RAM/NVMe). *Hit hardware/cost limits.*
2. **Read Replicas:** Primary + N Standby replicas via WAL replication. *Scales reads, but write throughput & storage are capped at 1 primary.*
3. **Application-Side Sharding:** Application code manually routes queries (`user_id % 64`). *High app complexity, no cross-shard JOINs/transactions.*
4. **Connection Poolers (PgBouncer):** Multiplexes client connections down to fewer PG connections. *Does not shard or route queries.*
5. **NewSQL (CockroachDB/YugabyteDB):** Re-implements DB engine from scratch. *Not 100% stock PostgreSQL compatible.*
6. **Middleware Sharding (Multigres):** Sits in front of standard, un-modified PostgreSQL. Provides transparent sharding, connection pooling, and consensus failover while maintaining 100% native PostgreSQL compatibility.

---

## 2. Architecture & Service Breakdown

* **`multigateway`**: PostgreSQL wire protocol proxy. Parses SQL to ASTs, plans queries, and routes them to appropriate poolers.
* **`multipooler`**: Connection pooler and query executor daemon sitting in front of PostgreSQL.
* **`pgctld`**: Local PostgreSQL process manager (starts, stops, reconfigures postgres instances).
* **`multiorch`**: Cluster orchestrator for consensus, leader election, and health checks via `etcd`.
* **`multiadmin` / `multigres`**: Admin gRPC service and CLI tool.

---

## 3. Deep Dive Logs & Key Lessons Covered

### A. The `multigateway` Request Lifecycle
```
Client (psql/ORM) ──> pgprotocol Server ──> MultigatewayHandler
                                                 │
                                 ┌───────────────┴───────────────┐
                                 ▼                               ▼
                           Parser (SQL->AST)              Planner (Query Plan)
                                                                 │
                                                                 ▼
                                                    Engine Primitives (Route/Scatter)
                                                                 │
                                                                 ▼
                                                  ScatterConn ──> gRPC to multipooler
```
* **Key Files:** 
  * `go/common/pgprotocol/server/server.go` (TCP/TLS/SCRAM auth)
  * `go/services/multigateway/handler/handler.go` (`HandleQuery`, `HandleParse`, `HandleBind`, `HandleExecute`)
  * `go/services/multigateway/executor/executor.go` (Plan cache + execution)
  * `go/services/multigateway/planner` (Builds primitive trees: `Route`, `Scatter`, `Transaction`)

---

### B. `multipooler` Connection Pool & Concurrency Deep Dive
* **Key Files:** 
  * `go/services/multipooler/internal/pools/connpool/pool.go`
  * `go/services/multipooler/internal/pools/connpool/waitlist.go`
  * `go/services/multipooler/internal/pools/connpool/stack.go`

#### Key Techniques Learned:
1. **State-Aware Connection Bucketing:**
   * Connections with no custom state live in the `clean` LIFO stack.
   * Connections with active session state (e.g. `SET search_path = 'app'`) are bucketed into 8 `states` stacks by state hash (`bucket = hash & 7`).
   * When a client requests a specific state, `connpool` reuses a pre-configured connection without sending `SET` queries to PostgreSQL!
2. **Zero-Allocation Node Recycling:**
   * `waitlist` uses `sync.Pool` (`wl.nodes`) to recycle `list.Element` structures and unbuffered `conn chan *Pooled[C]` channels.
3. **Zero-Polling Channel Handoff:**
   * Waiting threads block in a Go `select` statement listening to:
     * `closeChan` (Pool closed)
     * `ctx.Done()` (Client timeout)
     * `conn := <-elem.Value.conn` (Connection handed directly from returning thread)
4. **Context Timeout Race Resolution:**
   * When `ctx.Done()` triggers, the thread locks `wl.mu` and attempts `wl.list.Remove(elem)`.
   * If `removed == false`, another thread *already* popped the waiter and is sending a connection over the channel. The waiter ignores the timeout and safely receives `<-elem.Value.conn` to prevent connection leaks!
5. **Anti-Starvation Aging:**
   * When returning a connection, `tryReturnConnSlow` matches waiters wanting the exact same session settings.
   * Skipped waiters get their `age` incremented (`e.Value.age++`). Once `age > 8`, the pool forces a handoff to that oldest waiter, preventing starvation.

---

### C. Bug Fixes & Code Contributions Completed
1. **Timezone Offset Parsing Fix in Row Scanner (`result.go` & `result_test.go`):**
   * *Problem:* `ScanRow` failed with `cannot parse "2026-07-19 07:33:12.191706+05:30" as time.Time` when running unit tests in non-UTC timezones (like IST `+05:30`).
   * *Root Cause:* Go layout `"2006-01-02 15:04:05.999999-07"` only matches offsets without colons (e.g. `+05`).
   * *Fix:* Added `"2006-01-02 15:04:05.999999-07:00"` to both `**time.Time` and `*time.Time` switches in `go/services/multipooler/internal/executor/result.go` and added a unit test in `result_test.go`. Verified with `go test` passing 100%!
2. **`statement_timeout` Parity Testing:**
   * *Problem:* Parity test failed comparing gateway error to direct PostgreSQL 14.
   * *Lesson:* PostgreSQL 17 prints GUC error bounds with units `(0 ms .. 2147483647 ms)`, whereas PostgreSQL 14 prints `(0 .. 2147483647)`.

---

## 4. Five Exploration Tracks for Mastering Multigres

| Track | Focus Area | Core Files | Industry Skill Gained |
| :--- | :--- | :--- | :--- |
| **1. Compiler & Planner** | AST Parsing, Plan Caching, Scatter-Gather Routing | `go/common/parser/`, `go/services/multigateway/planner/` | Database Engine & Query Planner Design |
| **2. Wire Protocol** | TCP/TLS Handshakes, PG Frontend/Backend Messages, SCRAM | `go/common/pgprotocol/`, `go/services/multigateway/handler/` | Low-Level Network Systems Programming |
| **3. Concurrency & Memory (ACTIVE FOCUS)** | LIFO Pool Stacks, `sync.Pool`, Atomics, GUC Isolation, Transaction Reservation | `go/services/multipooler/internal/pools/`, `internal/executor/` | High-Performance Microsecond Backend Engineering |
| **4. Distributed Consensus** | `etcd`, Raft Quorums, Failover, Split-Brain Prevention | `go/services/multiorch/`, `go/services/pgctld/`, `go/common/consensus/` | Distributed Systems Architecture & SRE |
| **5. Control Plane** | CLI Commands, gRPC Services, Topology Schemas, Protobufs | `go/cmd/multigres/`, `go/cmd/multiadmin/`, `proto/` | Cloud-Native Infrastructure & Tooling |

### Option 3 vs Option 4 Comparison:
* **Option 3 (`multipooler`):** Single-Node SPEED & MEMORY (Mutexes, atomic operations, connection stacks, transaction reservation).
* **Option 4 (`multiorch`):** Multi-Node SURVIVAL & FAULT TOLERANCE (`etcd`, consensus quorums, heartbeats, automated leader failover).

---

## 5. Overall Progression & Next Steps

* [x] **Phase 1: Understanding & Architecture Mental Models** *(Completed for `multigateway` & `multipooler`)*
* [x] **Phase 2: First Hands-On Code Bug Fix** *(Completed: Fixed timezone offset parsing in `result.go` & `result_test.go`)*
* [ ] **Phase 3: Deep Dive into Track 3 (Concurrency, Memory & Transactions in `multipooler`)** *(In Progress)*
* [ ] **Phase 4: Open Source Portfolio & Senior Backend Interview Readiness**

---

*Last updated: 2026-07-24 (Saved inside notes repo at `multigres/MULTIGRES_LEARNING_JOURNEY.md`)*
