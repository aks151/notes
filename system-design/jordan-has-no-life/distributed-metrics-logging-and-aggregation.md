# Distributed Logging and Metrics Aggregation

## Overview
- **Data Types:** Handles structured data, metrics, and unstructured data.
- **Scalability:** Designed to receive massive volumes of data from horizontally scaled servers across diverse origins.
- **Data Categories:**
  - Windowed data
  - Text logs
  - Structured / enrichable data
  - Unstructured data

## Generalized Data Sink
- **Broker Pattern:** Publishing directly to a server is risky as high volume can take it down. Instead, dump data into an intermediary like **Kafka**.
- **Kafka:** A log-based broker where messages are durable and persistent.
- **Stateful Consumption:** Enables the use of **Flink** for processing.
- **Flink Benefits:**
  - Ensures at-least-once processing.
  - Facilitates data enrichment by caching auxiliary data.

## Data Aggregation (Flink Consumer)
The primary step in the Flink consumer involves windowing strategies:
- **Tumbling Window** - Fixed Size window
- **Hopping Window** - Joins two tumbling window
- **Sliding Window** - keeps sliding xD 
*Note: Flink is for processing; data should not be stored there permanently.*

## Storage Strategies

### Textual Logs
- Should be stored in a **distributed search index** using an **inverted index** for efficient searching.

### Structured Data
- Schema is known.
- **Optimizations:**
  - Use encoding buffers like **Protocol Buffers (protobuf)**, **Thrift**, or **Avro**.
  - Reduces size significantly by skipping attribute strings and using binary formats.

### Unstructured Data
- Used when the structure is unknown (e.g., varying API responses).
- Typically stored in **JSON**.
- **Pipeline:** `Publisher -> Kafka -> Flink -> Hadoop -> Spark Job`.
- Spark jobs are used for complex transformations.

## Analytics Data
- **Column-Oriented DBs:** Traditional OLTP databases are row-oriented. Analytics frequently require scanning specific columns (e.g., all emails signed up in a timeframe) rather than full row objects.
- **Parquet Files:** 
  - Column-oriented format with heavy compression/encoding.
  - Stores metadata (like ID ranges) for each chunk.
- **Storage Options for Parquet:**
  - **S3:** Requires loading over the network, but modern systems are often compute-bound rather than network-bound.
  - **Hadoop:** More expensive, but queries can be run directly on the storage layer.
- Parquet is excellent for generalizable queries and is inherently partitioned by time.

## Data Warehousing
- Use for partitioning on fields other than time.
- **Platforms:** Snowflake, Google BigQuery, Amazon Redshift.

## Stream Enrichment
- **Example:** Enriching user click data with a user profile table using `userId`.
- **Performance:** Reading from a database for every event is too slow.
- **Solution:** Cache the enrichment data in Flink.
  - **Small Tables:** Cache the entire table in memory.
  - **Large Tables:** Partition Flink indexes based on a specific key.

## Key Comparisons
- **Flink vs. Spark Streaming:** Spark Streaming batches data, while Flink processes data as a continuous stream (low latency). Both can act as stateful consumers.
- **Data Warehouse:** Essential for partitioning and querying across dimensions beyond arrival time.
