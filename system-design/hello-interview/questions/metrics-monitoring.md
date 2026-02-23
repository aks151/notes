# Metrics Monitoring
## Core Concepts
- **Metric**: Named measurement
- **Labels**: Key-value pairs attached to the metric to see where they came from
- **Series**: Unique combination of metrics name + labels tracked over time

## Metric Ingestion
- main aim is to not let 5M metrics/sec translate into 5M writes/sec

### 1. Simple Data Ingestion
- Assuming 500k servers and 100 metrics per 10 secs, it becomes 5M metrics/sec, which is a super heavy load.
- Arrangement: `servers -> ingestion service -> db`.
- Horizontally scaling the ingestion service helps with ingestion load, but not the downstream storage bottleneck (still faces 5M writes/sec).
- Issues: No buffer if the DB slows down or goes offline; metrics are dropped. No backpressure, no durability, and no way to replay data after failure.

### 2. Decouple with a Message Queue
- Introduce Kafka between the ingestion service and storage.
- Arrangement: `servers -> ingestion sv -> kafka -> ingestion consumer -> storage`.
- The ingestion service validates metrics and publishes to a Kafka topic partitioned by metric name.
- Provides backpressure handling, durability, and parallelism.

### 3. Agent-based Collection with Local Buffering
- Run a small background process (collector/agent) on each server to gather metrics locally.
- Agent collects metrics at high frequency -> buffers and batches locally -> periodically flushes batches via Kafka to our ingestion service.
- Shifts work to the edge, reducing central load significantly (e.g., from 5M/sec to 50k/sec requests).
- Kafka buffers against spikes; if the ingestion service falls behind, it catches up via Kafka's retention.

## Query and Visualize Metrics

### 1. Storage Choice: Why not PostgreSQL?
- **Scale:** At 5M writes/sec, standard relational DBs like Postgres can't keep up.
- **Query Performance:** Dashboard queries can touch billions of data points that need to be scanned, filtered, and aggregated in under a second.
- **Degradation:** Performance degrades as data grows; a query that works for a week's timeframe might fail for a month's range.
- **Sharding Complexity:** Sharding often breaks cross-shard queries, making aggregations difficult.

### 2. Time-Series Databases (TSDB)
- **Features:** Append-only writes, columnar compression, and built-in rollups.
- **Examples:** InfluxDB, TimescaleDB, VictoriaMetrics.
- **Partitioning:** We'll partition by both **time** and **metric series**.
- **Retention & Rollups (Downsampling):**
    - Raw 10-second data: Kept for 15 days.
    - 1-minute rollups: Kept for 90 days.
    - 1-hour rollups: Kept for 1 year.

### 3. Query Service Architecture
- Sits in front of the storage layer to accept queries in a DSL (like PromQL).
- **Separation of Concerns:** Read paths have completely different characteristics than write paths.
    - **Writes:** Constant, predictable, high-volume, must never be dropped.
    - **Queries:** Sporadic, user-driven, and computationally expensive.
- **Benefits:**
    - Independent scaling and tuning for reads vs. writes.
    - Easy to add a caching layer (e.g., Redis) to the query service without complicating the ingestion path.

## Alerting

### 1. Approach: Polling vs. Streaming
- Candidates often jump to Flink or Spark for rule evaluation, but this is often **overkill**.
- If alerts must fire within ~1 minute, **simple polling** is a robust starting point.

### 2. Architecture: "Alerts as Scheduled Queries"
- **User Flow:** Users register rules with thresholds via an **Alerting API**, which stores them in a DB.
- **Evaluation:** An **Alert Evaluator service** periodically grabs these rules and fires off queries to the TSDB.
- **Trigger:** If a threshold is breached, the service emits an event to a notification system.

### 3. Why Polling?
- **Battle-Tested:** This is exactly how Prometheus Alertmanager works—evaluating rules on a fixed interval against the same storage serving dashboards.
- **Simplicity:** Thinking of "alerts as scheduled queries" makes the system significantly easier to reason about, test, and debug.

## API Design

### 1. Ingest Metrics
- **Endpoint:** `POST /metrics/ingest`
- **Payload:**
```json
{
    "metrics": [
        {
            "name": "cpu_usage",
            "labels": {"host": "server-1", "region": "us-east"},
            "value": 0.85,
            "timestamp": 1677000000
        }
    ]
}
```

### 2. Query Metrics
- **Endpoint:** `GET /metrics/query`
- **Params:** `query=avg(cpu_usage{region="us_east"})&start=A&end=B&step=60`
- **Response:** `{"timestamps": [...], "values": [...]}`

### 3. Register Alert Rules
- **Endpoint:** `POST /alerts/rules`
- **Payload:**
```json
{
    "name": "High CPU Alert",
    "query": "avg(cpu_usage{region='us-east'}) > 0.9",
    "notifications": ["slack:#oncall", "pagerduty:team-infra"]
}
```

## Notifications

### 1. Dedicated Notification Service
- **Risk:** Don't call Slack/PagerDuty APIs directly from the alert evaluator. External APIs can be fickle or slow; if they fail or time out, alerts might be dropped.
- **Goal:** Separation between *evaluating alert conditions* and *managing notifications* (similar to the Prometheus/Alertmanager pattern).

