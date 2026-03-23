---
name: domain-agent
description: |
  Use when working on custom domain provisioning for a multi-tenant / Shopify-style platform.
  Triggers on: "custom domain", "domain agent", "attach domain", "nginx config", "certbot SSL",
  "tenant routing", "domain provisioning", "merchant domain", "store domain", "host header routing",
  "domain-agent API", "domain agent .NET", "point domain to store", "SSL automation",
  "domain webhook", "CALLBACK_URL", "domain status callback", "nginx multi-tenant".
  Covers the full contract between the .NET API and the Python domain agent:
  request/response shapes, DB schema, C# service class, callback handler, error handling,
  and the nginx host-routing model.
metadata:
  version: 1.0.0
---

# Domain Agent Skill

Aqlaan runs a **Python FastAPI service** (the _domain agent_) on the host OS.
Your **.NET API** calls it to provision custom merchant domains — nginx config, DNS check, SSL — without touching the host directly.

---

## Architecture

```
Merchant UI
    │  POST /api/domains/attach  { domain, storeId }
    ▼
.NET API  ──────────────────────────────────────────────────────►  Domain Agent  (127.0.0.1:8100)
  • saves domain row (status=pending)                               POST /domains
  • calls domain agent                                              • validates A record
  • returns 202 immediately                                         • writes nginx config
                                                                    • reloads nginx  ◄── nginx live in ~1 s
                                                                    • issues SSL async (certbot ~60 s)
                                                                    • POSTs callback to .NET when done
    ◄──────────────────────────────────────────────────────────────
  POST /internal/domain-ready  { domain, store_id, status, ssl_status, expiry }
  • updates domain row (status=active, ssl_status=active)
  • notifies merchant if you want
    │
    ▼
nginx:  store.example.com → storefront app (Host header unchanged)
    │
    ▼
Storefront app:  reads Host header → looks up store in DB → renders correct tenant
```

---

## Domain Agent Base URL & Auth

```
Base URL  : http://127.0.0.1:8100   (localhost only — never exposed publicly)
Auth      : X-Webhook-Secret: <DOMAIN_AGENT_SECRET>   (shared secret, set in .env)
```

Add to your .NET `appsettings.json` / secrets:
```json
{
  "DomainAgent": {
    "BaseUrl": "http://127.0.0.1:8100",
    "Secret":  "<same value as DOMAIN_AGENT_SECRET on the host>"
  }
}
```

---

## API Contract

### `POST /domains` — Provision a domain

**Request:**
```json
{
  "domain":            "store.example.com",
  "slug":              "my-store",
  "store_id":          "b3d9f1a2-...",
  "frontend_upstream": "127.0.0.1:3000",
  "revoke_on_delete":  false
}
```

| Field               | Type     | Required | Notes                                              |
|---------------------|----------|----------|----------------------------------------------------|
| `domain`            | string   | ✅       | Full domain, e.g. `store.example.com`              |
| `slug`              | string   | ✅       | Kebab-case store slug, used in nginx upstream name |
| `store_id`          | string   | optional | Your DB GUID/int — echoed back in callback         |
| `frontend_upstream` | string   | optional | `host:port` of storefront app. Falls back to `FRONTEND_UPSTREAM` env var |
| `revoke_on_delete`  | bool     | optional | Revoke cert when domain is deleted (default false) |

**Response (202-style — nginx is live, SSL is async):**
```json
{
  "ok":      true,
  "message": "store.example.com provisioned. status=ssl_pending ssl=pending",
  "data": {
    "store_id":    "b3d9f1a2-...",
    "status":      "ssl_pending",
    "ssl_status":  "pending",
    "tls":         "pending",
    "a_record":    "ok",
    "resolved_ip": "1.2.3.4",
    "required_ip": "1.2.3.4",
    "upstream":    "127.0.0.1:3000"
  }
}
```

**Failure (DNS not pointing to server):**
```json
{
  "ok":      false,
  "message": "A record for store.example.com points to 9.9.9.9, expected 1.2.3.4. Update DNS and retry.",
  "data":    {}
}
```

---

### `GET /domains/{domain}` — Status

**Response:**
```json
{
  "domain":      "store.example.com",
  "slug":        "my-store",
  "store_id":    "b3d9f1a2-...",
  "status":      "active",
  "ssl_status":  "active",
  "conf_exists": true,
  "ssl_active":  true,
  "ssl_expiry":  "2026-06-15T12:00:00+00:00",
  "a_record":    "ok",
  "resolved_ip": "1.2.3.4",
  "required_ip": "1.2.3.4",
  "created_at":  "2026-03-16T10:00:00+00:00",
  "verified_at": "2026-03-16T10:00:05+00:00",
  "updated_at":  "2026-03-16T10:01:10+00:00"
}
```

