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

