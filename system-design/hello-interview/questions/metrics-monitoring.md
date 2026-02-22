# Metrics Monitoring
## Core Concepts
- **Metric**: Named measurement
- **Labels**: Key-value pairs attached to the metric to see where they came from
- **Series**: Unique combination of metrics name + labels tracked over time

## Metric Ingestion
- main aim is to not let 5M metrics/sec translate into 5M writes/sec