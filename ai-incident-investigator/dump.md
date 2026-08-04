 /model
  ⎿  Set model to Opus 5 and saved as your default for new sessions

❯ /effort auto
  ⎿  Effort level set to auto

❯ okay, so starting with a personal project with the plan in @plan.md , the aim is to have a solid project as a 4 yo backend engieneer, upskilling to grab sde2 jobs at the best product organisations.
Read plan.md (359 lines)

  Ran 2 shell commands

Repo's empty (no commits yet), just plan.md. Toolchains available: Go 1.24, Java 25, Python 3.14, Node 24, Docker + Compose, kubectl (no kind/helm yet).

Two forks I don't want to guess on, since both change everything downstream:

⏺ User answered Claude's questions:
· What language should the microservices (order/payment/user/notification) be written in? → Go
· How do you want us to divide the work? The plan's whole thesis is that *you* learn by breaking things — so me writing all of it defeats the point. → not sure, what would be the best?

Go it is. On working mode — let me just recommend rather than survey:

Pair mode, with one hard rule: I never run an incident for you.

I'll write the plumbing (Compose, OTel wiring, Dockerfiles, DB setup) because there's zero interview value in you hand-typing otel.SetTracerProvider. But every failure injection, every "why did it do that", and every postmortem in docs/incidents/ is yours. That's where the actual signal is — nobody asks "did you write the Dockerfile", they ask "why did retries make it worse."

Starting V0 now, honoring the plan's "start boring" constraint: 3 Go services + Postgres + Compose + OTel to stdout. No Prometheus, no Tempo, no k8s yet — you'll feel the pain of correlating JSON in stdout, and that pain is what justifies the next component.

  Ran 1 shell command

❯ @tech-stack-decision.md has more details about what i want to do, your suggestions are welcome too

  Read 1 file

Read it. It largely matches what I've started — here are the deltas I'm applying, plus three suggestions:

Applying from your doc: services are order / payment / inventory (dropping my user-service), k6 for load (run via Docker image, nothing to install), Postgres primary.

Three calls I'd make differently, and why:

