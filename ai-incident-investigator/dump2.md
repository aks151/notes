w to go about developement in agentic era, like there should be something which will tell any…
See [AGENTS.md](AGENTS.md).

That file is the single source of agent instructions for this repository, so the
guidance cannot drift between tools. Do not add project instructions here.

⏺ Write(docs/PRODUCT.md)
Wrote 84 lines to docs/PRODUCT.md
# Product

## Problem

When a distributed system degrades, the evidence needed to explain it is scattered
across systems that do not talk to each other: metrics in one place, traces in another,
logs in a third, plus Kubernetes state, deployment history and source control.

An engineer on call spends the first twenty minutes of an incident doing clerical work
— pulling up five tabs, aligning timestamps by eye, and holding a mental model of what
… +74 lines

⏺ Write(docs/ARCHITECTURE.md)
Wrote 144 lines to docs/ARCHITECTURE.md
# Architecture

> Keep this file true. If the diagram and the code disagree, the diagram is the bug.
> Last verified against the code: **2026-08-02 (V0)**.

## Today (V0)

```
                    THE TESTBED
… +134 lines

⏺ Write(docs/ROADMAP.md)
Wrote 112 lines to docs/ROADMAP.md
# Roadmap

Six milestones. Each one is gated on the previous producing a *felt* need, not on a
calendar. The gates are the point — they are what keep the stack defensible.

| Milestone | Deliverable | Exit criteria |
|-----------|-------------|---------------|
| **V0** ✅ | Breakable testbed | 3 services + Postgres running, one trace spans all three, load harness produces a baseline |
| **V1** | Observability stack | Any V0 incident diagnosable from Grafana in under 5 minutes |
| **V2** | Incident catalogue | 9+ incidents reproducible by one command, each wi
… +102 lines

⏺ Write(docs/STATE.md)
Wrote 70 lines to docs/STATE.md
# Current state

> Short by design. Update it when a milestone moves, not on every commit — git already
> records commits. What git does *not* record is which incidents have been run and
> was learned from them, which is the expensive-to-rederive part.

**Updated:** 2026-08-02 · **Milestone:** V0 complete, V1 not started

## Where the project is
… +60 lines

⏺ Write(docs/DEVELOPMENT.md)
Wrote 143 lines to docs/DEVELOPMENT.md
# Development

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Go | 1.25+ | a transitive dependency raised the floor from 1.24 |
| Docker + Compose | v2 | Desktop is fine |
| k6 | — | not installed locally; runs via the `grafana/k6` image |
… +133 lines

Now wiring the README to the new docs, and flagging the background files as superseded:

⏺ Update(README.md)
Added 13 lines
The testbed comes first. You cannot evaluate whether an investigator produces useful
analysis or plausible nonsense until you can diagnose the incidents yourself.

## Documentation

| Document | Answers |
|----------|---------|
| [AGENTS.md](AGENTS.md) | how coding agents should work in this repo — **read f
| [docs/PRODUCT.md](docs/PRODUCT.md) | what we're building, and what we're deliberately not |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | how it works today and where it
| [docs/STATE.md](docs/STATE.md) | where the project actually is right now |
| [docs/ROADMAP.md](docs/ROADMAP.md) | the six milestones and their gates |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | building, running, every config knob |
| [docs/decisions/](docs/decisions/) | why it's built this way |
| [docs/incidents/](docs/incidents/) | the failure catalogue and postmortems |

## Current state: V0

```

