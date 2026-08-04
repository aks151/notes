# Flash Sale Inventory System: Concurrency & Fine-Grained Locking Notes

---

## 1. Test Case Analysis: `concurrentBuyersLimitedStock`

### Test Objective
Validates **thread-safety** and **overselling prevention** when high-concurrency requests hit a limited inventory concurrently.

### Scenario
- **Stock Available**: 40 items (`SKU_A`)
- **Concurrent Buyers**: 100 threads
- **Synchronization**: `CyclicBarrier(100)` forces all 100 worker threads to await and fire requests at the exact same millisecond (**Thundering Herd** simulation).

### Why Un-synchronized Code Fails (`expected: <40> but was: <45>`)
When 100 threads hit `purchase()` simultaneously without synchronization:
1. Thread A & Thread B both read `available = 1` before either writes the updated count.
2. Both evaluate `if (quantity > available)` -> `false`.
3. Both subtract stock and save `available = 0`.
4. **Result**: Both purchases succeed. Over 100 threads, 45 buyers succeed instead of strictly capping at 40.

---

## 2. Concurrency Strategies: Coarse-Grained vs. Fine-Grained

### A. Coarse-Grained Lock (`synchronized` Method)
- **Mechanism**: Marking `public synchronized PurchaseResponse purchase(...)`.
- **Pros**: Simple, completely thread-safe for in-memory services.
- **Cons**: Creates a **global bottleneck**. A buyer for Product A blocks buyers for Product B or unrelated sales.

---

### B. Fine-Grained Keyed Lock (Lock per SKU/Sale)
- **Mechanism**: Use a `ConcurrentHashMap` of `ReentrantLock` instances keyed by `"saleId:skuId"`.
- **Pros**: High throughput. Purchases for `SKU_A` do NOT block purchases for `SKU_B`.