### 2. Handling "Alert Storms"
- **Scenario:** 100 servers in a cluster breach a CPU threshold simultaneously.
- **Problem:** Sending 100 separate PagerDuty pages is counterproductive and overwhelming for engineers.

### 3. Core Features of the Notification Service
- **Deduplication:** The alert evaluator runs frequently (e.g., every minute). Without deduplication, an engineer would be paged every minute for the same ongoing incident.
    - **Solution:** Track alert state (Firing vs. Resolved). Only notify on state transitions (e.g., when it first starts firing and when it is finally resolved).
- **Grouping:** Collect alerts within short time windows and group them by labels (e.g., `cluster` or `service`). Send one summarized notification per group instead of one per server.
- **Silencing:** Allow users to mute specific alerts during planned maintenance windows.
- **Escalation:** Re-notify through a different channel (e.g., call after a Slack message) if no one acknowledges the alert within a specific timeframe.

### 4. Why This Pattern?
- These are fundamentally different problems. Evaluating conditions is a data-processing task; managing notifications is a stateful, human-interaction task with different scaling and reliability characteristics.

## Deep Dives

### 1. How to serve low-latency dashboard queries over weeks of data?
**Challenge:** Scaling reads for heavy aggregations and long time-range scans while maintaining sub-second responses.

#### Approach A: Query Raw Data Directly (Poor Scalability)
- **Method:** Store metrics at full resolution (e.g., 10s intervals) and query the DB for every panel.
- **Example:** "Average CPU for all 1,000 production pods over the last 30 days."
- **The Problem:** 1,000 pods * 259,200 points/series (30 days) = ~259M rows to scan. At ~100 bytes/row, that's ~25GB of data for a *single* dashboard panel. This cannot be done in under a second.

#### Approach B: Pre-computed Rollups (The Standard Way)
- **Method:** Store data at multiple resolutions (Downsampling).
    - **Raw (10s):** Kept for 2 days.
    - **1-min:** Kept for 2 weeks.
    - **1-hour:** Kept for 90 days.
    - **1-day:** Kept for 2 years.
- **Query Engine Logic:** Automatically selects the appropriate resolution based on the requested time range. A 30-day query uses hourly rollups, reducing the scan volume by 360x compared to raw data.
- **Limitations:** Rollups are "lossy." You cannot recover raw 10s spikes from hourly averages. For percentiles (P99), you must store **histograms or sketches** at each rollup level.

#### Approach C: Caching Layer + Query Splitting (The Advanced Way)
- **1. Query Splitting:** Break a long query into chunks. Recent data (last 2 hours) hits the DB for freshness; historical data hits the cache.
- **2. Precomputation:** Identify popular dashboard queries and precompute them on a schedule, assigning a TTL aligned with data freshness requirements.
- **3. Result Caching:** Cache results using `query + time_range` as the key.
- **Outcome:** Dashboards that don't require real-time data can be served entirely from cache with sub-100ms latency.
- **Challenges:** Cache invalidation is tricky (e.g., handling data backfills) and memory management is required to prevent exhaustion.

### 2. Reduce alert latency below 1 minute
**Goal:** Transitioning from polling to real-time stream processing for mission-critical alerts.

#### Option A: Increase Polling Frequency
- **Method:** Reduce polling interval from 1 minute to 15 or 30 seconds.
- **Trade-off:** Simple to implement but increases load on the TSDB. At high scale, frequent alert queries start competing with dashboard queries for resources, potentially degrading performance for both.

#### Option B: Stream Processing for Real-Time Alerts
- **Method:** Use a stream processing engine like **Apache Flink** to evaluate rules against live data.
- **Architecture:** Metrics already flow through Kafka. Flink is added as a second consumer (parallel to the storage consumer).
- **Execution:** 
    - Flink reads metrics from Kafka.
    - For each metric series, Flink maintains a windowed state (e.g., 5-minute moving average).
    - Alert rules are compiled into Flink jobs.
    - When a threshold is violated in the stream, Flink immediately emits an alert event to the notification service.
- **Benefit:** Reduces latency to seconds (basically the time it takes to traverse the Kafka pipeline) and removes the evaluation load from the storage layer.

---
## Study Session History (Feb 22, 2026)
- **Ingestion Strategy:** Evolved from a simple server-DB push to a decoupled Kafka-based architecture, then further optimized with agent-based local batching/buffering to handle 5M metrics/sec.
- **Storage & Querying:** Analyzed PostgreSQL's limitations for high-write/high-scan workloads; moved to Time-Series Databases (TSDB) with retention policies and rollups (downsampling).
- **Query Service:** Established the need for a separate query service to decouple expensive read paths from critical write paths and enable easier caching.
- **Alerting Logic:** Adopted a polling-based "alerts as scheduled queries" model (Prometheus-style) over complex streaming engines for simplicity and reliability.
- **API Design:** Defined RESTful endpoints for metric ingestion, time-series querying, and alert rule registration.
- **Notification Management:** Integrated a dedicated notification service to handle real-world complexities like deduplication, grouping (alert storms), and state transitions.
- **Read Optimization Deep Dive:** Compared raw data queries vs. pre-computed rollups and advanced caching/query splitting to achieve sub-second dashboard latency for large time ranges.
- **Alert Latency Deep Dive:** Explored scaling polling frequency vs. implementing real-time stream processing (Flink) for sub-minute alert triggering.