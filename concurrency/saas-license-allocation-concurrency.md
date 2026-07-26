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
