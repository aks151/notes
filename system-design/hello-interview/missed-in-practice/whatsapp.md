# Missed Parts - WhatsApp

## Non-Functional Requirements (NFR)
- **Guaranteed Message Delivery:** Ensure messages are durably stored and eventually delivered to recipients, even if they are offline (Data reliability and persistence).
- **Scalability Wordings:** Use more professional terminology; instead of "handle 1B users," use "be able to handle billions of users with high throughput."
- **Ephemeral Storage:** Messages should be stored on centralized servers for no longer than necessary.
- **Resilience:** The system should be resilient to failures of individual components.

### AI Feedback - NFR
> You're missing a critical requirement about message deliverability guarantees. While availability ensures the system is up and running, we also need to ensure that messages are durably stored and eventually delivered to recipients even if they're offline. This is about data reliability and persistence, not just system uptime.

## Core Entities
- **Clients:** Missed considering clients as a core entity.
- **Chats vs. Groups:** Better to use "Chats" as a generalized concept instead of specifically "Groups."
