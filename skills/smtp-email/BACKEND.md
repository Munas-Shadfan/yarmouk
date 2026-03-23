# SMTP Email — Backend Setup (Ovovex Backend v3)

This guide is tailored to the current Ovovex backend implementation.

---

## Current implementation (verified working)

### Files in place

| File | Purpose |
|---|---|
| `Modules/Auth/Infrastructure/Config/SmtpSettings.cs` | Strongly-typed settings with `[Required]` + `ValidateOnStart` |
| `Modules/Auth/Infrastructure/SmtpEmailService.cs` | Real SMTP implementation (Gmail App Password) |
| `Modules/Auth/Infrastructure/LoggingEmailService.cs` | Dev/test fake — logs to console only |
| `Modules/Auth/Application/Interfaces/IServices.cs` | `IEmailService` interface definition |
| `Modules/Auth/AuthModule.cs` | Registers `SmtpEmailService` as `IEmailService` |
| `test/Auth/EmailSmokeTests.cs` | Manual smoke test (`[Trait("Category", "Manual")]`) |

### Endpoints that trigger emails

| Trigger | Method | Email type |
|---|---|---|
| `POST /api/auth/register` | `SendWelcomeAsync` | Welcome |
| `POST /api/auth/forgot-password` | `SendPasswordResetAsync` | Password reset link |
| (future) email confirmation | `SendEmailConfirmationAsync` | Confirm email |

### SMTP provider in use

- **Provider**: Gmail (Google Workspace)
- **Host**: `smtp.gmail.com`
- **Port**: `587` (STARTTLS)
- **From**: `al-hussein@aqlaan.com`

---

## Required .env configuration

```env
Smtp__Host=smtp.gmail.com
Smtp__Port=587
Smtp__Username=al-hussein@aqlaan.com
Smtp__Password=<16-char-app-password-no-spaces>
Smtp__FromAddress=al-hussein@aqlaan.com
Smtp__FromName=Ovovex
```

> App Password is stored in `.env` only. Never commit it.

---

## Test environment wiring

In `test/Infrastructure/WebAppFactory.cs`, the real `SmtpEmailService` is replaced with `LoggingEmailService`:

```csharp
RemoveDescriptor<IEmailService>(services);
services.AddScoped<IEmailService, LoggingEmailService>();
```

`test/appsettings.Test.json` has a stub `Smtp` section so `ValidateOnStart()` passes:

```json
"Smtp": {
  "Host": "smtp.test.local",
  "Port": 587,
  "Username": "test@test.com",
  "Password": "test-password",
  "FromAddress": "test@test.com",
  "FromName": "Test"
}
```

---

## Running the smoke test

```bash
dotnet test test/Ovovex.Test.csproj --filter "Category=Manual"
```

Sends a real password reset and welcome email to the configured test address.
Smoke tests are excluded from normal CI runs.

---

## Verification checklist

- [x] App Password created and stored in `.env`
- [x] `SmtpSettings` validated at startup (`ValidateDataAnnotations` + `ValidateOnStart`)
- [x] `IEmailService` interface is clean — real/fake implementations swappable
- [x] Test host uses `LoggingEmailService` (no real SMTP in CI)
- [x] `appsettings.Test.json` has stub `Smtp` section
- [x] Smoke test passes — real emails delivered to `al-hussein@papayatrading.com`
- [x] 60/60 integration tests pass with no SMTP calls

---

## Adding a new email type

1. Add the method signature to `IEmailService` in `Modules/Auth/Application/Interfaces/IServices.cs`
2. Implement it in `SmtpEmailService.cs` (HTML body, call `SendAsync`)
3. Implement a no-op/log version in `LoggingEmailService.cs`
4. Inject `IEmailService` in the command handler and call it
5. Add a smoke test case to `EmailSmokeTests.cs`

---

## Upgrade to SendGrid (when volume exceeds Gmail limits)

Gmail allows ~500 emails/day. When you need more:

1. Sign up at sendgrid.com, get an API key
2. Install: `dotnet add package SendGrid`
3. Create `SendGridEmailService : IEmailService` 
4. Swap registration in `AuthModule.cs` — everything else stays the same
