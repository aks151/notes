# Complete Concurrency Theory & Architecture Roadmap

This note provides a comprehensive theoretical foundation for multi-threaded programming, JVM concurrency mechanisms, lock-free operations, thread pool management, and distributed concurrency patterns.

---

```
 ┌────────────────────────────────────────────────────────┐
 │ 1. Hardware & Memory Model (Visibility & Reordering)   │
 └──────────────────────────┬─────────────────────────────┘
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ 2. Concurrency Pitfalls (Race Conditions & Liveness)   │
 └──────────────────────────┬─────────────────────────────┘
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ 3. Synchronization & Lock Granularity (Pessimistic)    │
 └──────────────────────────┬─────────────────────────────┘
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ 4. Lock-Free & Atomic Operations (Optimistic / CAS)    │
 └──────────────────────────┬─────────────────────────────┘
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ 5. Thread Pools & Coordination Barriers                │
 └──────────────────────────┬─────────────────────────────┘
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ 6. Distributed Concurrency (System Design Level)       │
 └────────────────────────────────────────────────────────┘
```

---

## Pillar 1: Hardware & Memory Model (Why Concurrency is Hard)

At the hardware level, modern CPUs do not execute instructions one-by-one directly against RAM. CPUs utilize **L1/L2/L3 Caches**, **Registers**, and **Store Buffers**.

```
[Thread 1 on Core 1] ───> [L1/L2 Cache] ──┐
                                          ├──> [Main RAM]
[Thread 2 on Core 2] ───> [L1/L2 Cache] ──┘
```

### 1. Memory Visibility Problem
* **Concept:** When Thread 1 updates a variable `ready = true`, the value is written to Core 1's L1 cache first. Thread 2 running on Core 2 may keep reading `ready = false` from its own L1 cache indefinitely.
* **Java Solution:** `volatile` keyword or `synchronized`/`ReentrantLock`. `volatile` flushes CPU store buffers and enforces a **Happens-Before** memory visibility guarantee.

### 2. Instruction Reordering
* **Concept:** Both the compiler (JIT) and CPU reorder instructions to optimize execution, as long as single-threaded behavior doesn't change.
* **The Danger:** In multi-threaded code, instruction reordering can cause incomplete objects to become visible to other threads (e.g. Double-Checked Locking bug without `volatile`).

---

## Pillar 2: Core Concurrency Pitfalls & Hazards

### 1. The Two Types of Race Conditions
* **Read-Modify-Write:** e.g., `count++` (which is 3 steps: READ `count`, ADD 1, WRITE `count`). Two threads executing `count++` simultaneously will overwrite each other's increments (lost update).
* **Check-Then-Act:** e.g., `if (balance >= amount) balance -= amount`. You check a stale state, and by the time you act, another thread has already modified the state.

### 2. Liveness Hazards (The 4 Coffman Deadlock Conditions)
A **Deadlock** can only occur if all 4 Coffman conditions are present simultaneously:
1. **Mutual Exclusion:** Resources cannot be shared simultaneously.
2. **Hold and Wait:** A thread holds a resource while waiting for another.
3. **No Preemption:** A resource cannot be forcibly taken from a thread.
4. **Circular Wait:** Thread A waits for B, Thread B waits for A.

> **Key Rule:** Breaking **Circular Wait** (via Lock Ordering) or breaking **Hold and Wait** (via `tryLock` timeouts) completely eliminates deadlocks.

### 3. Other Liveness Hazards
* **Livelock:** Threads actively respond to each other (e.g. two people in a hallway stepping side to side repeatedly), consuming CPU without making progress.
* **Starvation:** High-priority or greedy threads hoard locks, leaving low-priority threads waiting indefinitely.

---

## Pillar 3: Synchronization & Lock Granularity

### 1. Pessimistic Locking
* Assume conflict **will** happen; block all other threads until done.
* **Intrinsic Locks (`synchronized`):** Built into Java objects. Reentrant and managed by JVM.
* **Explicit Locks (`ReentrantLock`):** Flexible locks with features like `tryLock(timeout)`, interruptible locking, and fairness policies.
* **Read-Write Locks (`ReentrantReadWriteLock`):** Allows multiple concurrent **readers**, but only one exclusive **writer**. Ideal for read-heavy workloads.

### 2. Lock Granularity & Striping
* **Coarse-Grained Locking:** Locking a whole database or whole service (`synchronized(this)`). High safety, terrible throughput.
* **Fine-Grained / Striped Locking:** Locking individual entities (`lockFor(accountId)`) or splitting data into buckets (like `ConcurrentHashMap`). High throughput, requires careful lock ordering.

