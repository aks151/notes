# Sharding
- The imp point to take care while selecting the shard key is, it should not create a hot spotttt
- hash based sharding is the most preffered answer, and then maybe range based sharding can be mentioned too, but directory based sharding is neverrrrr the answer
- strategies to steer clear from multi shard queries - denormalize to avoid this? Can I cache it? Can I precompute it with a background job?