**Status values:**

| `status`      | Meaning                                              |
|---------------|------------------------------------------------------|
| `ssl_pending` | nginx live, SSL cert being issued in background      |
| `active`      | fully live with valid SSL                            |
| `ssl_failed`  | nginx live but certbot failed — check DNS + logs     |
| `unknown`     | domain not managed by agent                         |

| `ssl_status` | Meaning                       |
|--------------|-------------------------------|
| `pending`    | certbot running               |
| `active`     | cert issued and valid         |
| `failed`     | certbot error                 |
| `none`       | TLS disabled (dev/staging)    |

---

### `PUT /domains/{domain}` — Update upstream or slug

```json
{ "slug": "new-slug", "frontend_upstream": "127.0.0.1:3001" }
```

---

### `DELETE /domains/{domain}` — Deprovision

```
DELETE /domains/store.example.com
DELETE /domains/store.example.com?revoke=true   ← also revokes cert
```

---

### `POST /domains/{domain}/ssl` — Re-issue SSL

Safe to retry. Call this if initial SSL failed.

---

### `POST /ssl/renew-all` — Renew all certs

Call from a Hangfire recurring job every 12 hours.

---

### `GET /health` — Liveness probe

No auth required. Returns `{ "status": "ok", "managed": 3 }`.

---

## Callback Webhook (.NET receives this)

When async SSL completes, the agent POSTs to your `.NET` API:

**Headers:** `X-Agent-Secret: <CALLBACK_SECRET>`  
**Body:**
```json
{
  "domain":     "store.example.com",
  "store_id":   "b3d9f1a2-...",
  "status":     "active",
  "ssl_status": "active",
  "tls":        "issued",
  "expiry":     "2026-06-15T12:00:00+00:00",
  "upstream":   "127.0.0.1:3000"
}
```

Configure in the host `.env`:
```
CALLBACK_URL=http://127.0.0.1:5000/internal/domain-ready
CALLBACK_SECRET=your-shared-secret
```

---

## .NET DB Table

```sql
CREATE TABLE CustomDomains (
    Id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    StoreId      UUID         NOT NULL REFERENCES Stores(Id),
    Domain       VARCHAR(253) NOT NULL UNIQUE,
    Status       VARCHAR(20)  NOT NULL DEFAULT 'pending',   -- pending | ssl_pending | active | ssl_failed | removed
    SslStatus    VARCHAR(20)  NOT NULL DEFAULT 'none',      -- none | pending | active | failed
    SslExpiry    TIMESTAMPTZ,
    VerifiedAt   TIMESTAMPTZ,
    CreatedAt    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UpdatedAt    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

EF Core entity:
```csharp
public class CustomDomain
{
    public Guid   Id        { get; set; }
    public Guid   StoreId   { get; set; }
    public string Domain    { get; set; } = "";
    public string Status    { get; set; } = "pending";     // pending | ssl_pending | active | ssl_failed | removed
    public string SslStatus { get; set; } = "none";
    public DateTime? SslExpiry   { get; set; }
    public DateTime? VerifiedAt  { get; set; }
    public DateTime  CreatedAt   { get; set; } = DateTime.UtcNow;
    public DateTime  UpdatedAt   { get; set; } = DateTime.UtcNow;
    public Store  Store    { get; set; } = null!;
}
```

---

## .NET C# Service

```csharp
// DomainAgentService.cs
public class DomainAgentService(HttpClient http, IConfiguration config)
{
    // ── Provision ──────────────────────────────────────────────────────────────
    public async Task<DomainAgentResult> ProvisionAsync(
        string domain, string slug, Guid storeId,
        string? upstream = null,
        CancellationToken ct = default)
    {
        var payload = new
        {
            domain,
            slug,
            store_id          = storeId.ToString(),
            frontend_upstream = upstream,
            revoke_on_delete  = false,
        };

        var res = await http.PostAsJsonAsync("/domains", payload, ct);
        var body = await res.Content.ReadFromJsonAsync<AgentResponse>(ct)
                   ?? throw new InvalidOperationException("Empty response from domain agent");

        return new DomainAgentResult(body.Ok, body.Message, body.Data);
    }