```java
package com.gronex.flashsale.service;

import com.gronex.flashsale.dto.InventoryResponse;
import com.gronex.flashsale.dto.PurchaseResponse;
import com.gronex.flashsale.exception.AppException;
import com.gronex.flashsale.exception.ErrorCode;
import com.gronex.flashsale.model.FlashSale;
import com.gronex.flashsale.model.Purchase;
import com.gronex.flashsale.model.PurchaseStatus;
import com.gronex.flashsale.model.SaleInventory;
import com.gronex.flashsale.repository.FlashSaleRepository;
import com.gronex.flashsale.repository.PurchaseRepository;
import com.gronex.flashsale.repository.SaleInventoryRepository;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.locks.ReentrantLock;

public class FlashSalePurchaseService {
    private final FlashSaleRepository flashSaleRepository;
    private final SaleInventoryRepository saleInventoryRepository;
    private final PurchaseRepository purchaseRepository;
    private final AtomicLong nextPurchaseId = new AtomicLong(1);
    private final ConcurrentHashMap<String, ReentrantLock> skuLocks = new ConcurrentHashMap<>();

    public FlashSalePurchaseService(
            FlashSaleRepository flashSaleRepository,
            SaleInventoryRepository saleInventoryRepository,
            PurchaseRepository purchaseRepository
    ) {
        this.flashSaleRepository = flashSaleRepository;
        this.saleInventoryRepository = saleInventoryRepository;
        this.purchaseRepository = purchaseRepository;
    }

    private ReentrantLock getLock(long saleId, long skuId) {
        String key = saleId + ":" + skuId;
        return skuLocks.computeIfAbsent(key, k -> new ReentrantLock());
    }

    private PurchaseResponse toResponse(Purchase purchase) {
        return new PurchaseResponse(
                purchase.getPurchaseId(),
                purchase.getSaleId(),
                purchase.getUserId(),
                purchase.getSkuId(),
                purchase.getQuantity(),
                purchase.getIdempotencyKey(),
                purchase.getStatus(),
                purchase.getCreatedAt()
        );
    }

    private InventoryResponse toResponse(SaleInventory inventory) {
        return new InventoryResponse(
                inventory.getSaleId(),
                inventory.getSkuId(),
                inventory.getAvailableQuantity(),
                inventory.getVersion()
        );
    }

    public FlashSale createSale(FlashSale sale) {
        return flashSaleRepository.save(sale);
    }

    public InventoryResponse addInventory(long saleId, long skuId, int quantity) {
        if (flashSaleRepository.findById(saleId).isEmpty()) {
            throw new AppException(ErrorCode.SALE_NOT_FOUND);
        }
        if (quantity <= 0) {
            throw new AppException(ErrorCode.INVALID_QUANTITY);
        }

        ReentrantLock lock = getLock(saleId, skuId);
        lock.lock();
        try {
            Optional<SaleInventory> existing = saleInventoryRepository.findBySaleAndSku(saleId, skuId);
            SaleInventory inventory;
            if (existing.isEmpty()) {
                inventory = new SaleInventory(saleId, skuId, quantity, 1);
            } else {
                inventory = existing.get();
                inventory.setAvailableQuantity(inventory.getAvailableQuantity() + quantity);
                inventory.setVersion(inventory.getVersion() + 1);
            }
            saleInventoryRepository.save(inventory);
            return toResponse(inventory);
        } finally {
            lock.unlock();
        }
    }

    public PurchaseResponse purchase(
            long saleId,
            long userId,
            long skuId,
            int quantity,
            String idempotencyKey,
            long now
    ) {
        if (quantity <= 0) {
            throw new AppException(ErrorCode.INVALID_QUANTITY);
        }

        if (idempotencyKey != null && !idempotencyKey.isBlank()) {
            Optional<Purchase> existing = purchaseRepository.findByIdempotencyKey(idempotencyKey);
            if (existing.isPresent()) {
                return toResponse(existing.get());
            }
        }

        FlashSale sale = flashSaleRepository.findById(saleId)
                .orElseThrow(() -> new AppException(ErrorCode.SALE_NOT_FOUND));

        if (!sale.isActive()) throw new AppException(ErrorCode.SALE_INACTIVE);
        if (now < sale.getStartsAt()) throw new AppException(ErrorCode.SALE_NOT_STARTED);
        if (now >= sale.getEndsAt()) throw new AppException(ErrorCode.SALE_ENDED);

        ReentrantLock lock = getLock(saleId, skuId);
        lock.lock();

        try {
            SaleInventory inventory = saleInventoryRepository.findBySaleAndSku(saleId, skuId)
                    .orElseThrow(() -> new AppException(ErrorCode.INVENTORY_NOT_FOUND));

            int available = inventory.getAvailableQuantity();

            if (quantity > available) {
                throw new AppException(ErrorCode.INSUFFICIENT_STOCK);
            }

            inventory.setAvailableQuantity(available - quantity);
            inventory.setVersion(inventory.getVersion() + 1);
            saleInventoryRepository.save(inventory);

            Purchase purchase = new Purchase(
                    nextPurchaseId.getAndIncrement(),
                    saleId,
                    userId,
                    skuId,
                    quantity,
                    idempotencyKey,
                    PurchaseStatus.COMPLETED,
                    now
            );
            purchaseRepository.save(purchase);
            return toResponse(purchase);
        } finally {
            lock.unlock();
        }
    }

    public PurchaseResponse cancelPurchase(long userId, long purchaseId) {
        Purchase purchase = purchaseRepository.findById(purchaseId)
                .orElseThrow(() -> new AppException(ErrorCode.PURCHASE_NOT_FOUND));

        if (purchase.getUserId() != userId) {
            throw new AppException(ErrorCode.PURCHASE_NOT_OWNED);
        }

        if (purchase.getStatus() == PurchaseStatus.CANCELLED) {
            throw new AppException(ErrorCode.PURCHASE_ALREADY_CANCELLED);
        }

        ReentrantLock lock = getLock(purchase.getSaleId(), purchase.getSkuId());
        lock.lock();
        try {
            SaleInventory inventory = saleInventoryRepository
                    .findBySaleAndSku(purchase.getSaleId(), purchase.getSkuId())
                    .orElseThrow(() -> new AppException(ErrorCode.INVENTORY_NOT_FOUND));

            inventory.setAvailableQuantity(inventory.getAvailableQuantity() + purchase.getQuantity());
            inventory.setVersion(inventory.getVersion() + 1);
            saleInventoryRepository.save(inventory);

            purchase.setStatus(PurchaseStatus.CANCELLED);
            purchaseRepository.save(purchase);
            return toResponse(purchase);
        } finally {
            lock.unlock();
        }
    }

    public InventoryResponse getInventory(long saleId, long skuId) {
        SaleInventory inventory = saleInventoryRepository.findBySaleAndSku(saleId, skuId)
                .orElseThrow(() -> new AppException(ErrorCode.INVENTORY_NOT_FOUND));
        return toResponse(inventory);
    }

    public List<PurchaseResponse> listPurchases(long userId) {
        List<Purchase> userPurchases = purchaseRepository.findByUserId(userId);
        List<PurchaseResponse> result = new ArrayList<>();
        userPurchases.stream()
                .sorted(Comparator.comparingLong(Purchase::getCreatedAt).reversed()
                        .thenComparing(Comparator.comparingLong(Purchase::getPurchaseId).reversed()))
                .forEach(purchase -> result.add(toResponse(purchase)));
        return result;
    }
}
```

