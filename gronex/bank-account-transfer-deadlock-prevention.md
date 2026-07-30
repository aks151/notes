# Bank Account Transfer & Deadlock Prevention System Notes

This note captures core domain rules, concurrency patterns, deadlock prevention strategies, and multi-threaded test scenarios for the Bank Account Transfer system.

---

## Part 1: Domain & Validation Rules
1. **Send and Receive Money:** Transfers must move funds from a source account to a destination account atomically.
2. **Positive Amount Transfers:** Transfers must be strictly positive ($> 0$). Zero or negative values are rejected (`INVALID_AMOUNT`).
3. **No Self Transfers:** Transferring money from an account to itself is prohibited (`SAME_ACCOUNT`).
4. **Account Validation:** Both source and destination accounts must exist (`ACCOUNT_NOT_FOUND`) and be active (`ACCOUNT_INACTIVE`).

---

## Part 2: Core Concurrency & Deadlock Prevention Concepts

1. **Circular Wait Deadlock Problem:**
   * **Scenario:** Thread 1 transfers from Account A $\rightarrow$ Account B (locks A, requests B). Simultaneously, Thread 2 transfers from Account B $\rightarrow$ Account A (locks B, requests A).
   * **Result:** Both threads freeze indefinitely waiting for each other to release their held lock.

2. **Lock Ordering / Resource Ordering Rule:**
   * **Solution:** Eliminate circular wait by acquiring locks in a globally deterministic order regardless of transfer direction.
   * **Mechanism:** Sort account IDs before locking (e.g., always lock `min(fromId, toId)` first, then `max(fromId, toId)`).

3. **Timed Lock Acquisition & Backoff (`tryLock`):**
   * Using Java's `ReentrantLock.tryLock(timeout, unit)` allows a thread to attempt lock acquisition with a timeout limit.
   * If the second lock cannot be acquired within the threshold, the thread releases the first lock and backs off safely, preventing thread starvation and indefinite hangs.

4. **Atomic Multi-Entity Transactions:**
   * Ensures balance **deduction** from the sender and **credit** to the receiver occur atomically. Money is conserved and never created or lost mid-transfer.

5. **Idempotent Retry Guards:**
   * Repeating a transfer with an already-processed idempotency key returns the original transfer response without applying duplicate balance deductions or credits.

---

## Part 3: Multi-Threaded Concurrency Scenarios

1. **200 Simultaneous Opposing Transfers ($A \rightarrow B$ & $B \rightarrow A$):**
   * Executes 100 threads for $A \rightarrow B$ and 100 threads for $B \rightarrow A$ concurrently using a `CountDownLatch` sync barrier.
   * **Goal:** Validates that strict lock ordering prevents circular wait deadlocks and completes cleanly.

2. **50 Concurrent Debits on a Single Account:**
   * 50 threads concurrently debit \$10 from an account starting with \$100.
   * **Goal:** Validates that check-then-act balance guards prevent overdrawing (negative balances) and race conditions, resulting in exactly 10 successful transfers and \$0 remaining balance.

3. **Total Balance Conservation & Invariant Guarantee:**
   * 200 random transfers execute concurrently across 5 different accounts.
   * **Goal:** Validates that the sum of balances across all accounts after concurrent execution remains strictly equal to the initial sum before transfers, proving system invariant safety.

4. **Bounded Thread Termination:**
   * Spawns 120 concurrent transfer threads across cyclic accounts.
   * **Goal:** Asserts that all threads terminate cleanly within a bounded `join(timeout)` window, proving no threads hang indefinitely due to deadlock or starvation.