    // ── Status ──────────────────────────────────────────────────────────────────
    public async Task<DomainStatus?> GetStatusAsync(string domain, CancellationToken ct = default)
    {
        var res = await http.GetAsync($"/domains/{domain}", ct);
        if (res.StatusCode == System.Net.HttpStatusCode.NotFound) return null;
        res.EnsureSuccessStatusCode();
        return await res.Content.ReadFromJsonAsync<DomainStatus>(ct);
    }

    // ── Delete ──────────────────────────────────────────────────────────────────
    public async Task DeleteAsync(string domain, bool revokeCert = false, CancellationToken ct = default)
    {
        var url = revokeCert ? $"/domains/{domain}?revoke=true" : $"/domains/{domain}";
        var res = await http.DeleteAsync(url, ct);
        res.EnsureSuccessStatusCode();
    }

    // ── Re-issue SSL ─────────────────────────────────────────────────────────────
    public async Task ReissueSslAsync(string domain, CancellationToken ct = default)
    {
        var res = await http.PostAsync($"/domains/{domain}/ssl", null, ct);
        res.EnsureSuccessStatusCode();
    }

    // ── Renew all ────────────────────────────────────────────────────────────────
    public async Task RenewAllSslAsync(CancellationToken ct = default)
    {
        var res = await http.PostAsync("/ssl/renew-all", null, ct);
        res.EnsureSuccessStatusCode();
    }
}

// DTOs
public record AgentResponse(bool Ok, string Message, JsonElement? Data);
public record DomainStatus(
    string  Domain,
    string  Slug,
    string  StoreId,
    string  Status,
    string  SslStatus,
    bool    ConfExists,
    bool    SslActive,
    string? SslExpiry,
    string  ARecord,
    string? ResolvedIp,
    string  RequiredIp,
    string? CreatedAt,
    string? VerifiedAt,
    string? UpdatedAt
);
public record DomainAgentResult(bool Ok, string Message, JsonElement? Data);
```

Register in `Program.cs`:
```csharp
builder.Services.AddHttpClient<DomainAgentService>(c =>
{
    c.BaseAddress = new Uri(builder.Configuration["DomainAgent:BaseUrl"]!);
    c.DefaultRequestHeaders.Add("X-Webhook-Secret", builder.Configuration["DomainAgent:Secret"]);
    c.Timeout = TimeSpan.FromSeconds(30); // SSL is async — no need for long timeout
});
```

---

## .NET Callback Endpoint

```csharp
// Controllers/Internal/DomainReadyController.cs
[ApiController]
[Route("internal")]
public class DomainReadyController(AppDbContext db, IConfiguration config) : ControllerBase
{
    [HttpPost("domain-ready")]
    public async Task<IActionResult> Handle(
        [FromHeader(Name = "X-Agent-Secret")] string secret,
        [FromBody] DomainReadyPayload payload,
        CancellationToken ct)
    {
        var expected = config["DomainAgent:CallbackSecret"] ?? "";
        if (!CryptographicOperations.FixedTimeEquals(
                System.Text.Encoding.UTF8.GetBytes(secret),
                System.Text.Encoding.UTF8.GetBytes(expected)))
            return Unauthorized();

        var domain = await db.CustomDomains
            .FirstOrDefaultAsync(d => d.Domain == payload.Domain, ct);

        if (domain is null) return NotFound();

        domain.Status    = payload.Status;
        domain.SslStatus = payload.SslStatus;
        domain.SslExpiry = payload.Expiry is not null
            ? DateTime.Parse(payload.Expiry, null, System.Globalization.DateTimeStyles.RoundtripKind)
            : null;
        domain.UpdatedAt = DateTime.UtcNow;
        if (payload.Status == "active")
            domain.VerifiedAt ??= DateTime.UtcNow;

        await db.SaveChangesAsync(ct);
        return Ok();
    }
}

