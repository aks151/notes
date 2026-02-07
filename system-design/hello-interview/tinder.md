# Tindr
- They dont mention the schema, they first start talking about features and what their query would look like hmmm
- partitions in cassandra is starting to cofuse me
- 12:42Pm, understood some basic setup of the question, will try to wind it up by 4pm, summary, then branistorm about deep dives and then some final notes and onto next question 
- one imp thing here is which Gemini was not sor right about, the GET /feed enpoint, we dont need pagination here, whenever we need a new feed we can just call the endpoint "You might be tempted to proactively consider pagination for the feed endpoint. This is actually superfluous for Tinder b/c we're really generating recommendations. Rather than "paging", the app can just hit the endpoint again for more recommendations if the current list is exhausted."
- GET /feed?lat={}&long={}&distance={} -> User[]
  
## Summary
- Before FR, the scope of this discussion is limited to the recommendation feature and swipping feature mostly
- FR have the important ones, create account with preferences and distance, 2. show feed according to preference, swipe, get notifications if they mutually swipe on each other ..... missing 
- NFR has one very imp thing - consistency for the matches if both users have swipped yes, they should be notified for sure, low latency feed, handle huge number of users and concurrent users(20M daily users) and 100 swipe per user per day average, avoid showing previous No swipped accounts
- HLD - for creating the profile we can have a simple client-server-database setup where we will call the post /profile with the details and then persisit it in our db
- for showing the reccomendations feed, the very first version can be we just do s select * from users where age in AND lat, long in and interested in sort of a query, this is a very inefficient query we will come back to it in our deep dives
- for the swipes, we will persist all the swipe data and suppose user A has already swipped on user B, and then user B also swipes on user A, we will check for every swipe, if the other user has already swipped on the current user(user B in our case right now), we will show the matched graphic to user B on their client and send a push notification to user A(using a third party for push notifications always, APN or FCM)
- for the swipes discussion i got diverted from swipes to the notification part, in swipes we will store the swipes, will prupose having a separate db(cassandra is a good option), as it is extremely right heavy and both the dbs can scale independently
- for push notifications the external things have been discussed already
  


## Deep Dives
- ### Consistent and low latency swapping
    - this problem taught me about thinking about the failure case, here suppose both the users swipped yes on each other at similar time, this is where things can get problematic, none of them will be notified and an opportunity of finding love is lost.
    - the easy way here is to think about a consolidating service which will check for users who have mutually swipped on each other, and then notify them but chances are interviewer will be interested in the other case
    - there are few solutions to these which will have to be read
- ### Low latency for feed stack generation
- ### Avoid showing the No swipped users
  
  