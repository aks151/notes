# SaaS License Seat Allocation & Java Concurrency Notes

System design, backend architectural patterns, interview follow-ups, and Java concurrency principles learned from the **Gronex SaaS License Seat Allocation System**.

---

## 1. Spring Boot Architecture: DTO vs Model vs Repository

In production backend applications, components are strictly separated into distinct layers:

| Layer Component | Example Class | Primary Responsibility |
| :--- | :--- | :--- |
| **Repository** | `SeatAssignmentRepository` | **Persistence Layer**: Reads & writes raw data to database/storage. Does not contain business logic. |
| **Model / Entity** | `SeatAssignment` | **Internal Domain State**: Represents database table structure & entity state. Contains mutable setters for internal service operations. |
| **DTO (Data Transfer Object)** | `SeatAssignmentResponse` | **Public API Contract**: Immutable JSON payload returned to frontend/clients. |

### Why convert Model to DTO (`toAssignmentResponse(assignment)`)?
1. **Information Hiding & Security**: Prevents exposing internal sensitive fields (e.g. hashed passwords, internal DB keys, audit logs, deleted timestamps).
2. **Decoupling DB Schema from API**: Changing database table structures does not break frontend API contracts if DTOs remain unchanged.
3. **Immutability & Safety**: Models have setters (`setStatus()`) needed by backend logic. DTOs are read-only to prevent accidental modification outside services.
4. **Preventing Circular JSON Recursion**: Avoids ORM (JPA/Hibernate) infinite loops during JSON serialization (e.g., `Org -> SeatAssignment -> Org...`).

---

## 2. System Design & Interview Follow-Up Questions

### Q1: How would you auto-reclaim idle seats fairly?
* **Problem with simple batch sweeps**: Reclaiming all idle seats indiscriminately evicts users without notice and creates poor UX.
* **Fair Reclaim Strategies**:
  1. **Least Recently Used (LRU) Eviction**: On seat allocation (`assignSeat`), if capacity is full (`seatsUsed >= seatCap`), reclaim *only the single oldest idle seat* exceeding `idleDays` to make room for the new user.
  2. **Soft Grace Period State (`PENDING_RECLAIM`)**: Transition idle seats to `PENDING_RECLAIM` and notify the user. If they log in or hit a `touch()` endpoint within 24 hours, restore status to `ACTIVE`.
  3. **Role/Priority Tiering**: Admins or VIP accounts get non-reclaimable status or extended idle thresholds.
  4. **Multi-Tenant Isolation**: Ensure per-organization locks so auto-reclaim in Org A never blocks or affects Org B.

### Q2: How would you handle seat over-subscription policies?
* **Problem with hard caps**: Hard failing immediately (`SEAT_CAP_EXCEEDED`) blocks organizational growth during hiring spikes or high-concurrency peak events.
* **Over-Subscription Policies**:
  1. **Soft Cap with Overage Billing**: Allow capacity up to e.g. 120% soft limit. Tag seats exceeding `seatCap` as `OVERAGE` and bill per seat-hour.
  2. **Temporary Burst Licenses**: Grant short-term seats valid for e.g. 4 hours during all-hands events, after which they auto-expire.
  3. **FIFO Waitlist Queue**: When full, place requests into an async queue (`SeatWaitlist`). When any seat is reclaimed or released, automatically fulfill the top waitlisted request.
  4. **Concurrent Active Sessions vs Total Users**: Allow 500 total registered users, but limit max active concurrent sessions to 100 via distributed locks / Redis.

---

## 3. Core Java Concurrency Concepts

### A. Fine-Grained Lock Striping (Per-Organization Locks)
```java
private final Map<Long, ReentrantLock> locks = new ConcurrentHashMap<>();

private ReentrantLock lockFor(long orgId) {
    return locks.computeIfAbsent(orgId, key -> new ReentrantLock());
}
```
* **Concept**: Locks are partitioned by `orgId`. 
* **Benefit**: High throughput under multi-tenancy. Requests for `Org 1` lock `lockFor(1)` and never block requests for `Org 2` on multi-core CPUs.
* **`computeIfAbsent()`**: Atomically creates lock objects without race conditions during initialization.

