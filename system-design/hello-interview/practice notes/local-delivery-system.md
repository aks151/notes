# local delivery system practice notes (14Feb)
## NFR
- ### my first version 
  - consistent ordering, low latency loading and ordering, scale handling 
- ### improvements
  - did not mention degree of consistency for ordering, should have been strong consistent instead of consistent
  - specificity was missing for low latency, search wasn't mentioned, but it should have been(<100ms)
  - eventual consistent for search

## Core Entities
- The points to take care is that there will be an ITEM(what all is there to order, this is what matters to users) and there will also be an INVENTORY(physical instance of an item in a DC, which will tell users what all are there to order)