⏺ Update(README.md)
Added 1 line
loadtest/k6/            load profiles
docs/decisions/         why each component exists
docs/incidents/         the incident catalogue and postmortems
docs/background/        original brainstorming — superseded, kept for provenanc
```

## Conventions

⏺ Write(docs/background/README.md)
Wrote 22 lines to docs/background/README.md
# Background — superseded source material

⚠️ **Do not treat anything in this directory as current.** These are the original
planning conversations that led to the project. They are kept for provenance, bec
the reasoning in them is worth re-reading, but several of their specifics were
overruled once building started.

Known contradictions with the actual system:

| These documents say | Reality | Where the real decision lives |
… +12 lines

Now the issue seed. Creating issues on your public repo is outward-facing, so I'm writing it as a script for you to run rather than firing it off:

⏺ Write(scripts/seed-issues.sh)
Wrote 212 lines to scripts/seed-issues.sh
#!/usr/bin/env bash
# Seeds GitHub milestones and issues for V1 and V2.
#
# Issues are the unit of work an agent is pointed at: "implement issue #8" is a fa
# better prompt than "continue the observability project". Each one below carries its
# own acceptance criteria so the agent does not have to invent requirements.
#
# Run once:  ./scripts/seed-issues.sh
# Requires:  gh auth login
… +202 lines

  Ran 1 shell command

Done. Everything verifies: gofmt/vet/test -race clean, stack still serving 201s.

What I built

AGENTS.md              ← entry point: map + the one hard prohibition
CLAUDE.md              → pointer to AGENTS.md (so they can't diverge)
docs/
  PRODUCT.md           what we're building; non-goals
  ARCHITECTURE.md      today vs target, with a "last verified" date
  STATE.md             where we actually are (~40 lines)
  ROADMAP.md           V0→V5 with gates
  DEVELOPMENT.md       every config knob, every command
  decisions/           3 ADRs (already existed)
  incidents/           catalogue + template
  background/          plan.md + tech-stack-decision.md, marked superseded
scripts/seed-issues.sh 14 issues across V1/V2, each with acceptance criteria

The project plan

Six milestones, each gated on the previous producing a felt need:

┌───────┬───────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────┐
│       │                Deliverable                │                                Gat                │
├───────┼───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ V0 ✅ │ Breakable testbed                         │ done — baseline 665 rps, p95 31.8m                │
├───────┼───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ V1    │ Collector + Prometheus/Tempo/Loki/Grafana │ diagnose incident 01 from Grafana ce code changes │
├───────┼───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ V2    │ 15 incidents, one command each            │ you can narrate every causal chain                │
├───────┼───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ V3    │ Deterministic evidence + timeline         │ correct timeline, verified by hand                │
├───────┼───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ V4    │ AI reasoner                               │ blocked until V2's exit criterion                 │
├───────┼───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ V5    │ 300-run benchmark                         │ a published accuracy number, inclus               │
└───────┴───────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────┘

The V1 gate is doing real work: if switching to OTLP requires touching Go code, ADR 0002 was wrong and the abstraction needs fixing before anything else proceeds.

On the agentic-context question

ChatGPT's core principle is right and worth adopting: the repo owns the context, the agent doesn't. AGENTS.md as a map rather than a database, non-goals to stop agents inventing requirements, ADRs so a
future agent knows why Postgres was chosen — all correct.

Three places I'd diverge, now reflected in what's on disk:

1. A stale doc is worse than none. ChatGPT's own template asserted Java/Spring services cision. I put docs/background/README.md in specifically to neutralise that: a table ofevery contradiction between the old planning docs and reality. Same reason ARCHITECTURE.md carries a "last verified" date.
2. STATE.md earns its place. ChatGPT said skip it, use git + issues. But git records codord which incidents you've run and what you learned — which is this project's expensivestate. Kept to ~40 lines, updated per milestone.
3. One prohibition no generic template contains. An agent that helpfully runs incident 0m has destroyed the project's entire purpose. That's now the loudest section of AGENTS.md, with a do/don't table, plus your own rule quoted verbatim: "AI may write more code than me, but I must understand more architecture than the AI writes for me."

Also fixed along the way: your Go module path was github.com/aks151boson/... but the repo is github.com/aks151/... — that breaks go get on a public module. Renamed throughout.

Two things I held back on

Both are outward-facing on a public repo, so they're your call:

- ./scripts/seed-issues.sh — creates 2 milestones + 14 issues. Want me to run it?
- The initial commit. 40-odd files, still zero commits on main, and origin is an empty pnd I'll commit and push.

✻ Crunched for 5m 30s

❯ /reload-plugins
  ⎿  Reloaded: 1 plugin · 0 skills · 6 agents · 1 hook · 0 plugin MCP servers · 0 plugin LSP servers

※ recap: We're building your incident-investigator project: V0 testbed is running and verified, and the agent-context docs plus a V0–V5 project plan are now in place. Next up is your call on whether I run
  the issue-seeding script and make the initial commit and push. (disable recaps in /confi

❯ can i change my model now?

⏺ Skill(claude-api)
Successfully loaded skill · 4 tools allowed

Yes — /model any time. The conversation carries over; the switch only affects subsequent turns, and nothing on disk is touched. One minor effect: prompt caches are model-scoped, so the first message after
a switch re-processes this conversation's context — a one-off latency/cost blip, not a c

The thing that actually matters here isn't the switch — it's that there are still zero cs unaffected by changing models, but it's the real exposure.

What I'd pick, based on what's next:

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                              Next stretch                                              │                          Model                           │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ You run incident 01, I answer questions and make small edits                                           │ Sonnet 5 — near-Opus on coding, cheaper, plenty for this │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ V1 wiring (collector, Prometheus/Tempo/Loki, Grafana provisioning — config-heavy, well-specified)      │ Sonnet 5                                                 │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ V3/V4 (evidence-collector interfaces, correlation engine, deciding what the model does vs. doesn't do) │ Back to Opus 5                                           │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

So: switch to Sonnet 5 now, switch back when we hit V3. The next phase is genuinely youreading the telemetry, writing the postmortem — and my role until then is mostly answering"why did it do that" and small edits.

Worth noting: this is exactly what the AGENTS.md / STATE.md work bought you. The project state lives in the repo now, not in this conversation — so switching models, starting a fresh session, or moving to
Cursor all cost about the same, which is nearly nothing.

Want me to make the initial commit before you switch? Good checkpoint, and it means a frtarts from a clean, readable tree.

✻ Brewed for 43s

❯ /model
  ⎿  Set model to Sonnet 5 and saved as your default for new sessions

❯ help me with what is done till now, a lot was done by Opus, so i have no track of things

  Ran 1 shell command

Good — everything's still there and the stack's still up (18h). Here's the full status.

Where things stand

Repo state: 44 files, zero commits. Everything is staged as untracked — nothing is lost, it's just not in git yet. I'd suggest committing today's work before anything else, so you have a checkpoint to
fall back to.

Stack state: running right now, containers up 18 hours (order-service:8081, inventory-see:8083, postgres on host port 55432).

What got built (V0 — complete)

A checkout system: order-service orchestrates a saga across inventory-service (stock + rervice (charges), all Go, all talking to Postgres, all wired with OpenTelemetry (traces +metrics + trace-correlated logs) going to stdout.

Verified working: one distributed trace spans all three services, DB pool saturation metrics are emitting, a k6 load test ran clean — 13,318 orders, 0 failures, p95 31.8ms.

The docs — this is your actual map back in

Read these in this order, they were built specifically so you (or any agent) can pick this up cold:

1. docs/STATE.md — the single most useful file. Short, says exactly where the project is and what's next.
2. docs/ROADMAP.md — V0 (done) → V5, with the gate each milestone has to clear before th
3. AGENTS.md — has one load-bearing rule: I build plumbing, you run every incident and write every postmortem. That's not a formality — it's the reason the project has interview value at all.
4. docs/ARCHITECTURE.md, docs/DEVELOPMENT.md — how it's wired, every env var, every comm
5. docs/decisions/ — three ADRs explaining why (single module, stdout-first telemetry, why Kubernetes/Redis/Kafka aren't in yet).
6. docs/background/ — your and ChatGPT's original planning docs, kept but marked supersehere — like a Java service — are no longer true).

What's not done yet — your move

Per docs/STATE.md, next step is incident 01 (DB pool exhaustion):

make load                                            # baseline first
PAYMENT_DB_MAX_CONNS=2 PAYMENT_DB_WORK=200ms make up
VUS=100 make load                                    # break it

Copy docs/incidents/TEMPLATE.md → 01-db-pool-exhaustion.md, write your prediction beforecompare.

Two loose ends from Opus's session

- No commit yet. Want me to do that now? Clean checkpoint before you start incident work
- scripts/seed-issues.sh exists but was never run — it creates GitHub milestones/issues for V1/V2 on your public repo. Not run without your say-so.                                                         
Want me to commit now, or do you want to look through anything first?                                                                                                                                       
✻ Cogitated for 34s                                                                                                                                                                                           
※ recap: You're building a distributed incident-investigator testbed (Go microservices + telemetry). V0 is done and running; next you need to inject the DB pool exhaustion incident and write the postmortem  yourself. First though: commit the 44 untracked files so nothing's at risk. (disable rec
                                                                                                                                                                                                               lets do one thing, lets simulate the development of this project in its current shape, tt all the insights of the project, i dont want any blackboxes at all
                                                                                                                                                                                                               Good instinct — walking through the build order rebuilds the mental model that just readive you. I'll go bottom-up: platform primitives first (nothing depends on business logic,everything else depends on these), then the domain services, then how it all wires together. Each package gets: the problem it solves, why it's shaped this way, and the actual code.                       
This'll take a few passes — let's do the platform layer first and I'll pause before moving to the services.                                                                                                 
---                                                                                                                                                                                                          1. envx — the foundation everything else reads from
                                                                                                                                                                                                               Read 1 file
                                                                                                                                                                                                               What it's for: every service needs to read config — pool size, timeouts, feature flags. alling os.Getenv and hand-parsing, there's one tiny package with a function per type.
                                                                                                                                                                                                             Why it looks like this:
- Every function has the identical shape: look up the var, fall back to a default if unset/unparseable. No panics on bad input (except MustString) — a typo'd env var degrades to the default with a         slog.Warn, rather than crashing the service. That's a deliberate call: in a system you'rsconfigure to cause incidents, you don't want typos to be indistinguishable fromintentional incidents.                                                                                                                                                                                       - MustString is the one exception — it os.Exit(1)s. That's reserved for things with no s_URL. There's no sane fallback for "no database," so failing fast at boot is correctthere.                                                                                                                                                                                                       - No struct, no reflection, no tags (envconfig-style libraries do this differently). Giv services, a few dozen knobs total), a magic struct-tag library would be over-engineering— every call site is explicit about what it reads and what happens if it's missing.                                                                                                                         
This package has zero dependencies on anything else in the repo — it's leaf-level. Everything above it (telemetry, httpx, db) calls into it, never the reverse.                                             
---                                                                                                                                                                                                          2. telemetry — OpenTelemetry SDK wiring
                                                                                                                                                                                                               Read 1 file
                                                                                                                                                                                                               What it's for: OpenTelemetry has three separate signal types — traces, metrics, logs — awiring (an exporter, a provider, and registration as the process-wide default). This filedoes that setup once per service at boot.                                                                                                                                                                   
The core concepts, mapped to this code:                                                                                                                                                                     
Resource (buildResource, line 119) — a set of attributes describing what process is emitting telemetry: service name, version, environment, and a ServiceInstanceID (the container hostname). Every span and every metric point gets stamped with this. The comment on line 129-130 explains why the ut it, if payment-service has 3 replicas and one is unhealthy, all the telemetry from all 3 replicas looks identical — you can't tell "one bad pod" from "the whole service degraded."                                                                                                                
Propagator (line 80-83) — this is the mechanism that makes distributed tracing actually distributed. When order-service calls payment-service over HTTP, the trace ID has to travel in an HTTP header so     payment-service's spans get attached to the same trace as order-service's. propagation.Ttandard for that header (traceparent). Without this line, you'd get three separatesingle-service traces instead of one trace spanning all three services — which is exactly the failure mode the comment on line 77-79 calls out. This is also the thing I actually verified worked, back when we ran the first checkout — you saw the trace_id show up in all three services' logs.

TracerProvider vs MeterProvider (tracerProvider / meterProvider, lines 136 & 164) — theselines for traces and metrics. Structurally identical: pick an exporter based oncfg.Exporter (stdout/otlp/none), wrap it in a provider, attach the resource. They're separate functions because traces and metrics are separate OTel APIs with separate exporter packages — otlptracegrpc vs
otlpmetricgrpc even though both talk to the same collector endpoint in the otlp case.

Sampler (line 160) — ParentBased(TraceIDRatioBased(cfg.SampleRatio)). Sampling decides wecorded, since not every span gets exported in high-volume production systems. ParentBased means: if this span already has a parent (i.e., it's not the start of a new trace), inherit the parent's sampling decision — you never want half a trace sampled and half dropped. TraceIDRatioBased(1.0)
is the root decision: sample 100% of root traces. That 1.0 default is deliberate — durinu want every request traced, not a statistical sample, or you might miss the one requestthat shows the failure.

Why the comment at line 54-59 exists — this is the real bug I caught and fixed earlier in this session. OTEL_TRACES_SAMPLER_ARG and OTEL_METRIC_EXPORT_INTERVAL are names reserved by the OpenTelemetry spec
itself — the SDK reads them directly, independent of this code, and it expects differentonds, not "15s"). I'd originally named our config vars the same thing, which caused theSDK to try parsing our value and log a parse warning, while our own envx.Duration call parsed it separately and got a different value. Two systems silently disagreeing about one variable's meaning.
Renamed to TRACE_SAMPLE_RATIO / METRIC_EXPORT_INTERVAL to avoid the collision entirely.

Runtime metrics (line 105) — go.opentelemetry.io/contrib/instrumentation/runtime auto-em size, goroutine count, GC pause time) as metrics with zero extra code. The commentexplains why: this is what turns "the container got OOMKilled" from a mystery into something you saw coming — you'd watch heap climb in the metrics before the kill happens.

Setup returns a Shutdown closure (line 66, 110-116) — both providers batch spans/metrics and flush periodically, not on every single span. If the process exits without calling shutdown, whatever's sitting
in the batch buffer is lost — which tends to be the last few seconds of activity, i.e. eg crashed. This closure is what app.go (we'll get to it) calls via defer during gracefulshutdown.

Now the second telemetry file — logging:

  Read 1 file

What it's for: the third signal — logs — but OpenTelemetry doesn't have a mature Go logging SDK the way it does for traces/metrics, so this uses Go's standard log/slog directly and bolts on the one thing
that matters: correlating a log line to the trace it belongs to.

The mechanism — a decorator around slog.Handler: slog.Handler is Go's logging interface le/WithAttrs/WithGroup/Enabled can be a logger backend. traceHandler wraps a real handler(the JSON one) and intercepts every Handle call to inject two extra fields before delegating to the wrapped handler. This is the standard decorator pattern — traceHandler doesn't know how to actually
write logs, it just adds fields and passes through.

Why trace.SpanContextFromContext(ctx) line 38 is the whole point: every HTTP handler in context.Context that — because of the OTel HTTP middleware we'll see in httpx next —carries the active span. Pulling TraceID()/SpanID() out of that context and stamping them onto every single log line means: given one trace_id, you can grep every service's logs and get exactly the lines
from that one request, in order, across all three services. That's literally how I diagn$(... grep trace_id ...) then grepped all three services for it.

This is deliberately the cheapest possible version of log correlation — no log shipping,out with two extra fields. The comment says as much: "the cheapest useful thing in thewhole observability stack." V1 will add Loki so you can query this instead of grep, but the correlation mechanism (trace_id/span_id on every line) doesn't change — Loki just makes it queryable instead of
grep-able.

---
3. httpx — server, client, routing, responses

Four files here. Let's go through them in the order a request actually flows.

  Read 2 files

server.go — the four timeouts that decide how a server dies under load.

This is one of the most important files in the whole repo for the incident work ahead, and it's worth being very deliberate about what each timeout does:

- ReadHeaderTimeout — how long the server waits for a client to finish sending HTTP headers. Guards against slow-header attacks.
- ReadTimeout — how long it waits for the full request body.
- WriteTimeout — how long it has to write the response, starting from when the request was read.
- IdleTimeout — how long a keep-alive connection can sit idle before being closed.

The comment at line 13-15 explains why these are explicit instead of Go zero values: Go'imeouts by default. If you don't set them, a slow or hung client (or slow downstream thatthe handler is waiting on) holds a goroutine and a file descriptor open forever. Under load, that's exactly how you exhaust the server — not by CPU, but by accumulating stuck connections. This is directly
relevant to the incidents ahead: if you ever wanted to simulate "a slow client dying by bs.

NewServer wraps the handler in otelhttp.NewHandler — this creates the outer server span routing even happens. It's the outermost layer of instrumentation; the mux handles theinner layer.

mux.go — the request lifecycle for every route.

Handle is what every handler in order/payment/inventory calls to register a route — never the raw mux.HandleFunc. It wraps the handler in observe, which does three things on every single request:

1. Renames the span from generic to route-specific (lines 27-30). Here's the subtlety: otelhttp.NewHandler in server.go creates a span before the router has matched anything, so it can't know the route
pattern yet — Go's http.ServeMux only exposes r.Pattern (the matched pattern like "GET /andler, after matching. So the naming happens in two stages: outer wrapper creates thespan, inner observe renames it once the pattern is known. Why this matters: if you didn't rename it and just used r.URL.Path, you'd get a distinct span name per order ID (/orders/abc123, /orders/def456,
...) — that's "high cardinality," and it breaks aggregation in any trace backend, becausled "GET /orders/{id}" you get thousands of unique things.
2. Panic recovery (lines 35-44) — a defer+recover() around every handler. If a handler panics (nil pointer, index out of range, whatever), this catches it, logs it, marks the span, and returns a 500 —
instead of crashing the entire process and taking down every other in-flight request tooing, but it's also incident-relevant: it means "one bad request" and "the whole service is down" are always distinguishable failure modes in this codebase, on purpose.
3. Access logging (lines 46-52) — one structured log line per request, always, win or lotatus, duration. This is what you'll be grep-ing during incident work.

statusRecorder (lines 59-77) is the same decorator trick as traceHandler in the logging  doesn't expose "what status code did the handler actually send," so this wraps it andcaptures the code on WriteHeader/Write so the access log line can report it accurately.

Now the client side and response helpers:

  Read 2 files

client.go — this is where "one slow query causes retry amplification" actually gets its plumbing.

The comment at lines 13-17 states the thesis directly: three settings here are direct incident levers.

- Timeout — per-request deadline for calls to a specific dependency. Notice this isn't one global timeout for all outbound calls — each Downstream (order→inventory, order→payment) gets its own client with
its own timeout, configured separately (INVENTORY_SERVICE_TIMEOUT, PAYMENT_SERVICE_TIMEOmd/order-service/main.go). The reasoning: if you had one shared timeout, it'd have to besized for your slowest dependency, which makes it useless for catching a fast dependency that's become abnormally slow.
- The connection pool fields (MaxIdleConns, MaxIdleConnsPerHost, MaxConnsPerHost) — thise comment at lines 48-50 calls out a genuine Go gotcha: http.DefaultTransport keeps only 2 idle connections per host by default. Under load, a service making many concurrent calls to the same downstream will constantly be opening new TCP connections because the pool of 2 is exhausted — and
each new connection pays a TCP handshake + (if TLS) a TLS handshake. That latency gets mtream is slow" when it's actually "we're re-dialing constantly." SettingMaxIdleConnsPerHost: 100 fixes that. MaxConnsPerHost: 0 (unlimited) is explicitly called out as "a knob for connection-starvation experiments" — set it to something small later and you've built a
client-side bottleneck that's invisible unless you know to look for it.
- DialTimeout is separate from Timeout — dialing (opening the TCP connection) and waiting for the response are different phases with different failure modes; a dependency that's unreachable (DNS/network
issue) should fail fast via DialTimeout rather than waiting the full request Timeout.

Span naming here mirrors the server side (line 66-73) — same cardinality reasoning as muls: "POST inventory-service/reserve" rather than a raw URL, so a trace with threedependencies is actually legible. You saw this fixed earlier in the session — before the fix, outbound spans were all named literally "HTTP POST", indistinguishable from each other in a trace view.

respond.go — the shared response/request helpers every handler uses.

- maxBodyBytes = 1 MiB (line 15) — every request body is capped via http.MaxBytesReader. Without this, a client can send an arbitrarily large body and make the service allocate memory proportional to it —
a cheap way to OOM a service that has nothing to do with real load. This is a security-hnt-specific, but worth knowing it's there.
- Error() (lines 34-40) — every error response does two things at once: writes the JSON body and, for 5xx only, marks the span as failed (span.SetStatus(codes.Error, msg)). That second part is why, when
you look at a trace for a failed request, the failing span is visually flagged red/errornot just a log line, it's baked into the span itself. 4xx (client's fault — bad input)deliberately does not mark the span as an error, which matters for incident work: your error-rate dashboards should reflect your system's health, and a client sending garbage isn't a signal that your
service is unhealthy.
- DecodeJSON() (lines 43-56) — two strictness choices: DisallowUnknownFields() rejects a request body with fields the struct doesn't expect (catches typos and API drift early), and the trailing-decode
check on line 52 rejects {}  {} — multiple JSON values concatenated — which json.Decoderaccept, decoding only the first and ignoring the rest.

---
That's the full HTTP layer. Two packages left in the platform tier — db (the one with the most incident-relevance of anything in this codebase) and faultx — then app, which is where all of this actually
gets composed. Want me to keep going through those now, or pause here and let questions ux first?

✻ Crunched for 1m 58s

❯ now since you have given all the explanations, lets approach each steps in terms of deci steps for all the components like: aim, architecture decsision, tech stack, low leveldecisions

Good structure — that maps directly onto "tell me about a design decision" in an interview, too. Let me recap what we've covered in this format (compressed), then continue forward the same way.

Recap: envx

- Aim: every service reads config from the environment uniformly, because in this project incidents get injected by changing config and restarting — not by redeploying code.
- Architecture decision: a leaf package with zero dependents in the repo. One function ption...), not a struct-tag/reflection library.
- Tech stack: stdlib only — os, strconv, time, log/slog. No envconfig/viper — unjustified at 3 services and a few dozen knobs (same "don't add infra before you need it" reasoning as the rest of the
project).
- Low-level decisions: fail soft everywhere (bad/missing value → default + slog.Warn) except MustString, which os.Exit(1)s — reserved for things with no safe default, like DATABASE_URL. Deliberate: typos
degrading to defaults must be distinguishable from intentional incidents.

Recap: telemetry

- Aim: give every service correlated traces + metrics + logs, starting as cheap as possiof not having a real backend is felt before one gets added.
- Architecture decision: one Setup() call at boot wires all three signals and registers them as process-wide globals. The exporter is a config switch (stdout/otlp/none) — zero application-code changes to
redirect telemetry, which is the thing ADR 0002 is betting on.
- Tech stack: OpenTelemetry Go SDK (otel/sdk/trace, otel/sdk/metric), stdout exporters now / OTLP-gRPC exporters wired but unused until V1, contrib/instrumentation/runtime for free Go runtime metrics,
stdlib log/slog with a custom Handler decorator for trace-correlated logs (no OTel logginough in Go yet).
- Low-level decisions: W3C TraceContext+Baggage propagators (without this, distributed traces silently become per-service traces — the single most common way to end up with useless telemetry);
ParentBased(TraceIDRatioBased(1.0)) sampler — 100% sampling, because during incident reptistically miss the one request that shows the failure; ServiceInstanceID (hostname) inthe resource so replicas are distinguishable; config vars deliberately renamed away from OTEL_* after discovering the SDK reserves those names and parses them itself in an incompatible format (integer ms
vs. Go duration) — a real bug I caught and fixed mid-session; Shutdown returned as one cflushes every pipeline with a single defer.

Recap: httpx

- Aim: make every HTTP hop — inbound and outbound — uniformly timeout-bounded, traced, as and connection pooling are the literal mechanism behind cascading failures and retrystorms later in the catalogue.
- Architecture decision: split into server construction (server.go), a shared route wrap goes through, client construction (client.go), and shared response/decode helpers(respond.go). Both server and client wrap otelhttp for automatic span creation.
- Tech stack: stdlib net/http (Go 1.22+ pattern-matching mux), contrib/instrumentation/nhe server and client transport.
- Low-level decisions: explicit non-zero timeouts everywhere (Go's http.Server has none by default — a slow client/handler holds a connection forever); per-dependency client timeout and connection pool
rather than one shared client (a shared timeout would have to be sized for the slowest dss); MaxIdleConnsPerHost raised from Go's default of 2 → 100 (otherwise services re-dialconstantly under load and the latency gets misattributed to "the dependency is slow"); span renaming to low-cardinality route patterns on both sides ("GET /orders/{id}" not "GET /orders/abc123"); the same
decorator trick (wrap-and-intercept) used twice — statusRecorder for capturing the respolier for log correlation; strict JSON decoding + 1 MiB body cap as theboundary-validation default.

---
Now continuing forward in this format — next up is db, the package with the most direct talogue.

  Read 2 files

db — connection pool + saturation metrics

- Aim: make "the database is slow" and "we've run out of connections" — two failure mode the outside (both present as elevated request latency) — distinguishable from telemetryalone, without guessing.
- Architecture decision: wrap pgxpool.Pool in a thin Pool type that adds exactly one beh applied on every checkout (AcquireContext) — and register a background metrics callbackat connect time. Every domain store (order, payment, inventory) calls pool.AcquireContext(ctx) before doing DB work, so the timeout is uniform across all three services rather than being each handler's
problem to remember.
- Tech stack: jackc/pgx/v5/pgxpool (the standard high-performance Postgres driver/pool for Go — not database/sql, because pgx exposes richer pool internals like pool.Stat() that this whole file depends
on), exaring/otelpgx for automatic per-query tracing, OpenTelemetry's ObservableUpDownCotric instruments with a RegisterCallback (a pull-based metric — read pool.Stat() on demand each export cycle, rather than manually incrementing counters everywhere pool state changes).
- Low-level decisions:
  - AcquireTimeout (default 3s) is the single most important line in this file. Without it, when the pool is exhausted, a request just hangs — waiting indefinitely for a connection — and the service looks
perfectly healthy (still returning 200s eventually, still passing health checks) while els. With it, pool exhaustion becomes a fast, attributable context.DeadlineExceeded errorinstead of an invisible hang.
  - DB_MAX_CONNS defaults to 25, not something bigger. The comment spells out why: Postglobal cap of 100 total connections. Three services × 25 = 75, already 75% of that budget — a detail that becomes very relevant the moment you try to scale a service to multiple replicas, or the moment you want to reproduce pool exhaustion (PAYMENT_DB_MAX_CONNS=2 is the actual incident-01
lever, cranking this down).
  - Nine separate metrics, not one. The doc comment (lines 13-19) gives the actual diagnostic recipe: DB genuinely slow → acquire.duration stays flat while query spans themselves get long; pool exhausted
→ acquire.duration climbs, connections.acquired pins at max, and acquire.empty (acquisitrts rising. You need the combination to tell them apart — no single metric does it.
  - db.pool.connections.constructing, not a "callers blocked" gauge (lines 45-48) — I initially wanted to expose "how many goroutines are currently blocked waiting for a connection," which is the single
most direct saturation signal, but pgxpool doesn't expose that stat at all. Had to subst (saturation = acquired == max + rising empty count) and leave a comment saying soexplicitly, rather than papering over the gap with a fake metric. Worth internalizing as a general lesson: sometimes the metric you actually want doesn't exist in the library, and the honest move is to
say that, not silently approximate it and call it the same name.
  - otelpgx.WithIncludeQueryParameters() — every SQL statement becomes its own child span with the actual query text and parameters attached, nested under the request span. That's what let a trace show
pool.acquire → prepare → query as distinct spans under POST /payments when we verified i

faultx — the chaos harness, kept deliberately separate

  Read 1 file

faultx — chaos injection, quarantined from business logic

- Aim: give a small number of genuinely un-reproducible failures (a flaky/slow third-par only one used in V0) an honest way to exist, without letting "fake the failure" becomethe default tool for every incident. The doc comment (lines 8-13) is explicit that most incidents in the catalogue should be reproduced through real config, not this package.
- Architecture decision: the injector lives in its own package, imported only by paymentver by platform/db or platform/httpx. That's a deliberate boundary — anyone reading therepo should be able to answer "is this failure real or injected?" by checking one import, not by auditing every handler.
- Tech stack: nothing beyond stdlib (math/rand/v2, time, context) plus OTel span attribus visible in the trace (fault.injected: true), not a silent, undetectable lie about system behavior.
- Low-level decisions:
  - Zero-value injector is a no-op (line 38 comment) — New(prefix) with no env vars set returns an Injector that does nothing, so every handler can unconditionally call faultx.New(...) and .Apply(ctx)
without a feature-flag branch anywhere.
  - The sleep respects context cancellation (lines 69-77) — this is the detail that makes it an honest simulation rather than a toy one. If you just called time.Sleep(delay), an injected "slow provider"
would ignore the caller's timeout entirely and always sleep the full duration — which isdency behaves. Using select against ctx.Done() means the injected delay interacts with the caller's deadline exactly the way a real slow HTTP call would: if the caller times out first, Apply returns immediately with the caller's error, not the fault's.
  - Latency and error rate are independent, composable knobs — you can have both a base babilistic error on top, because a real flaky provider is usually both slow andoccasionally failing, not one or the other.

app — the boot sequence that composes everything above

This is the last platform file, and it's the one that actually wires envx → telemetry → db → httpx → your handlers into a runnable process.

  Read 2 files

app — the boot sequence, and the payoff for everything above

- Aim: every cmd/<service>/main.go should be ~20 lines. All the ceremony — config, telemetry, DB, health checks, graceful shutdown — happens exactly once, here, so it can't drift between the three
services.
- Architecture decision: app.Service is a small struct a main.go fills in (Name, DefaultAddr, RequiresDB, and a Routes callback that registers that service's actual handlers). app.Run(svc) does everything
else. This is the inversion-of-control / template-method pattern: the framework (app) owthe caller only supplies the parts that differ per service.
- Tech stack: stdlib only — os/signal, syscall, context, net/http. No framework (no Gin/Echo/Chi) — deliberate, since http.ServeMux with Go 1.22's pattern routing already does everything three services
need, and pulling in a framework here would be the same "unjustified infra" mistake the  avoid.
- Low-level decisions, walking the actual boot sequence in run():
  a. Signal-aware root context (line 54) — signal.NotifyContext gives you a context.Cont SIGINT/SIGTERM. Everything downstream — in-flight DB queries, outbound HTTP calls —inherits this context, so a shutdown signal propagates as cancellation, not as a hard kill. This is the plumbing that makes graceful shutdown possible at all.
  b. Telemetry first, DB second, HTTP server last — order matters: you want telemetry liuld fail (DB connect) so the failure itself gets traced/logged; you want the DB connectedbefore serving traffic so /readyz has something real to check from request one.
  c. errCh + select (lines 85-98) — the server runs in a goroutine; the main goroutine btartup error (e.g., port already in use) or the shutdown signal, whichever comes first.This is a standard Go pattern for "wait for the first of two independent things to happen."
  d. The shutdown-grace-period comment (lines 100-102) is worth internalizing directly —tx) stops accepting new connections but lets in-flight requests finish, up toSHUTDOWN_TIMEOUT (default 10s). If a request is mid-checkout (order → inventory → payment, several hops) and the grace period is shorter than that chain can take, a routine deploy looks like an outage to
that one customer. This is directly related to incident-08 in the catalogue (bad deploym one more knob that can silently turn "we shipped a new version" into "we droppedrequests."
  e. flushTelemetry uses a fresh context, not the (already-canceled) root one (lines 113ug class worth knowing by name: if you reused the canceled root context to flush the final telemetry batch, the flush would immediately fail because the context is already done — you'd lose exactly the spans/logs from the shutdown sequence itself, which is often the most interesting part.
- registerHealth — liveness vs. readiness, the distinction that becomes load-bearing on
  - /healthz (liveness) answers "is this process wedged?" — and deliberately never touches the database. If it did, one slow/down Postgres would cause every replica's liveness probe to fail, and           Kubernetes would restart the entire fleet in response to a database problem — the exact arting healthy app containers does nothing to fix the database and just adds athundering-herd reconnect storm on top.                                                                                                                                                                        - /readyz (readiness) does ping the DB, with its own 2-second timeout independent of ting readiness only pulls this one instance out of the load balancer's rotation, which isthe safe way to shed traffic from an instance that can't currently serve it.                                                                                                                                   - The doc comment says outright: "Getting these backwards is one of the incidents in tng is deliberately foreshadowing incident 15 (bad readiness probe) once Kubernetes is inplay.                                                                                                                                                                                                       
---                                                                                                                                                                                                          That's the entire platform layer — envx → telemetry → httpx → db → faultx → app, six pacmain service does rests on these. Next tier up is the three domain packages (inventory,payment, order) — same four-part format. Want me to continue straight through, or pause here first?                                                                                                         
✻ Sautéed for 1m 36s                                                                                                                                                                                          
❯ dude you have to question me                                                                                                                                                                                
Fair — lecturing at you doesn't build the recall you actually need for an interview. Let's flip it. Answer these based on what we've covered (envx, telemetry, httpx, db, faultx, app) — I'll tell you where you're right, where you're fuzzy, and we don't move to the domain services until this st

1. (envx) Why does MustString call os.Exit(1) while every other function just falls backarning? What's the actual principle drawing that line, not just "it's more important"?

2. (telemetry) We renamed our config vars away from OTEL_TRACES_SAMPLER_ARG / OTEL_METRI kept those names, what specifically breaks — and if you hadn't caught it while testing,what would you have observed in production that pointed you at "the env var name is the bug" rather than somewhere else?

3. (httpx) Suppose DefaultClientConfig left MaxIdleConnsPerHost at Go's default of 2 instead of setting it to 100. Under load, you'd see p99 latency for order→payment climb. If all you had was a trace —
no code access — what specifically in that trace would make you suspect "client-side conather than "payment-service itself is slow"?

4. (db) Walk it through end to end: PAYMENT_DB_MAX_CONNS=2, then 50 concurrent requests for 200ms via PAYMENT_DB_WORK. Which db.pool.* metric moves first, which moves second, and what does a trace of one of the stuck requests look like right at the AcquireContext boundary?

5. (app) Why does registerHealth put the DB ping behind /readyz and never /healthz? Don't just restate the rule — give me the actual outage scenario that happens if you get it backwards.

6. (faultx) The rule here is "most incidents should come from real config, not faultx." Payment's simulated slow provider is the one exception. Why can't you reproduce "flaky third-party payment provider"
the same way you reproduce the others — with DB_MAX_CONNS or client timeouts?

Take these one at a time or all at once, whichever you'd rather.

✻ Churned for 26s

❯ not answering based on what you cover, lets go in a flow, where you will name a step, an the decision questions, assume you are approaching the development of current shape ofapplication from the begining, strictly donot make any changes

Got it — I'll play the sequence back as if we're deciding it live, one build step at a time. You answer as the engineer making the call; I'll only tell you where it lands versus what actually shipped once
you've answered. No file changes.

Step 1 — Before a single package exists

You have the brief: a deliberately breakable e-commerce checkout flow, plus (eventually)noses it. Nothing is written yet.

Aim. State it precisely — what does V0 need to be, and what must it explicitly not be yeeady too much?)

Architecture decision. You know you need at least three services (order, payment, inventr amount of plumbing — config reading, telemetry setup, DB pooling. Do you give eachservice its own repo/Go module, or one repo/one module with three cmd/ binaries? Make the call and justify it against the specific fact that they share plumbing.

Tech stack. Language for the services, and separately, why that specific choice serves this project's goal (re-read the brief: the point isn't the checkout app, it's operational intuition) rather than
being a generic "what's a good backend language" answer.

Low-level decisions. Given your architecture answer above, sketch the actual directory lhere does shared infrastructure code live relative to each service's business logic, andwhat's the naming/structural signal that tells a reader "this file is plumbing, not domain logic" before they even open it?

Go ahead.

✻ Baked for 37s

❯ V0: have a simple distributed system ready, not kubernetes or any other setup in it

  "Architecture decision. You know you need at least three services (order, payment, inventory) that will share a fair amount of plumbing — config reading, telemetry setup, DB pooling. Do you give each
  service its own repo/Go module, or one repo/one module with three cmd/ binaries? Make thnst the specific fact that they share plumbing." : what is plumbing, not that familiarwith distributed systems of now, and learning distributed systems is what my aim is too from this whole project, but to answer this question, i think they should have separate modules for each

  "Tech stack. Language for the services, and separately, why that specific choice serves this project's goal (re-read the brief: the point isn't the checkout app, it's operational intuition) rather than
  being a generic "what's a good backend language" answer." - golang for the distributed s in different tech stacks would also be benfitial, primary db - postgresql, cache -redis, rest all are something which chatgpt has suggested and i am not upskilled enough to suggest them by myself, mentioning them here for my practice: telemetry standard: OpenTelemetry, metrics:
  prometheus, traces: graphana tempo, logs: graphana loki, visualization: grafana, event st: docker kubernetes, k8s packaging: helm, ci: github actions, load generation: k6,failure injection: initial custom scripts...later chaos mesh, local dev: docker compose

  "Low-level decisions. Given your architecture answer above, sketch the actual directory layout you'd start with — where does shared infrastructure code live relative to each service's business logic, and
  what's the naming/structural signal that tells a reader "this file is plumbing, not doma open it?": i dont have an answer for this, i mean not upskilled enough to answer this

Good — let's go through these one at a time. Some of this is genuinely new ground for yos a convention and question where it's a judgment call.

Aim — partially right
                                                                                                                                                                                                          "No Kubernetes" is correct, but it's only half the requirement. Ask yourself: if I hand telemetry and you break something in it, can you actually find out what happened? Adistributed system with no visibility into itself doesn't serve V0's purpose at all — you'd be breaking it and then guessing.                                                                             
So V0's real aim is two things at once: minimal infrastructure (no k8s, no Redis, no Kafka, no gateway) and enough visibility to diagnose a failure from telemetry alone (traces, metrics, logs — even if they just go to stdout). Keep that pairing in mind — it's why telemetry got built in ste, immediately after the services existed, before anything else.

"Plumbing" — definition first, since you asked directly

Plumbing = infrastructure code whose shape doesn't care which service it's in — reading a tracer, pooling DB connections, health-check endpoints. It looks identical whetheryou're in order-service or payment-service.

Business/domain logic = code that's specific to what this service is for — how a checkout saga runs, how stock gets reserved, how a charge gets recorded. inventory-service's domain logic and
payment-service's domain logic are genuinely different; their plumbing is not.

Architecture decision — you said "separate modules." Let's pressure-test that.

Two follow-up questions — answer both before we lock this in:

1. Say all three services are separate Go modules (separate go.mod, maybe separate repostelemetry setup code — the trace-correlated logger, say. How many places do you fix it,and how do the other two services find out the fix exists?
2. What do you actually gain from separate modules that you'd lose by having three cmd/ ach still building its own separate Docker image, each independently configured via itsown env vars, each independently deployable and independently killable? Independent deployability comes from separate containers, not separate Go modules — so if that's true, what's left as the argument
for separate modules?

Tech stack — Go reasoning is sound, one instinct needs pressure-testing
                                                                                                                                                                                                     Go for the core: good, and for the right reason (it's a language you're deliberately usifrastructure ecosystem you're trying to break into — Kubernetes, Prometheus, Terraform are all Go).                                                                                                                                                                                             
But you also said "having services in different tech stacks would also be beneficial" and want to do it now. Apply the project's own rule back onto that instinct: no infrastructure without a demonsrequirement. Does "three services, three languages, on day one" pass that test? What speoes having, say, Node in the mix from day one teach you that Go-only doesn't teach you?(There's a real answer here, and it's not "no polyglot ever" — but the timing and justification matter a lot.)                                                                                       
On the rest of your list (Redis, Kafka, Prometheus, Tempo, Loki, Helm, Chaos Mesh...) — good that you flagged you're reciting these, not reasoning about them yet. That's the honest state to be in, it's fine — we'll interrogate each one individually, at the exact moment the build reachtempted to reach for it, not all at once now. That's a more useful way to learn themanyway: "why does this exist" lands much harder when you've just felt the problem it solves.                                                                                                         
Low-level layout — this one's a convention, not a judgment call, so I'll just teach it                                                                                                               
Go has a real, compiler-enforced feature here: any package under a directory named internal/ can only be imported by code inside that same module — the compiler will refuse to compile if an outsidetries to import it. So internal/ isn't a naming suggestion, it's an enforced boundary.
                                                                                                                                                                                                     The actual layout:
cmd/order-service/main.go       # entrypoint, ~30 lines                                                                                                                                              cmd/payment-service/main.go
cmd/inventory-service/main.go                                                                                                                                                                        internal/
  platform/                     # ← plumbing lives here                                                                                                                                                  envx/       config
    telemetry/  otel wiring                                                                                                                                                                              httpx/      server/client/routing
    db/         pool + metrics                                                                                                                                                                           faultx/     chaos harness
    app/        boot sequence composing all of the above                                                                                                                                               order/                        # ← domain logic lives here
  payment/                                                                                                                                                                                             inventory/
                                                                                                                                                                                                     The naming signal you asked about: everything under internal/platform/ has short, infra-vx, httpx, faultx, db) — abbreviations, utility-shaped. Everything at internal/<name>/uses the actual business noun (order, payment, inventory). A reader who's never seen this repo can predict "this file is plumbing" from the import path alone, before opening it.                    
Quick check: given that layout, if internal/order needed to import something from internal/payment directly — bypassing the HTTP call between them — would that be a structural violation of anythingjust an ordinary Go import? (There's a real answer, and it matters for why order talks th a client in the first place, instead of just calling a Go function.)
                                                                                                                                                                                                     Answer the three follow-ups above and we'll lock Step 1, then move to Step 2.
                                                                                                                                                                                                       Cogitated for 1m 14s
                                                                                                                                                                                                       recap: We're building an incident-investigation testbed to sharpen your production-failurviews, and right now we're walking through V0's design decisions Socratically. Next:answer the three follow-up questions on module structure, polyglot timing, and cross-service imports. (disable recaps in /config)                                                                    
❯ if internal/order and internal/payment talk directly then its not microservices and distributed architecture anymore                                                                                 
  "  Say all three services are separate Go modules (separate go.mod, maybe separate repos). You find a bug in your telemetry setup code — the trace-correlated logger, say. How many places do you fixand how do the other two services find out the fix exists?" - looks like my fundamentalsrate containers was not clear, so giving each service its own repo/Go module is not howwe separately containerize it!                                                                                                                                                                       
   couldn't find the third question                                                                                                                                                                    
You're landing on the right insight faster than you're giving yourself credit for. Let's confirm and clean up.                                                                                       
Low-level layout — your answer is exactly right, here's the mechanical reason underneath it                                                                                                          
Correct: if order called into payment directly, it stops being distributed. The sharper version of why: a Go function call is in-process. For order to literally call a function inside payment, bothhave to be compiled into the same binary and run in the same OS process — which means on gets redeployed, both get redeployed; there's no way to have "payment is down but orderstill serving" as a distinct state. That's precisely the kind of incident this whole project explores, so it can't be structurally impossible.                                                       
That's why internal/order/clients.go makes an actual HTTP call to reach payment — not a style preference, the only way to reach code running in a separate process is over some transport (HTTP here)internal/ visibility rule is a second, independent guard on top of that — even if someon/payment from internal/order directly, the compiler refuses. Two layers of protectionagainst the same mistake: process separation (real) and compiler enforcement (backup).                                                                                                               
Architecture decision — your realization is the key one                                                                                                                                              
▎ "giving each service its own repo/Go module is not how we separately containerize it"                                                                                                              
Exactly. That's the whole answer. Independent deployability comes from the Dockerfile + build step — each cmd/<service> compiles to its own binary, each binary goes into its own image, each image gown container with its own config. None of that depends on Go module boundaries at all. arate Go modules" stops buying you the thing you actually wanted (independentdeploy/scale/failure) and starts only costing you something (see below) — which is why the actual call was one module.                                                                               
On the missing question — my count was off, sorry                                                                                                                                                    
I said "answer the three follow-ups" but there were actually four scattered across sections, and only two are still open. Here they are, cleanly, no more digging through the wall of text:          
1. You find a bug in the trace-correlated logger — shared plumbing. If all three services were separate Go modules: how many places do you fix it, and how do the other two services find out the fixexists? (Concretely: what would you have to actually do — bump a version number somewher repos? Nothing at all?)
                                                                                                                                                                                                     2. Apply the project's own rule ("no infrastructure without a demonstrated requirement")y one" instinct. What specific incident or lesson does having, say, Node in the mix fromday one teach you that Go-only doesn't? Is there a reason to have it later, once something specific demands it, instead of now?                                                                      
Answer those two and Step 1 is fully locked — then we move to Step 2.                                                                                                                                
✻ Sautéed for 44s                                                                                                                                                                                      
❯ " You find a bug in the trace-correlated logger — shared plumbing. If all three services were separate Go modules: how many places do you fix it, and how do the other two services find out the fix exists? (Concretely: what would you have to actually do — bump a version number somewher repos? Nothing at all?)": although i cant think about how a trace-correlated loggerwould have been implemented, but i think to fix it we will just make change in trace-correlated logger, as it is a plumber, and then the separate module would automatically call the correct code for
  trace-correlated logger

  "Apply the project's own rule ("no infrastructure without a demonstrated requirement") tone" instinct. What specific incident or lesson does having, say, Node in the mix fromday one teach you that Go-only doesn't? Is there a reason to have it later, once something specific demands it, instead of now?" - i think having go for all the services would give me a better visibility
  on how distributed systems can be approached in golang, rather than jumping the steps ange setup.

Q1 — this is the one to fix, and it's a genuinely common misconception, not a silly one

▎ "the separate module would automatically call the correct code"

Nothing is automatic here — this is the actual mechanical gap. Let's trace it concretely

If the trace-correlated logger lived in its own module — say github.com/aks151/platform-payment-service, and inventory-service would each have their own go.mod, and each onewould pin a specific version of that dependency, exactly the way our current go.mod pins github.com/jackc/pgx/v5 v5.10.0. Not "whatever's newest" — a fixed version, frozen at that number, for reproducible
builds.

So here's what actually happens when you fix the bug:

1. You fix it in platform-lib, commit, and cut a new version — v1.2.1 (Go versions modul
2. All three services are still pinned to v1.2.0. Nothing about their go.mod changed. They will keep building and running the buggy version indefinitely — forever, if left alone.
3. You have to go into order-service's repo, run go get github.com/aks151/platform-lib@vgo.mod/go.sum, and redeploy. Then repeat that by hand in payment-service. Theninventory-service.

So the real answer to "how many places do you fix it": the code fix happens once, but the propagation requires three separate version bumps, three separate PRs, three separate redeploys — and if you
forget one, there's no error, no warning, nothing. That service just quietly keeps runnid you won't know unless you go check.

Compare that to what we actually built: internal/platform/telemetry is compiled directlyrom the same source tree, in the same build. Fix the bug once, docker compose buildrebuilds all three images from that one fixed source, and there is no version to bump, no service that can silently lag behind. That's the concrete cost separate modules impose that a single module
doesn't — not "more files," but silent drift risk with manual, forgettable propagation.

Q2 — correct, and matches the actual reasoning

Good instinct, and it's exactly backwards from what would be résumé-architecture: masterlanguage first, so that when you do go polyglot later (the actual plan: convertinventory-service to Java/Spring at V2, specifically to get JVM failure modes — heap OOM, GC pauses, HikariCP exhaustion — plus proof that trace context propagates across languages), you're adding it for
a reason you can defend, not because three languages looks more impressive on a README.

Step 1 — locked

- Module structure: one Go module, cmd/<service>/main.go per binary, shared plumbing in
- Independent deployability comes from separate Docker images/containers/configs — not from module boundaries.
- Language: Go for every V0 service. Polyglot deferred until a specific, nameable failur

---
Step 2 — before telemetry, before the DB, before any handler: how does a service read its own config?

Nothing else can be built yet — the DB pool needs a connection string, the telemetry setup needs to know which exporter to use, the HTTP server needs to know which port. All of it comes from somewhere.
Decide that mechanism now.

Aim. What does this mechanism need to guarantee, and why does it have to exist before anly: what would go wrong if you started writing the DB pool or the telemetry setup first,and just called os.Getenv inline wherever you needed a value?

Architecture decision. The project's stated philosophy is "every operational knob is an environment variable, because incidents get injected by changing config and restarting." Given that, do you reach
for a config library (Viper, envconfig, struct tags + reflection), or hand-write a small per type (String, Int, Duration...)? What does the scale of this project (3 services,maybe 30-40 total knobs) do to that calculus, versus if this were a 50-service company?

Tech stack. Same rule as before — justify against "no infrastructure without a demonstrated requirement." Does reaching for a config library pass that test here?

Low-level decisions — this is the one with real judgment in it. Three situations can happen when reading a config value:
- (a) the variable is unset, but there's a sane default
- (b) the variable is set, but malformed (e.g., DB_MAX_CONNS=banana)
- (c) the variable is genuinely required, with no safe default at all (e.g., a database

Should all three be handled the same way? What should happen in each case — silently falsh the process? Argue it from the project's own goal: you're going to be deliberatelymisconfiguring this system to cause incidents. What does that requirement do to how you'd handle case (b) specifically?

✻ Churned for 53s

※ recap: You're building a breakable Go microservices testbed (V0 done: order/payment/inventory + Postgres + OTel) to learn distributed-systems failure modes for SDE2 interviews. We're doing a Socratic walkthrough of every design decision from scratch; next up is Step 2, config strategy (envx package).