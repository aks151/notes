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

### C. Debugging Discoveries Made
1. **Timezone Offset Parsing:**
   * *Problem:* `ScanRow` failed with `cannot parse "2026-07-19 07:33:12.191706+05:30" as time.Time`.
   * *Lesson:* PostgreSQL formats `timestamptz` in the session's local timezone. Layout `2006-01-02 15:04:05.999999-07` expects offsets without colons (`+05`), so offsets with colons (`+05:30`) fail unless `2006-01-02 15:04:05.999999-07:00` is included in the format list.
2. **`statement_timeout` Parity Testing:**
   * *Problem:* Parity test failed comparing gateway error to direct PostgreSQL 14.
   * *Lesson:* PostgreSQL 17 prints GUC error bounds with units `(0 ms .. 2147483647 ms)`, whereas PostgreSQL 14 prints `(0 .. 2147483647)`.

---

## 4. Overall Progression & Next Steps

* [x] **Phase 1: Understanding & Architecture Mental Models** *(Completed for `multigateway` & `multipooler`)*
* [ ] **Phase 2: First Hands-On Code Contributions** *(Next Step: Pick a `TODO` or unit test to implement)*
* [ ] **Phase 3: Building a Non-Trivial Feature / Optimization**
* [ ] **Phase 4: Open Source Portfolio & Senior Backend Interview Readiness**

---

*Last updated: 2026-07-22 (Saved inside notes repo at `multigres/MULTIGRES_LEARNING_JOURNEY.md`)*
