# Cassandra
- distributed nosql database
- wide column store
- designed to handle massive amount of data across many distributed servers without any given single point of failure
- created at FB by co creator of Amazon Dynamo
- took inspiration from dynamo and G's bigQuerry
- to solve fb inbox messaging system.
- needed a db that could handle massive amount of write throughput for millions of users sending billions of msgs every day
-  needed to scale horizontally without mannual sharding
-  provide tons of availability in zero down time
-  super low latency reads and write globally.
-  Cassandra was designed to give up on flexibility in querying, and in exchange we get 
   -  highly scalable
   -  highly available
   -  fault tolerence


## How it organises data
-  Keyspace - like a database in postgres/mysql (holds the tables and defines some global settings like how data should be replicated along the cluster or how many copy of the data we should maintain, which data centre)
-  Table - defines the schema(flexible)
-  Row
-  

## Scalability talks
- Ranging from normal hashing funtion -> consistent hashing scheme -> no master slave architecture -> gossip protocol to have coordination -> which helps avoid a breaking failure like zookeeper outage -> CAP Theorum Talks where obvio we focus on availability over consistency as the three features of Cassandra is Highly Available, Highly Scalable and Fault Tolerent
- ### Some nuance which will be very good to bring up in interviews:
  - Cassandra doesn't forces you to pick one side, consistency or availability forever, it lets you tune it per query (ONE, QUORUM, ALL)

## Summary Till Here
- Partitioning and consistent hashing gives scalability
- Replication gives it the availability and fault tolerence
- Gossip and leaderless design keep the cluster decentralized
- tunable consistency lets you control how it balances correcness and uptime - per request