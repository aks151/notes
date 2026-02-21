# Local Delivery Service

## FR
- should be able to query availability of items, deliverable in 1 hour, by location
- should be able to order multiple items at the same time
-              out of scope
- billing
- driver routing and deliveries
- search functionality and catalogue apis
- cancellations and returns

## NFR
- availability queries should be fast(< 100ms) to support use cases like search
- ordering should be strongly consistent
- catalogs should be available (> consistent)
- should be able to handle 10k DCs and 100k items in the catalogue
- order volume ~ 10m orders/day
-              out of scope
- privacy and security
- disaster management

## Core Entities
- Items
- Inventory
- Order
- Distribution Centre

## HLD
- ### check inventory
  - user makes a request to check inventory for item A, B, C by passing the items and the lat long of his location to the availability service
  - the availability service fires the nearby service to get the list of nearby servicable DCs for the user
  - with the list of DCs in hand we can search for the inventory for the required items
  - we sum up the results and return it to our client
- ### order items
  - consistent orders - all the reads should serve the most recent writes or error
  - should be strictly consistent, no double bookings should happen
  - how to avoid double booking?? lock rows when the items are read, basically the contention concpets, first bring in transactions, then the lock row concpets, then the different isolation levels comes into talks, lets see what is here.
  - put orders and inventory in the same db and then take advantage of the ACID properties of postgresql and use isolation level serializable so that the whole transaction becomes atomic. ie two users try to order the same item at the same time, one of it will be rejected.