1. Redis holds until Phase 1.5. Your Phase 1 list includes it, but there's no problem it solves yet — that violates your own "don't introduce infra you can't justify" rule. It earns its place the moment you add a payment idempotency store or hit a hot-key read path. Then "Redis failure → thundering herd on Postgres" becomes a real incident instead of a prop.
2. No API Gateway yet. Same reason. It gets justified when you add rate limiting (which is incident #14 in your catalogue anyway). order-service is the entry point for now.
3. All-Go for V0; convert exactly one service to Java/Spring later. Polyglot on day one is drag. Converting inventory-service to Spring Boot in Phase 2 buys you two real things: JVM-specific failure modes (heap OOM, GC pause, HikariCP exhaustion — different from Go's) and a live demonstration that W3C trace context propagates across languages. That's a defensible reason to be polyglot; "three languages on the README" isn't.

Building V0 now.

  Ran 2 shell commands

Now the platform layer.

⏺ Write(internal/platform/envx/envx.go)
Wrote 90 lines to internal/platform/envx/envx.go
// Package envx reads configuration from the process environment.
//
// Every operational knob in this project is an environment variable on purpose.
// Most real incidents start as a configuration change that ships with a
// deployment, so being able to break a service by editing one line of Compose
// and restarting it is the whole point of the testbed.
package envx

import (
  "log/slog"
… +80 lines

⏺ Write(internal/platform/telemetry/telemetry.go)
Wrote 184 lines to internal/platform/telemetry/telemetry.go
// Package telemetry wires the OpenTelemetry SDK for every service.
//
// V0 deliberately exports to stdout. There is no collector, no Prometheus and
// no Tempo yet, because we have not yet hit the problem those systems solve.
// Flip OTEL_EXPORTER to "otlp" once a collector exists; no service code changes.
package telemetry

import (
  "context"
  "errors"
… +174 lines

⏺ Write(internal/platform/telemetry/logging.go)
Wrote 53 lines to internal/platform/telemetry/logging.go
package telemetry

import (
  "context"
  "log/slog"
  "os"

  "go.opentelemetry.io/otel/trace"
)
… +43 lines

⏺ Write(internal/platform/httpx/server.go)
Wrote 56 lines to internal/platform/httpx/server.go
package httpx

import (
  "net/http"
  "time"

  "github.com/aks151boson/ai-incident-investigator/internal/platform/envx"
  "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
)
… +46 lines

⏺ Write(internal/platform/httpx/client.go)
Wrote 62 lines to internal/platform/httpx/client.go
package httpx

import (
  "net"
  "net/http"
  "time"

  "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
)
… +52 lines

⏺ Write(internal/platform/httpx/mux.go)
Wrote 77 lines to internal/platform/httpx/mux.go
package httpx

import (
  "log/slog"
  "net/http"
  "time"

  "go.opentelemetry.io/otel/attribute"
  "go.opentelemetry.io/otel/trace"
)
… +67 lines

⏺ Write(internal/platform/httpx/respond.go)
Wrote 56 lines to internal/platform/httpx/respond.go
package httpx

import (
  "encoding/json"
  "errors"
  "io"
  "net/http"

  "go.opentelemetry.io/otel/codes"
  "go.opentelemetry.io/otel/trace"
… +46 lines

Now the DB layer — this is where incident #07's telemetry gets built in from day one.

⏺ Write(internal/platform/db/db.go)
Wrote 102 lines to internal/platform/db/db.go
// Package db owns the PostgreSQL connection pool and its telemetry.
//
// The pool is the most instructive component in the whole testbed. It is a
// bounded queue sitting between the service and the database, and almost every
// "the database is slow" incident is really "we ran out of connections and
// requests are queueing for one".
package db

import (
  "context"
… +92 lines

⏺ Write(internal/platform/db/metrics.go)
Wrote 97 lines to internal/platform/db/metrics.go
package db

import (
  "context"

  "github.com/jackc/pgx/v5/pgxpool"
  "go.opentelemetry.io/otel"
  "go.opentelemetry.io/otel/metric"
)
… +87 lines

That pending metric was drafted wrong — pgxpool doesn't expose a waiter count. Fixing it honestly rather than faking it:

⏺ Update(internal/platform/db/metrics.go)
Added 6 lines, removed 4 lines
  if err != nil {
    return err
  }
  // A non-zero value here means goroutines are blocked waiting for a
  // connection right now. It is the earliest signal of pool exhaustion.
  pending, err := meter.Int64ObservableUpDownCounter("db.pool.acquire.pending",
    metric.WithDescription("Callers currently blocked waiting for a connection"))
  // pgxpool does not expose a "callers currently blocked" gauge, so
  // saturation has to be inferred: acquired == max, plus a rising
  // db.pool.acquire.empty rate, means requests are queueing for connections.
  // Worth knowing that the obvious metric you want does not always exist.
  constructing, err := meter.Int64ObservableUpDownCounter("db.pool.connections.constructing",
    metric.WithDescription("Connections currently being established"))
  if err != nil {
    return err
  }

⏺ Update(internal/platform/db/metrics.go)
Added 2 lines, removed 7 lines
      o.ObserveInt64(idle, int64(s.IdleConns()))
      o.ObserveInt64(total, int64(s.TotalConns()))
      o.ObserveInt64(maxConns, int64(s.MaxConns()))
      o.ObserveInt64(pending, s.EmptyAcquireWaitTime().Nanoseconds()/1e9*0+int64(s.NewConnsCount())*0+pendingCount(s))
      o.ObserveInt64(constructing, int64(s.ConstructingConns()))
      o.ObserveInt64(acquireCount, s.AcquireCount())
      o.ObserveInt64(emptyAcquire, s.EmptyAcquireCount())
      o.ObserveInt64(canceledAcquire, s.CanceledAcquireCount())
      o.ObserveFloat64(acquireDuration, s.AcquireDuration().Seconds())
      return nil
    },
    acquired, idle, total, maxConns, pending,
    acquired, idle, total, maxConns, constructing,
    acquireCount, emptyAcquire, canceledAcquire, acquireDuration,
  )
  return err
}

// pendingCount reports how many callers are blocked waiting for a connection.
func pendingCount(s *pgxpool.Stat) int64 {
  return int64(s.ConstructingConns())
}

⏺ Write(internal/platform/app/app.go)
Wrote 121 lines to internal/platform/app/app.go
// Package app boots a service: config, telemetry, database, HTTP server and
// graceful shutdown. Each cmd/ main stays small enough to read in one screen.
package app

import (
  "context"
  "errors"
  "log/slog"
  "net/http"
  "os"
… +111 lines

⏺ Write(internal/platform/app/health.go)
Wrote 48 lines to internal/platform/app/health.go
package app

import (
  "context"
  "net/http"
  "time"

  "github.com/aks151boson/ai-incident-investigator/internal/platform/httpx"
)
… +38 lines

Now the three domain services. Chaos knobs go in a clearly-separated faultx package rather than being smeared through business logic — that boundary matters when you explain this to an interviewer.

⏺ Write(internal/platform/faultx/faultx.go)
Wrote 85 lines to internal/platform/faultx/faultx.go
// Package faultx is testbed scaffolding, not application logic.
//
// It exists so a service can be made slow or unreliable from the environment
// without editing business code. It is deliberately isolated in its own package
// so the boundary between "the application" and "the chaos harness" stays
// obvious to anyone reading the repo.
//
// Most incidents in the catalogue do NOT use this. Pool exhaustion, retry
// storms and cascading timeouts are all producible from real configuration
// (DB_MAX_CONNS, client timeouts, replica counts), and reproducing them that
… +75 lines

⏺ Write(internal/inventory/store.go)
Wrote 139 lines to internal/inventory/store.go
package inventory

import (
  "context"
  "errors"
  "fmt"

  "github.com/aks151boson/ai-incident-investigator/internal/platform/db"
  "github.com/google/uuid"
  "github.com/jackc/pgx/v5"
… +129 lines

⏺ Write(internal/inventory/handler.go)
Wrote 137 lines to internal/inventory/handler.go
package inventory

import (
  "context"
  "errors"
  "log/slog"
  "net/http"

  "github.com/aks151boson/ai-incident-investigator/internal/platform/faultx"
  "github.com/aks151boson/ai-incident-investigator/internal/platform/httpx"
… +127 lines

⏺ Write(internal/payment/store.go)
Wrote 83 lines to internal/payment/store.go
package payment

import (
  "context"
  "fmt"
  "time"

  "github.com/aks151boson/ai-incident-investigator/internal/platform/db"
  "github.com/google/uuid"
)
… +73 lines

⏺ Write(internal/payment/handler.go)
Wrote 120 lines to internal/payment/handler.go
package payment

import (
  "context"
  "errors"
  "log/slog"
  "net/http"
  "time"

  "github.com/aks151boson/ai-incident-investigator/internal/platform/envx"
… +110 lines

⏺ Write(internal/order/store.go)
Wrote 127 lines to internal/order/store.go
package order

import (
  "context"
  "fmt"
  "time"

  "github.com/aks151boson/ai-incident-investigator/internal/platform/db"
  "github.com/google/uuid"
  "github.com/jackc/pgx/v5"
… +117 lines

⏺ Write(internal/order/clients.go)
Wrote 203 lines to internal/order/clients.go
package order

import (
  "bytes"
  "context"
  "encoding/json"
  "fmt"
  "io"
  "math/rand/v2"
  "net/http"
… +193 lines

⏺ Write(internal/order/errors.go)
Wrote 34 lines to internal/order/errors.go
package order

import (
  "errors"
  "fmt"
  "net/http"
)

// statusError carries a downstream service's HTTP status back to the caller so
// the order service can decide whether to retry and what to report upstream.
… +24 lines

⏺ Write(internal/order/handler.go)
Wrote 190 lines to internal/order/handler.go
package order

import (
  "context"
  "errors"
  "log/slog"
  "net/http"
  "time"

  "github.com/aks151boson/ai-incident-investigator/internal/platform/httpx"
… +180 lines

Now the entrypoints, schema, and Compose stack.

⏺ Write(cmd/inventory-service/main.go)
Wrote 22 lines to cmd/inventory-service/main.go
// Command inventory-service tracks stock levels and reservations.
package main

import (
  "context"
  "net/http"

  "github.com/aks151boson/ai-incident-investigator/internal/inventory"
  "github.com/aks151boson/ai-incident-investigator/internal/platform/app"
)
… +12 lines

⏺ Write(cmd/payment-service/main.go)
Wrote 22 lines to cmd/payment-service/main.go
// Command payment-service records charges against orders.
package main

import (
  "context"
  "net/http"

  "github.com/aks151boson/ai-incident-investigator/internal/payment"
  "github.com/aks151boson/ai-incident-investigator/internal/platform/app"
)
… +12 lines

⏺ Write(cmd/order-service/main.go)
Wrote 41 lines to cmd/order-service/main.go
// Command order-service is the checkout entry point. It orchestrates the saga
// across inventory-service and payment-service.
package main

import (
  "context"
  "net/http"
  "time"

  "github.com/aks151boson/ai-incident-investigator/internal/order"
… +31 lines

⏺ Write(deploy/postgres/init.sql)
Wrote 79 lines to deploy/postgres/init.sql
-- Schema for the testbed.
--
-- One Postgres instance, three databases. Separate databases keep the services
-- honest about ownership (no cross-service joins), while the shared instance
-- means they still compete for the same CPU, memory and max_connections --
-- which is realistic, and is the source of several incidents in the catalogue.

CREATE DATABASE orders;
CREATE DATABASE payments;
CREATE DATABASE inventory;
… +69 lines

⏺ Write(deploy/compose/Dockerfile)
Wrote 36 lines to deploy/compose/Dockerfile
# One Dockerfile builds all three services; SERVICE selects the binary.
#
# The build stage is shared, so `docker compose build` downloads modules once
# rather than three times.

FROM golang:1.24-alpine AS build

ARG SERVICE
ARG SERVICE_VERSION=dev
… +26 lines

⏺ Write(deploy/compose/docker-compose.yml)
Wrote 144 lines to deploy/compose/docker-compose.yml
# V0 stack: three Go services, one Postgres, telemetry to stdout.
#
# There is deliberately no Prometheus, Tempo, Loki or collector here yet. Run
# the stack, generate load, break something, and try to diagnose it from
# `docker compose logs`. The frustration of doing that is the justification for
# every component added in V1.

name: incident-testbed

x-service-defaults: &service-defaults
… +134 lines

⏺ Write(loadtest/k6/checkout.js)
Wrote 68 lines to loadtest/k6/checkout.js
// Checkout load profile.
//
// Run it:
//   make load
//   VUS=200 DURATION=3m make load
//   SKU=SKU-HOT VUS=200 make load     # row-lock contention on a single SKU
//
// Read the summary carefully. The number that matters during an incident is
// p99, not avg: a service can hold a perfectly healthy average while a quarter
// of your customers time out.
… +58 lines

Now let me get dependencies resolved and confirm it actually builds.

  Ran 1 shell command

⏺ Update(internal/platform/telemetry/telemetry.go)
Added 1 line, removed 1 line
  "github.com/aks151boson/ai-incident-investigator/internal/platform/envx"
  "go.opentelemetry.io/contrib/instrumentation/runtime"
  "go.opentelemetry.io/otel"
  "go.opentelemetry.io/otel/exporters/otlp/otlpmetricgrpc"
  "go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc"
  "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
  "go.opentelemetry.io/otel/exporters/stdout/stdoutmetric"
  "go.opentelemetry.io/otel/exporters/stdout/stdouttrace"

  Ran 1 shell command

Builds clean, vet clean. But note a dependency pulled in a newer toolchain — that affects the Dockerfile:

  Read 1 file

⏺ Update(deploy/compose/Dockerfile)
Added 1 line, removed 1 line
# The build stage is shared, so `docker compose build` downloads modules once
# rather than three times.

FROM golang:1.24-alpine AS build
FROM golang:1.25-alpine AS build

ARG SERVICE
ARG SERVICE_VERSION=dev

⏺ Write(Makefile)
Wrote 61 lines to Makefile
COMPOSE := docker compose -f deploy/compose/docker-compose.yml

.DEFAULT_GOAL := help

## help: list targets
help:
  @grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## //' | awk -F': ' '{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

## build: compile all services locally
build:
… +51 lines

⏺ Write(.gitignore)
Wrote 5 lines to .gitignore
bin/
*.exe
.env
.DS_Store
coverage.out

Let me bring the stack up and verify it actually works end to end.

  Ran 1 shell command

Docker daemon isn't running — I'll need you to start Docker Desktop before we can bring the stack up. Meanwhile, let me finish the docs and tests.

⏺ Write(README.md)
Wrote 122 lines to README.md
# ai-incident-investigator

A deliberately breakable distributed system, and an engine that investigates it.

There are two projects in this repository, and the split is intentional:

1. **The testbed** — a small e-commerce checkout flow (`order` → `inventory` → `payment`)
   that can be broken in reproducible, documented ways.
2. **The investigator** — a service that collects evidence from telemetry, builds an
   incident timeline deterministically, and only then asks a model to reason about it.
… +112 lines

⏺ Write(docs/incidents/README.md)
Wrote 51 lines to docs/incidents/README.md
# Incident catalogue

Fifteen failure modes, each one reproducible on demand. This is the input to
everything that follows: without repeatable incidents there is nothing to evaluate an
investigator against.

## The rules

1. **Predict first.** Before injecting anything, write down what you expect to see in
   metrics, traces and logs. Put it in the postmortem under *Prediction*.
… +41 lines

⏺ Write(docs/incidents/TEMPLATE.md)
Wrote 66 lines to docs/incidents/TEMPLATE.md
# INCIDENT NN — <name>

- **Date run:** YYYY-MM-DD
- **Stack version:** V0 / V1 / …
- **Injected by:** exact command or config diff

## Prediction

*Write this BEFORE injecting anything. Do not edit it afterwards.*
… +56 lines

⏺ Write(docs/decisions/0001-single-go-module-monorepo.md)
Wrote 34 lines to docs/decisions/0001-single-go-module-monorepo.md
# 0001 — One Go module, several binaries

**Status:** accepted · **Date:** 2026-08-02

## Context

Three services need to share telemetry setup, HTTP client/server construction and
database pooling. The alternatives were one module per service (each with its own
`go.mod`), or a single module with multiple `cmd/` entrypoints.
… +24 lines

⏺ Write(docs/decisions/0002-telemetry-to-stdout-first.md)
Wrote 36 lines to docs/decisions/0002-telemetry-to-stdout-first.md
# 0002 — Telemetry goes to stdout in V0

**Status:** accepted · **Date:** 2026-08-02

## Context

The obvious move is to stand up the OpenTelemetry Collector, Prometheus, Tempo, Loki
and Grafana on day one. The stack is well documented and would take an afternoon.

## Decision
… +26 lines

⏺ Write(docs/decisions/0003-deferred-infrastructure.md)
Wrote 41 lines to docs/decisions/0003-deferred-infrastructure.md
# 0003 — Deferred infrastructure, and what will unblock each piece

**Status:** accepted · **Date:** 2026-08-02

## Context

The target architecture includes Redis, Kafka, Kubernetes, an API gateway and a
polyglot service. Introducing them now is the fastest way to end up unable to answer
"why is this here?" in an interview.
… +33 lines

Now some tests worth having — the retry policy is the part most likely to be subtly wrong.

⏺ Write(internal/order/clients_test.go)
Wrote 154 lines to internal/order/clients_test.go
package order

import (
  "context"
  "errors"
  "net/http"
  "net/http/httptest"
  "sync/atomic"
  "testing"
  "time"
… +144 lines

⏺ Write(internal/platform/faultx/faultx_test.go)
Wrote 56 lines to internal/platform/faultx/faultx_test.go
package faultx

import (
  "context"
  "errors"
  "testing"
  "time"
)

func TestZeroInjectorIsNoOp(t *testing.T) {
… +46 lines

  Ran 1 shell command

Tests pass, gofmt and vet clean. Let me check if Docker is up yet.

  Ran 1 shell command

Docker's up now. Bringing the stack online:

  Ran 1 shell command

Port 5432 is already taken on your machine — something else is running there:

  Ran 1 shell command

You have a native Postgres on 5432. I won't touch it — making the host port configurable instead, defaulting to 55432:

⏺ Update(deploy/compose/docker-compose.yml)
Added 4 lines, removed 1 line
      - -c
      - log_min_duration_statement=500ms
    ports:
      - "5432:5432"
      # 55432 by default so this never fights a Postgres you already run
      # natively on 5432. Services reach it as postgres:5432 on the Compose
      # network regardless; this mapping is only for psql/GUI clients.
      - "${POSTGRES_HOST_PORT:-55432}:5432"
    volumes:
      - ../postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
      - postgres-data:/var/lib/postgresql/data

  Ran 1 shell command

All four containers up. Now the real test — does a checkout actually work end to end?

  Ran 1 shell command

Checkout works. Now the critical correctness check — does one trace actually span all three services?

  Ran 1 shell command

W3C trace context propagates cleanly across all three services. Let me confirm the span tree has the depth we need — including SQL spans:

  Ran 2 shell commands

Found a real bug: OTEL_METRIC_EXPORT_INTERVAL is a reserved OTel SDK variable that expects integer milliseconds, not a Go duration — the SDK logs a parse error on it. I'm shadowing a spec'd name with an incompatible format. Renaming to avoid the collision:

⏺ Update(internal/platform/telemetry/telemetry.go)
Added 10 lines, removed 4 lines
    ServiceName:    serviceName,
    ServiceVersion: envx.String("SERVICE_VERSION", "dev"),
    Environment:    envx.String("ENVIRONMENT", "local"),
    Exporter:       envx.String("OTEL_EXPORTER", "stdout"),
    Endpoint:       envx.String("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-collector:4317"),
    SampleRatio:    envx.Float("OTEL_TRACES_SAMPLER_ARG", 1.0),
    MetricInterval: envx.Duration("OTEL_METRIC_EXPORT_INTERVAL", 15*time.Second),
    Exporter: envx.String("OTEL_EXPORTER", "stdout"),
    Endpoint: envx.String("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-collector:4317"),
    // These two use project-local names rather than OTEL_TRACES_SAMPLER_ARG
    // and OTEL_METRIC_EXPORT_INTERVAL on purpose. Those are reserved by the
    // OTel spec and the SDK parses them itself with different formats --
    // the interval is integer milliseconds there, not a Go duration -- so
    // reusing the names produces confusing parse warnings and a value that
    // silently disagrees with what the SDK thinks it is.
    SampleRatio:    envx.Float("TRACE_SAMPLE_RATIO", 1.0),
    MetricInterval: envx.Duration("METRIC_EXPORT_INTERVAL", 15*time.Second),
  }
}


⏺ Update(deploy/compose/docker-compose.yml)
Added 6 lines, removed 2 lines
    # no service code changes required.
    OTEL_EXPORTER: ${OTEL_EXPORTER:-stdout}
    OTEL_EXPORTER_OTLP_ENDPOINT: ${OTEL_EXPORTER_OTLP_ENDPOINT:-otel-collector:4317}
    OTEL_METRIC_EXPORT_INTERVAL: ${OTEL_METRIC_EXPORT_INTERVAL:-15s}
    OTEL_TRACES_SAMPLER_ARG: ${OTEL_TRACES_SAMPLER_ARG:-1.0}
    # Project-local names: the OTEL_-prefixed equivalents are reserved by the
    # spec and parsed differently by the SDK itself.
    METRIC_EXPORT_INTERVAL: ${METRIC_EXPORT_INTERVAL:-15s}
    # Keep at 1.0 while reproducing incidents; sampling away the failing
    # requests is a great way to make an incident invisible.
    TRACE_SAMPLE_RATIO: ${TRACE_SAMPLE_RATIO:-1.0}

services:
  postgres:

  Ran 1 shell command

Parse warning gone. Let me look at the raw span output directly rather than through my filter:

  Ran 1 shell command

Span tree is exactly what we need. Let me verify the order-service side and the pool metrics:

  Ran 1 shell command

Everything's wired. One polish worth doing — client spans are named HTTP POST, which is useless when reading a trace. Let me name them by dependency:

⏺ Update(internal/platform/httpx/client.go)
Added 4 lines
//   - Timeout too low   -> healthy-but-slow requests get retried, amplifying load.
//   - MaxConnsPerHost   -> a client-side queue nobody knows exists until it fills.
type ClientConfig struct {
  // Name identifies the dependency in client span names. Without it every
  // outbound call is called "HTTP POST", which makes a trace with three
  // dependencies unreadable at exactly the moment you need to read it.
  Name                string
  Timeout             time.Duration
  MaxIdleConns        int
  MaxIdleConnsPerHost int

⏺ Update(internal/platform/httpx/client.go)
Added 4 lines, removed 2 lines
  DialTimeout         time.Duration
}

// DefaultClientConfig returns sane starting values for service-to-service calls.
func DefaultClientConfig(timeout time.Duration) ClientConfig {
// DefaultClientConfig returns sane starting values for calls to the named
// dependency.
func DefaultClientConfig(name string, timeout time.Duration) ClientConfig {
  return ClientConfig{
    Name:                name,
    Timeout:             timeout,
    MaxIdleConns:        100,
    MaxIdleConnsPerHost: 100,

⏺ Update(internal/platform/httpx/client.go)
Added 9 lines, removed 2 lines
  }

  return &http.Client{
    Timeout:   cfg.Timeout,
    Transport: otelhttp.NewTransport(transport),
    Timeout: cfg.Timeout,
    Transport: otelhttp.NewTransport(transport,
      otelhttp.WithSpanNameFormatter(func(_ string, r *http.Request) string {
        if cfg.Name == "" {
          return r.Method + " " + r.URL.Path
        }
        return r.Method + " " + cfg.Name + r.URL.Path
      }),
    ),
  }
}

⏺ Update(internal/order/clients.go)
Added 1 line, removed 1 line
  return &Downstream{
    name:    name,
    baseURL: baseURL,
    client:  httpx.NewClient(httpx.DefaultClientConfig(timeout)),
    client:  httpx.NewClient(httpx.DefaultClientConfig(name, timeout)),
    retry:   retry,
  }
}

  Ran 1 shell command

Client spans now read properly. gofmt flagged my telemetry edit — fixing:

  Ran 1 shell command

Let me verify the load harness works end to end with a short run:

  Ran 1 shell command

Full loop verified: 13,318 checkouts, 0 failures, p95 31.8ms, ~665 rps. That's your V0 baseline.

Let me save the working agreement and context, since neither is derivable from the repo.

  Listed 1 directory, wrote 3 memories

V0 is up and verified. Stack is still running — make ps to confirm, make down when you're done.

What exists

cmd/{order,payment,inventory}-service/   ~30-line entrypoints
internal/
  order/       checkout saga, downstream clients, retry policy
  inventory/   stock, reservations, compensation (release)