---

### C. Optimistic Locking with Versioning (Database Level)
- **Mechanism**: Atomic SQL conditional updates using a `version` column (CAS - Compare And Swap).
- **Pros**: Completely lock-free at application layer. Relational database handles row atomicity.

```sql
UPDATE sale_inventory 
SET available_quantity = available_quantity - :qty, 
    version = version + 1
WHERE sale_id = :saleId 
  AND sku_id = :skuId 
  AND available_quantity >= :qty 
  AND version = :expectedVersion;
```

---

### D. Redis Atomic Decrement & Lua Scripting (Production Standard)
- **Mechanism**: Inventory held in Redis cache; decrements executed via Redis `DECRBY` or Lua script.
- **Pros**: Single-threaded Redis guarantees non-blocking atomic decrements up to 100k+ ops/sec.

```lua
-- Redis Lua Script for Flash Sale Purchase
local stock = tonumber(redis.call('get', KEYS[1]))
if stock and stock >= tonumber(ARGV[1]) then
    redis.call('decrby', KEYS[1], ARGV[1])
    return 1 -- Success
else
    return 0 -- Insufficient Stock
end
```

---

## 3. Concurrency Strategy Comparison Matrix

| Concurrency Model | Lock Granularity | Performance | Bottleneck Scope | Scaling Capability | Complexity | Best Used For |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`synchronized` Method** | Global (Entire Method) | 🔴 Low | Entire Application | Low | 🟢 Very Simple | Prototype / Small In-Memory unit tests |
| **`ReentrantLock` per SKU** | Keyed (SKU / Sale Level) | 🟡 Medium | Same SKU / Sale Only | Medium | 🟡 Moderate | In-memory services with high traffic across multiple SKUs |
| **DB Optimistic Lock (CAS)** | Row-Level (Version field) | 🟢 High | Same Database Row | High | 🟡 Moderate | Relational DBs handling atomic updates under low-to-medium contention |
| **Redis `DECRBY` / Lua Script** | Key-Level (Redis Key) | 🚀 Extreme | Distributed Key | Extreme (100k+ TPS) | 🔴 High | Real-world High-Scale Flash Sales (e.g., Amazon, Flipkart) |

---

## 4. Interview Follow-Up Questions & Architecture Deep Dive

### Question 1: Distributed Atomic Decrement Options & Trade-Offs
> *"The solution serializes each SKU behind an in-process lock. How would you achieve the same atomic decrement across many application servers — would you use a DB conditional UPDATE, Redis, or optimistic version checks, and what are the trade-offs?"*

When scaling horizontally across multiple JVM nodes, in-process `ReentrantLock` does not synchronize across servers. The three main distributed alternatives are:

#### 1. Database Conditional `UPDATE` (Pessimistic Row Update)
```sql
UPDATE sale_inventory 
SET available_quantity = available_quantity - :qty 
WHERE sale_id = :saleId AND sku_id = :skuId AND available_quantity >= :qty;
```
- **Trade-offs**:
  - 🟢 **Pros**: Guaranteed ACID compliance; zero extra infrastructure needed.
  - 🔴 **Cons**: High DB row-lock contention. Under a thundering herd, incoming requests queue at the DB layer, exhausting database connection pools.

#### 2. Redis Atomic Decrement (`DECRBY` / Lua Script)
```lua
local stock = tonumber(redis.call('get', KEYS[1]))
if stock and stock >= tonumber(ARGV[1]) then
    redis.call('decrby', KEYS[1], ARGV[1])
    return 1 -- Success
end
return 0 -- Insufficient stock
```
- **Trade-offs**:
  - 🟢 **Pros**: Blazing fast (100k+ TPS); Redis is single-threaded, guaranteeing atomic execution without row locks.
  - 🔴 **Cons**: Cache volatility risk (requires Redis Persistence / Sentinel / Cluster); requires asynchronous sync back to SQL DB for persistent storage.

