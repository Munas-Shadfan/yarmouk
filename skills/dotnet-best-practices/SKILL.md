---
name: dotnet-best-practices
description: 'Ensure .NET/C# code meets best practices for the solution/project.'
---

# .NET/C# Best Practices

Your task is to ensure .NET/C# code in ${selection} follows modern, production-grade best practices.

Focus on correctness, maintainability, security, observability, performance, and testability.

---

## 1) Architecture & Boundaries

- Keep clear module boundaries (API/Application/Domain/Infrastructure).
- Enforce separation of concerns:
	- API layer: HTTP contracts, auth, transport mapping.
	- Application layer: orchestration/use-cases (commands/queries/handlers).
	- Domain layer: business rules and invariants.
	- Infrastructure layer: persistence, external services, implementation details.
- Prefer explicit interfaces for external dependencies (`IStorageProvider`, `IEmailSender`, etc.).
- Keep handlers/services focused and cohesive; avoid “god classes.”

## 2) DI, Configuration & Startup Safety

- Use constructor injection (primary constructors are fine).
- Register lifetimes correctly:
	- `Singleton`: stateless/shared services.
	- `Scoped`: request/db-context scoped services.
	- `Transient`: lightweight stateless utilities when needed.
- Use strongly typed options and validate at startup:
	- `Bind(...)`
	- `ValidateDataAnnotations()`
	- `ValidateOnStart()`
- Fail fast on missing/invalid critical config (DB, auth keys, Redis, storage).

## 3) Validation & Error Handling

- Validate inputs close to boundaries (API validators + command validation).
- Return structured failures (validation/business/authorization/not-found), not opaque exceptions.
- Throw exceptions only for exceptional/unexpected failures.
- Use centralized exception handling middleware for consistent error responses.
- Log errors with context, but never leak secrets or sensitive values.

## 4) Async, Cancellation & Concurrency

- Use async end-to-end for I/O.
- Pass `CancellationToken` through every async call chain.
- Avoid blocking calls (`.Result`, `.Wait()`).
- Ensure streams and disposable resources are correctly handled.

## 5) Persistence (EF Core / SQL)

- Keep domain invariants in domain models, not just in controllers.
- Use explicit migrations; avoid runtime schema mutation in production paths.
- Use proper indexes and keys for query patterns.
- Keep queries purposeful and avoid accidental N+1 patterns.
- Parameterize SQL and avoid string-concatenated SQL commands.

## 6) Security Best Practices

- Enforce authentication and authorization by default.
- Use strong token signing and secure key management.
- Validate uploaded files by both MIME type and signature (magic bytes).
- Sanitize file names/paths and scope storage keys by tenant/context.
- Never log credentials, tokens, private keys, or PII unnecessarily.

## 7) Resilience & External Integrations

- Add retries with exponential backoff for transient failures (storage/network).
- Add health checks for critical dependencies (DB, cache, storage).
- Prefer idempotent operations where possible.
- Consider circuit breakers/timeouts for unstable dependencies.

## 8) Logging, Tracing & Metrics

- Use structured logging with meaningful properties.
- Correlate logs across request boundaries (correlation/request IDs).
- Add distributed tracing and metrics (OpenTelemetry).
- Exclude noisy endpoints (like health probes) from tracing when appropriate.

## 9) Testing Strategy

- Use xUnit + FluentAssertions by default (or existing project standard).
- Test pyramid:
	- Unit tests for domain and handler logic.
	- Integration tests for API + DB + infrastructure wiring.
- Cover both success and failure cases.
- Keep tests deterministic and isolated.
- Use fakes/mocks for external services when testing business logic.

## 10) API & Contract Quality

- Keep request/response contracts explicit and version-aware when needed.
- Return appropriate HTTP status codes.
- Document APIs with OpenAPI.
- Avoid breaking changes without clear migration/versioning strategy.

## 11) Code Quality Standards

- Prefer clear names over clever code.
- Keep methods small and single-purpose.
- Remove dead code and duplicated logic.
- Use nullable reference types correctly.
- Add XML docs for public APIs where it improves maintainability.

## 12) Performance Guidance

- Measure before optimizing.
- Minimize allocations in hot paths.
- Batch/chunk large operations where appropriate.
- Avoid unnecessary serialization/deserialization and repeated mapping work.

---

## Practical Defaults for This Workspace

When working on this backend, prefer:

- .NET 10 + modern C# language features.
- Vertical-slice modules with MediatR command/query handlers.
- EF Core + PostgreSQL with explicit migrations.
- Serilog + OpenTelemetry for observability.
- xUnit + FluentAssertions for tests.
- Strongly-typed options with startup validation.

If an existing project convention conflicts with a generic best practice, follow the project convention unless it introduces clear risk.