### B. Lock-Free Atomic Counters (`AtomicLong`)
```java
private final AtomicLong nextAssignmentId = new AtomicLong(1);
long id = nextAssignmentId.getAndIncrement();
```
* **Concept**: Standard `long count++` is not thread-safe (read, modify, write). `AtomicLong` uses CPU-level **CAS (Compare-And-Swap)** instructions to increment IDs safely without heavy mutex locks.

### C. Thread-Safe Storage (`ConcurrentHashMap`)
```java
private final Map<Long, SeatAssignment> assignments = new ConcurrentHashMap<>();
```
* **Concept**: Regular `HashMap` throws `ConcurrentModificationException` or corrupts data under concurrent reads/writes. `ConcurrentHashMap` uses bucket-level locking and lock-free reads.

### D. Defensive Lock Management (`try-finally`)
```java
ReentrantLock lock = lockFor(orgId);
lock.lock();
try {
    // Critical Section: modify seat status & update org capacity
} finally {
    lock.unlock(); // Always unlocks even if exceptions occur!
}
```
* **Concept**: Ensures `lock.unlock()` executes regardless of runtime exceptions, preventing permanent deadlocks.

### E. Method-Level `synchronized` vs Lock Striping
```java
public synchronized SeatAssignmentResponse assignSeat(...)
```
* **Concept**: `synchronized` locks the entire service instance (`this`), acting as a global bottleneck across all organizations. Replacing it with per-org `ReentrantLock` improves multi-tenant concurrency.

### F. Race Condition Testing Utilities
1. **`CyclicBarrier(N)`**: Forces $N$ parallel threads to wait until all are created, then releases them simultaneously to simulate an exact stampede race condition.
2. **`CopyOnWriteArrayList`**: Thread-safe list implementation used by test threads to store granted responses without list index collisions.
3. **`thread.join(timeout)`**: Main thread waits for background worker threads to complete execution before running test assertions.