#### 3. Optimistic Locking with Version Field (CAS)
```sql
UPDATE sale_inventory 
SET available_quantity = available_quantity - :qty, version = version + 1
WHERE sale_id = :saleId AND sku_id = :skuId AND version = :expectedVersion;
```
- **Trade-offs**:
  - 🟢 **Pros**: Non-blocking reads; great for low-to-medium contention.
  - 🔴 **Cons**: Under high contention (e.g., 10,000 requests racing for 40 items), 99.6% of requests fail on version mismatch, causing massive retry storms.

**Recommendation for Interview**: **Redis Lua Script** at the API gateway layer for stock reservation + Async queue to persist to DB.

---

### Question 2: High-Throughput Scaling Beyond Coarse Locks
> *"Under 100 buyers racing for 40 units, coarse per-SKU locking can become a bottleneck. What techniques (sharded counters, atomic compare-and-set, queue-based admission) would you use to raise throughput while still never overselling?"*

1. **Sharded Inventory Counters (Partitioning)**:
   - Instead of 1 single counter for `SKU_A = 40`, divide stock into N shards (e.g., 4 shards of 10 items each: `sku_1001_shard_1` to `shard_4`).
   - Route buyers via `hash(userId) % 4`. Concurrency contention drops by 4x. If a shard runs out, spill over to another active shard.

2. **Edge Rate Limiting & Fast-Fail Counter**:
   - Maintain an atomic counter in Redis. Once it hits 0, reject all subsequent incoming requests at the API Gateway in O(1) time before they reach downstream services or databases.

3. **Queue-Based Admission Control (Virtual Waiting Room)**:
   - Buffer incoming buyer requests in a high-throughput queue (Kafka / RabbitMQ / Redis Stream).
   - Worker pools consume messages at a controlled rate (Token Bucket rate), turning unpredictable traffic spikes into a smooth, predictable processing curve.

---

### Question 3: Double-Checked Idempotency & Key Expiration
> *"Idempotency is resolved both before and inside the lock here. Why is the double check necessary, and how would you make idempotency keys durable and expire them safely?"*

#### Why Double-Checking is Necessary (Double-Checked Locking Pattern)
- **First Check (Outside Lock)**: Fast-path execution for retry requests. It returns cached purchase responses immediately without taking lock overhead.
- **Second Check (Inside Lock)**: Handles the **race condition** where two identical requests with the *same idempotency key* arrive simultaneously. Both pass the 1st check before the lock is acquired. The 2nd check inside the lock ensures the 2nd request is blocked from executing a duplicate purchase.

#### Durability & Expiration Strategy
- **Storage**: Store idempotency records in a distributed cache (Redis) or database table with a `UNIQUE INDEX (idempotency_key)`.
- **Expiration**: Set a TTL (e.g., 24–72 hours) using Redis `SET key value NX EX 86400` or a SQL scheduled cleanup job to prevent memory from growing indefinitely.

---

### Question 4: Abandoned Checkouts, Payment Failures & Reservation TTL
> *"How would you handle abandoned checkouts and payment failures — should stock be held with a reservation TTL and released automatically, and how does that interact with the cancel/restock path?"*

#### Two-Phase Reservation Pattern
1. **Phase 1: Reserve Stock with TTL (Temporary Hold)**
   - When a user clicks "Checkout", decrement available stock and increment `reserved_stock`.
   - Create a reservation record with `status = PENDING_PAYMENT` and `expires_at = now + 15 minutes`.
2. **Phase 2: Payment Confirmation**
   - Upon payment webhook success, transition status from `PENDING_PAYMENT` -> `COMPLETED`.
3. **Phase 3: Expiration & Auto-Release (Abandoned Checkouts / Payment Failures)**
   - If payment fails or TTL expires (15 min), a background worker or Redis Keyspace Expiration event (`notify-keyspace-events`) triggers an auto-release:
     ```sql
     UPDATE sale_inventory 
     SET available_quantity = available_quantity + :reservedQty 
     WHERE sale_id = :saleId AND sku_id = :skuId;
     ```
   - Transition status to `EXPIRED`.

#### Interaction with Manual Cancel Path
- **Auto-Release (`EXPIRED`)**: Operates on `PENDING_PAYMENT` reservations that timed out or failed payment.
- **Manual Cancel (`CANCELLED`)**: Operates on `COMPLETED` purchases cancelled by the user.
- **State Machine Guard**: Strict status transitions (`PENDING_PAYMENT` -> `EXPIRED` and `COMPLETED` -> `CANCELLED`) prevent double-restocking bugs.