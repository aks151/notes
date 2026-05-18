# AD Click Aggregator - Hello Interview

## Functional Requirements (FR)
- Click on ad and get redirected to advertiser's website.
- Advertisers can query ad click metrics over time, with a min granularity of 1 minute.

### Out of Scope FRs
- Ad targeting
- Ad serving
- Cross device tracking
- Integration with offline marketing channels

## Scale
- 10 M active ads
- Peak 10k clicks per second
- Avg 1k clicks per second
- 1k * 100k seconds in a day = 100M clicks per day

## Non-Functional Requirements (NFR)
1. **Scale:** Able to handle the scale of 10k clicks per second.
2. **Query Latency:** Low latency analytics query for advertisers.
3. **Reliability:** Fault tolerance and accurate data collection. We should not lose metrics.
4. **Timeliness:** As real-time as possible.
5. **Idempotency:** Idempotent click tracking; we should not count the same click multiple times.