public record DomainReadyPayload(
    string  Domain,
    string  StoreId,
    string  Status,
    string  SslStatus,
    string  Tls,
    string? Expiry,
    string  Upstream
);
```

---

## .NET Endpoint — Attach Domain (full flow)

```csharp
// POST /api/domains/attach
[HttpPost("attach")]
public async Task<IActionResult> AttachDomain(
    [FromBody] AttachDomainRequest req,
    CancellationToken ct)
{
    // 1. Validate domain not already taken
    var existing = await db.CustomDomains.FirstOrDefaultAsync(d => d.Domain == req.Domain, ct);
    if (existing is not null)
        return Conflict(new { error = "Domain already registered" });

    // 2. Save as pending
    var record = new CustomDomain
    {
        StoreId = currentStoreId,   // from auth claims
        Domain  = req.Domain.ToLowerInvariant().Trim(),
        Status  = "pending",
    };
    db.CustomDomains.Add(record);
    await db.SaveChangesAsync(ct);

    // 3. Call domain agent (fast — nginx live in ~1s, SSL async)
    var result = await domainAgent.ProvisionAsync(
        req.Domain,
        req.Slug,
        currentStoreId,
        ct: ct
    );

    if (!result.Ok)
    {
        // DNS not pointing to server yet — keep record as pending, return error
        record.Status = "pending";
        await db.SaveChangesAsync(ct);
        return BadRequest(new { error = result.Message });
    }

    // 4. Update to ssl_pending — agent will callback when SSL is done
    record.Status    = "ssl_pending";
    record.SslStatus = "pending";
    record.VerifiedAt = DateTime.UtcNow;
    await db.SaveChangesAsync(ct);

    return Accepted(new { domain = req.Domain, status = "ssl_pending" });
}
```

---

## Nginx Routing Model

The agent writes one config per domain that:
- Passes `Host $host` **unchanged** to your storefront app
- Your app reads the `Host` header and resolves the tenant from the DB

```nginx
upstream aqlaan_my_store {
    server 127.0.0.1:3000;
    keepalive 32;
}

server {
    listen 80;
    server_name store.example.com;

    location / {
        proxy_pass       http://aqlaan_my_store;
        proxy_set_header Host $host;          # ← tenant resolution happens here
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
# Certbot appends HTTPS block automatically
```

Your storefront app tenant resolution pattern:
```csharp
// Middleware or filter
var host   = httpContext.Request.Host.Host; // "store.example.com"
var domain = await db.CustomDomains
    .Include(d => d.Store)
    .FirstOrDefaultAsync(d => d.Domain == host && d.Status == "active", ct);

if (domain is null) { /* 404 or fallback */ return; }
httpContext.Items["CurrentStore"] = domain.Store;
```

---

## Hangfire Recurring Jobs

```csharp
// Program.cs or JobSetup.cs
RecurringJob.AddOrUpdate<DomainAgentService>(
    "ssl-renew-all",
    svc => svc.RenewAllSslAsync(CancellationToken.None),
    Cron.HourInterval(12)
);
```

---

## Error Handling Patterns

| Scenario                        | Agent response                                | .NET action                              |
|---------------------------------|-----------------------------------------------|------------------------------------------|
| DNS not pointing to server      | `ok: false`, message has "wrong_ip"           | Return 400 to merchant, keep status=pending |
| DNS not propagated yet          | `ok: false`, message has "dns_error"          | Return 400, suggest retry in 10 min      |
| nginx config write failed       | HTTP 500                                      | Mark status=failed, alert ops            |
| certbot failed (after callback) | callback `ssl_status: "failed"`               | Update DB, surface to merchant           |
| Agent unreachable               | `HttpRequestException` / timeout              | Mark status=pending, retry via Hangfire  |

---

## Environment Variables Reference

Agent `.env` on the host:

| Variable               | Example                              | Purpose                                  |
|------------------------|--------------------------------------|------------------------------------------|
| `DOMAIN_AGENT_SECRET`  | `super-secret-32chars`               | Shared secret for .NET → agent calls     |
| `SERVER_IP`            | `1.2.3.4`                            | IP the A record must resolve to          |
| `FRONTEND_UPSTREAM`    | `127.0.0.1:3000`                     | Default storefront address               |
| `CERTBOT_EMAIL`        | `ops@yourdomain.com`                 | Let's Encrypt registration email         |
| `PROVISION_SSL_ASYNC`  | `true`                               | Issue SSL in background (non-blocking)   |
| `CALLBACK_URL`         | `http://127.0.0.1:5000/internal/domain-ready` | .NET callback endpoint         |
| `CALLBACK_SECRET`      | `another-secret`                     | Sent as `X-Agent-Secret` in callback     |
| `ENABLE_TLS`           | `true`                               | Set `false` in dev to skip certbot       |

.NET `appsettings.json`:

```json
{
  "DomainAgent": {
    "BaseUrl":        "http://127.0.0.1:8100",
    "Secret":         "<same as DOMAIN_AGENT_SECRET>",
    "CallbackSecret": "<same as CALLBACK_SECRET>"
  }
}
```
