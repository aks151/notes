# Bank Account Transfer & Deadlock Prevention System Notes

This note captures core domain rules, concurrency patterns, deadlock prevention strategies, multi-threaded test scenarios, and the final implementation lessons for the Bank Account Transfer system.

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

---

## Part 4: The Final Implementation & Critical Concurrency Lessons

### 1. The Overdrawing Bug Encountered (`expected: <10> but was: <18>`)
* **The Flaw:** `if (source.getBalance() < amount)` was executed **OUTSIDE** the lock guard.
* **Why it failed:** Under 50 concurrent threads, 18 threads executed the balance check simultaneously before any thread acquired the lock. All 18 saw `balance = 100` and passed the check. Then each thread acquired the lock one by one and deducted \$10 without re-checking the balance, overdrawing the account.
* **The Lesson:** **Condition checks (Check-Then-Act) MUST happen INSIDE the critical section.**

### 2. Final Correct Implementation (`BankTransferService.java`)

```java
public TransferResponse transfer(
        long fromAccountId,
        long toAccountId,
        long amount,
        String idempotencyKey) {

    // 1. Idempotency Guard Check
    if (idempotencyKey != null && !idempotencyKey.isBlank()) {
        Optional<Transfer> existing = transferRepository.findByIdempotencyKey(idempotencyKey);
        if (existing.isPresent()) {
            return toTransferResponse(existing.get());
        }
    }

    // 2. Domain Validations
    Account source = accountRepository.findById(fromAccountId).orElse(null);
    Account destination = accountRepository.findById(toAccountId).orElse(null);

    if (source == null || destination == null) {
        throw new AppException(ErrorCode.ACCOUNT_NOT_FOUND);
    }
    if (fromAccountId == toAccountId) {
        throw new AppException(ErrorCode.SAME_ACCOUNT);
    }
    if (!source.isActive() || !destination.isActive()) {
        throw new AppException(ErrorCode.ACCOUNT_INACTIVE);
    }
    if (amount <= 0) {
        throw new AppException(ErrorCode.INVALID_AMOUNT);
    }

    // 3. Lock Ordering (Prevents Deadlocks)
    long firstId = Math.min(fromAccountId, toAccountId);
    long secondId = Math.max(fromAccountId, toAccountId);

    ReentrantLock lock1 = lockFor(firstId);
    ReentrantLock lock2 = lockFor(secondId);

    // 4. Nested Atomic Lock Acquisition
    lock1.lock();
    try {
        lock2.lock();
        try {
            // 5. CHECK BALANCE INSIDE THE LOCK (Prevents Race Condition)
            if (source.getBalance() < amount) {
                throw new AppException(ErrorCode.INSUFFICIENT_FUNDS);
            }

            // 6. ATOMIC MUTATION (Deduct Sender & Credit Receiver)
            source.setBalance(source.getBalance() - amount);
            accountRepository.save(source);

            destination.setBalance(destination.getBalance() + amount);
            accountRepository.save(destination);
        } finally {
            lock2.unlock();
        }
    } finally {
        lock1.unlock();
    }

    // 7. Save Transfer Audit Record
    Transfer transfer = new Transfer(
            nextTransferId.getAndIncrement(),
            fromAccountId,
            toAccountId,
            amount,
            idempotencyKey,
            TransferStatus.COMPLETED,
            clock.now());
    transferRepository.save(transfer);
    return toTransferResponse(transfer);
}

// History lookup must check BOTH sender and receiver roles
public List<TransferResponse> listAccountTransfers(long accountId) {
    return transferRepository.findByAccountId(accountId).stream()
            .map(this::toTransferResponse)
            .toList();
}
```

---

### Summary of Key Engineering Takeaways

| Bug / Challenge | Failure Mode | Correct Architectural Pattern |
| :--- | :--- | :--- |
| **Check Outside Lock** | 18 threads overdraw account (`was: <18>`) | Check-Then-Act must be **inside** lock guard |
| **Arbitrary Lock Order** | Thread A ($A \rightarrow B$) & Thread B ($B \rightarrow A$) deadlock | Lock in sorted order (`Math.min` / `Math.max`) |
| **Sequential Un-nested Locks** | Money temporarily vanishes mid-flight | Hold **both** locks nested during balance mutation |
| **Account History Filtering** | Receiver accounts miss transaction history | Query `fromAccountId == id \|\| toAccountId == id` |