---

## Pillar 4: Lock-Free Concurrency & Atomic Operations

Blocking threads via locks causes **Context Switches** (costly OS kernel transitions taking ~1,000 to 10,000 CPU cycles). Non-blocking concurrency avoids locks altogether.

### 1. Hardware Compare-And-Swap (CAS)
CPUs support atomic assembly instructions (e.g. `CMPXCHG` on x86).
```
CAS(memory_location, expected_old_value, new_value)
```
* Read `expected_old_value`.
* Attempt to swap with `new_value`.
* If another thread changed the memory location in the meantime, CAS fails. The thread retries in a loop (Optimistic Concurrency Control).

### 2. Atomic Classes in Java
* `AtomicInteger`, `AtomicLong`, `AtomicReference`: Thread-safe variables using CPU CAS under the hood without any locks.
* `LongAdder`: Uses internal cell striping to avoid CAS contention under high thread concurrency (faster than `AtomicLong` for high-write counters).

---

## Pillar 5: Thread Management & Coordination Barriers

### 1. Why Thread Pools?
Spawning a Java `new Thread()` allocates a ~1MB OS stack and incurs kernel overhead. **Thread Pools (`ExecutorService`)** reuse a fixed pool of worker threads.

#### Essential `ThreadPoolExecutor` Tuning Parameters:
* `corePoolSize`: Minimum active threads.
* `maximumPoolSize`: Max thread limit under burst load.
* `workQueue`: Queue holding pending tasks (`ArrayBlockingQueue`, `LinkedBlockingQueue`, `SynchronousQueue`).
* `handler`: Rejection Policy when pool + queue are full (`AbortPolicy`, `CallerRunsPolicy`, `DiscardPolicy`).

### 2. Thread Synchronization Barriers

| Barrier | Purpose | Real-World Use Case |
| :--- | :--- | :--- |
| **`CountDownLatch`** | One or more threads wait for $N$ events to complete. (One-time use) | Waiting for 10 microservices to report health status on startup. |
| **`CyclicBarrier`** | $N$ threads wait for each other to reach a common barrier point. (Reusable) | Parallel matrix computation where all threads sync after each iteration. |
| **`Semaphore`** | Restricts access to a fixed number of shared permits ($N$). | Limiting database connections to max 20 concurrent queries (Rate Limiting). |
| **`CompletableFuture`** | Asynchronous task chaining and reactive compositions ($A \rightarrow B \land C \rightarrow D$). | Fetching User Profile + Orders concurrently, then merging results. |

---

## Pillar 6: Distributed Concurrency (System Design Level)

When your application scales out from 1 JVM to 50 server pods, Java locks no longer work across processes.

### 1. Optimistic Concurrency Control (OCC) vs. Pessimistic (PCC)
* **Pessimistic (`SELECT ... FOR UPDATE`):** Locks database rows during a transaction. Prevents concurrent reads/writes.
* **Optimistic (Version Column):** Uses `UPDATE accounts SET balance = 90, version = version + 1 WHERE id = 1 AND version = 5`. If another pod updated row version first, `rows_affected = 0`, triggering an application-level retry.

### 2. Distributed Locks
* **Redis Redlock / ZooKeeper Ephemeral Nodes:** Lease-based locks across distributed nodes with auto-expire TTLs to prevent zombie locks if a pod crashes.

### 3. Distributed Transactions
* **2-Phase Commit (2PC):** Prepare phase $\rightarrow$ Commit phase across multiple databases (heavy, slow).
* **Saga Pattern:** Sequence of local transactions where each transaction updates state and publishes an event. If a step fails, **Compensating Transactions** roll back preceding steps.

---

### Summary Checklist for Interview Mastery

* [x] **Race Condition Types:** Read-Modify-Write vs. Check-Then-Act.
* [x] **Deadlock Avoidance:** Lock Ordering (Resource Hierarchy) & Timed Backoff (`tryLock`).
* [x] **Lock Granularity:** Coarse vs. Fine-Grained (Per-Entity Locking).
* [x] **Thread-Safety Mechanisms:** Locks (`ReentrantLock`), Lock-Free (`AtomicLong`/CAS), Volatile/Visibility.
* [x] **Thread Coordination:** `CountDownLatch`, `Semaphore`, `ExecutorService`.
* [x] **Distributed Scaling:** Database Versioning (OCC), Distributed Locks (Redis/ZK), Sagas.