# from chat

 ──────
  ### 1. Fine-Grained Lock Striping (Per-Organization Locking)

  📍 Where it's used: LicenseService.java

    private final Map<Long, ReentrantLock> locks = new ConcurrentHashMap<>();
    
    private ReentrantLock lockFor(long orgId) {
        return locks.computeIfAbsent(orgId, key -> new ReentrantLock());
    }
    
  • The Problem: If you lock the entire LicenseService class (e.g., using synchronized), then 1,000 users requesting seats in Org 1 will block a user requesting a seat in Org 2. That's a huge performance
  bottleneck.
  • The Solution (Lock Striping): Partition locks by orgId.
      • Operations on Org 1 lock lockFor(1).
      • Operations on Org 2 lock lockFor(2).
      • Now, Org 1 and Org 2 can execute concurrently in parallel on multi-core CPUs without blocking each other!
  • Key Method — computeIfAbsent(): Atomically creates a new ReentrantLock for an orgId if one doesn't exist yet, preventing race conditions during lock creation.
  ──────
  ### 2. Lock-Free Atomic Counters (AtomicLong)

  📍 Where it's used: LicenseService.java

    private final AtomicLong nextOrgId = new AtomicLong(1);
    private final AtomicLong nextAssignmentId = new AtomicLong(1);
    
    // Generating unique IDs:
    nextAssignmentId.getAndIncrement();
    
  • The Problem: A standard long count = 0; count++; is not thread-safe. Under the hood, count++ does 3 operations: (1) read value, (2) add 1, (3) write back. If 2 threads run this simultaneously, both might
  read 1 and both write 2, skipping an ID!
  • The Solution: AtomicLong uses low-level hardware instructions called CAS (Compare-And-Swap). It increments the counter atomically without needing heavy lock overhead.
  ──────
  ### 3. Thread-Safe In-Memory Storage (ConcurrentHashMap)

  📍 Where it's used: InMemoryOrgRepository.java & InMemorySeatAssignmentRepository.java

    private final Map<Long, SeatAssignment> assignments = new ConcurrentHashMap<>();
    
  • The Problem: A regular Java HashMap is not thread-safe. If multiple threads call .put() or iterate over a HashMap concurrently, it can cause corrupted bucket pointers, missing updates, or throw
  ConcurrentModificationException.
  • The Solution: ConcurrentHashMap allows concurrent reads without locking and uses bucket-level locking for writes.
  ──────
  ### 4. Defensive Lock Cleanup (try-finally Block)

  📍 Where it's used: LicenseService.java

    ReentrantLock lock = lockFor(orgId);
    lock.lock();
    try {
        // Critical Section: modify seat status & update org capacity
    } finally {
        lock.unlock();
    }
    
  • Why finally is critical: If an exception is thrown inside the try block (e.g., database failure or unexpected runtime error), the finally block guarantees that lock.unlock() will be called. Without finally,
  an unhandled exception would leave the lock acquired forever, deadlocking that organization indefinitely!
  ──────
  ### 5. Method-Level Synchronization (synchronized)

  📍 Where it's used: LicenseService.java

    public synchronized SeatAssignmentResponse assignSeat(long orgId, long userId, long now)
    
  • How it works: The synchronized keyword locks the entire LicenseService instance (this) during the assignSeat method execution.
  • Refactoring Opportunity: Notice how reclaimSeat and autoReclaim use per-organization ReentrantLock lockFor(orgId), while assignSeat uses synchronized! In a production refactor, replacing synchronized in
  assignSeat with ReentrantLock lock = lockFor(orgId); would improve multi-tenant throughput by allowing different organizations to assign seats simultaneously.
  ──────
  ### 6. Advanced Concurrency Testing Tools (Simulating Race Conditions)
  📍 Where it's used: LicenseServiceTest.java

  Testing concurrent code is notoriously difficult because thread timing is unpredictable. The test suite uses two smart Java concurrency utilities to simulate stampede race conditions:

  #### A. CyclicBarrier (Simulating Simultaneous Requests)

    CyclicBarrier barrier = new CyclicBarrier(40);
    
    // In each of the 40 threads:
    barrier.await(); // Blocks until all 40 threads reach this line
    service.assignSeat(orgId, userId, 1); // ALL 40 threads fire AT THE EXACT SAME MILLISECOND!
    
  • Why it's used: Without CyclicBarrier, threads created in a for loop will start sequentially one after another. CyclicBarrier acts as a starting gate: it holds back all 40 threads until every single one is
  ready, then releases them simultaneously to force race conditions!
  #### B. CopyOnWriteArrayList (Thread-Safe Test Results Collector)

    List<SeatAssignmentResponse> granted = new CopyOnWriteArrayList<>();
    
  • Why it's used: Multiple worker threads add their granted seat responses to this list. CopyOnWriteArrayList makes thread-safe additions without throwing data corruption or indexing errors.
  #### C. thread.join(5000) (Thread Completion Wait)

    for (Thread thread : threads) {
        thread.join(5000);
    }
    
  • Why it's used: Instructs the main JUnit test runner thread to pause and wait until all 40 background threads finish running before checking assertions (assertEquals).
  ──────
  ### Concurrency Summary Cheat Sheet

   Concept                                                             | Class / Primitive                                                  | Purpose in this Repo
  ---------------------------------------------------------------------|--------------------------------------------------------------------|--------------------------------------------------------------------
   Lock Striping                                                       | Map<Long, ReentrantLock>                                           | Per-org isolation (Org 1 locked separately from Org 2)
   Atomic Operations                                                   | AtomicLong                                                         | Lock-free unique ID generation (nextAssignmentId)
   Thread-Safe Map                                                     | ConcurrentHashMap                                                  | Prevents data corruption during concurrent reads/writes
   Defensive Unlocking                                                 | lock.lock() + try/finally                                          | Prevents permanent deadlocks on unexpected errors
   Race Test Barrier                                                   | CyclicBarrier                                                      | Holds 40 test threads until they can all fire simultaneously