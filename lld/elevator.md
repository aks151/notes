# Elevator

## Requirements
- Lift and Floor Counts
- How to call an elevator? up/down button or floor selection
- How to select destination? Are multiple destinations allowed?
- Invalid floor's error handling?
- How are we distinguishing between diffn destinations
- Step Funcn vs Model control s/w that talks to some h/w
### Out of scope
- Weight and capacity mgmnt
- Emergency stop
- Door open/close mechanics
- Dynamic floor/elevator config
- UI/rendering layer


## Entities
- Floor: just numbers so not an entity
- Request: just a floor number or a whole class?
- Elevator: surely a class
- ElevatorController: Orchestrator surely neede


## Classes
- ElevatorController: receives hall calls, decides which elevator should handle each request, coordinates overall system
- Elevator: maintains current floor, direction, queue of requests. knows how to execute movement behaviour, move one floor at a time, stop when needed, reverse when there are no more stops ahead, no idea about other elevators
- Request: represents the stop an elevator needs to make,  will be decided later if it would be a class or not 


## Class Designs
- ```code
    class ElevatorController
    -elevators:list<Elevator>
    +


