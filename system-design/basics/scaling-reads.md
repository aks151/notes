# Scaling Reads

## Three Major Ways
- Optimizing DB(read performance within db).
- Horizontal Scaling.
- Adding external caching.


## Optimizing DB
- ### Indexing: 
  B-Tree index(genral querries), Hash Index(Exact Matches), Specialized Index(Full text search or geographic index). Add indexes to the the coulumn that you frequently query, join on, or sort by.
- ### Hardware Upgrade
- ### Denormalization Strategies: 
    optimizing for reads in expense of writes

## Horizontal Scaling the db
 when you exceed 50,000-100,000 read requests per second (assuming you already have proper indexing).
- ### Read Replicas: 
- ### Database Sharding
   - Functional Sharding
   - Geographical Sharding
  
  Caching is a more effective way than sharding, sharding is primarily a write scaling technique.

## Add external caching layer
  after optimizing your database if we still need more read performance, two main options - add read replicas (as discussed above) or add caching.

  - Application Level Caching 
  - CDN and Edge Caching

## Corner Cases/Deep Dives
  - "What happens when your queries start taking longer as your dataset grows?"
  - "How do you handle millions of concurrent reads for the same cached data?"
       - Request Coalescing
       - Cache Key Fanout
  - "What happens when multiple requests try to rebuild an expired cache entry simultaneously?" (Cache Stampede)
        - Distributed Locks
        - Probabilistic Early Refresh
  - "How do you handle cache invalidation when data updates need to be immediately visible?"
      lots of talks here around nuances of various scenarios, cache versioning works well for single-entity caches like user profiles or product details, doesnt helps much with computed data like search results or feeds where invalidation is inherently more complex


 ## Summary
 - optimize within your database first with proper indexing and denormalization, then scale horizontally with read replicas, and finally add caching layers for ultimate performance. 
 - demonstrate that you understand both the performance benefits and the operational complexity of each approach

 ## Notes
 1. 01.02.26 - missed Denormalization Strategies for Optimizing Read Performance, Read Replicas for horizontal scaling, 

