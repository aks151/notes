# API Design
## Notes for me (Mistakes i keep making)
1. No usage of verbs in the url (swipeLeft & swipeRight to swipe/ with type in the body)
2. Responses can be HTTP codes
3. Don't rely on client timestamps ever, they can trick you by changing the time, always generate timestamps in the backend
4. how to make something strong consistent -> make sure to return an acknowledgment response
5. Learn pagination and start adding it to your endpoints, stop being a naive
6. 