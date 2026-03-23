---
name: smtp-email
description: Set up transactional email sending via SMTP (Gmail App Password or any SMTP provider) for a backend project. Use when the user wants to send password reset, welcome, or confirmation emails. Covers .NET, Node.js, and Python backends.
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# SMTP Transactional Email Skill

You are setting up best-practice 2026 transactional email via SMTP. Follow this guide precisely.

## Architecture

```
Application code
  → IEmailService (interface)
      → SmtpEmailService (real, uses Gmail/SMTP in production)
      → LoggingEmailService (fake, logs to console in tests/dev)

Triggered by:
  - User registration  → SendWelcomeAsync
  - Forgot password    → SendPasswordResetAsync
  - Email confirmation → SendEmailConfirmationAsync
```

### Key design rules

| Rule | Rationale |
|---|---|
| Always hide SMTP behind an interface | Swap providers without touching callers |
| Use App Passwords, never your real account password | Safe to revoke, scoped access |
| Never commit credentials — use `.env` or secrets manager | Prevent credential leaks |
| Replace the real implementation with a fake in tests | No real emails in CI |
| HTML emails with inline styles | Maximum email client compatibility |
| Log success and failure with structured logging | Observability without leaking content |

---

## Step 1 — Understand the project stack

Read the main entrypoint and any existing email/notification code to determine:
- Language/framework (.NET, Node/Express, Python/FastAPI, etc.)
- Existing email service or `IEmailService` interface
- Config format (appsettings.json, .env, config.py, etc.)
- Test setup (what fake/mock pattern is in use)

Ask the user for any missing values:
- SMTP host (e.g. `smtp.gmail.com`)
- SMTP port (587 for STARTTLS, 465 for SSL)
- SMTP username (usually the sender email)
- SMTP password (App Password, not account password)
- From address and display name

---

## Step 2 — Gmail App Password setup (if using Gmail)

Tell the user to do this in their Google Account if not already done:

1. Go to **myaccount.google.com → Security → 2-Step Verification** — must be ON
2. Go to **myaccount.google.com → Security → App passwords**
3. Create a new App Password — name it something like "Ovovex Backend"
4. Copy the 16-character password (remove spaces when storing)
5. Gmail SMTP settings:
   - Host: `smtp.gmail.com`
   - Port: `587` (STARTTLS)
   - Username: your full Gmail/Google Workspace address
   - Password: the 16-char App Password (no spaces)
   - `EnableSsl = true` (triggers STARTTLS on port 587)

> ⚠️ App Passwords only appear once. Save it immediately.

---

## Step 3 — Store credentials in environment

Never hardcode credentials. Use `.env` (loaded at startup) or a secrets manager.

```env
Smtp__Host=smtp.gmail.com
Smtp__Port=587
Smtp__Username=you@yourdomain.com
Smtp__Password=abcdabcdabcdabcd
Smtp__FromAddress=you@yourdomain.com
Smtp__FromName=Your App Name
```

Ensure `.env` is in `.gitignore`.

---

## Step 4 — Implement per stack

### .NET (ASP.NET Core)

#### SmtpSettings.cs
```csharp
using System.ComponentModel.DataAnnotations;

public sealed class SmtpSettings
{
    public const string SectionName = "Smtp";

    [Required] public string Host        { get; init; } = string.Empty;
    [Range(1, 65535)] public int Port    { get; init; } = 587;
    [Required] public string Username    { get; init; } = string.Empty;
    [Required] public string Password    { get; init; } = string.Empty;
    [Required] public string FromAddress { get; init; } = string.Empty;
    public string FromName               { get; init; } = "My App";
}
```

#### IEmailService.cs (interface)
```csharp
public interface IEmailService
{
    Task SendPasswordResetAsync(string toEmail, string displayName, string token);
    Task SendEmailConfirmationAsync(string toEmail, string displayName, string token);
    Task SendWelcomeAsync(string toEmail, string displayName);
}
```

#### SmtpEmailService.cs
```csharp
using System.Net;
using System.Net.Mail;
using System.Text;
using Microsoft.Extensions.Options;

public sealed class SmtpEmailService(
    IOptions<SmtpSettings>    opts,
    ILogger<SmtpEmailService> logger
) : IEmailService
{
    private SmtpSettings Settings => opts.Value;

    public Task SendPasswordResetAsync(string toEmail, string displayName, string token) =>
        SendAsync(toEmail, displayName,
            subject: "Reset your password",
            htmlBody: $"""
                <p>Hi {Encode(displayName)},</p>
                <p>Click below to reset your password. This link expires in 1 hour.</p>
                <p><a href="https://app.example.com/reset-password?token={Uri.EscapeDataString(token)}"
                      style="padding:10px 20px;background:#4F46E5;color:#fff;border-radius:6px;text-decoration:none;">
                  Reset Password
                </a></p>
                """);

    public Task SendEmailConfirmationAsync(string toEmail, string displayName, string token) =>
        SendAsync(toEmail, displayName,
            subject: "Confirm your email",
            htmlBody: $"""
                <p>Hi {Encode(displayName)},</p>
                <p><a href="https://app.example.com/confirm-email?token={Uri.EscapeDataString(token)}"
                      style="padding:10px 20px;background:#4F46E5;color:#fff;border-radius:6px;text-decoration:none;">
                  Confirm Email
                </a></p>
                """);

    public Task SendWelcomeAsync(string toEmail, string displayName) =>
        SendAsync(toEmail, displayName,
            subject: "Welcome!",
            htmlBody: $"<p>Hi {Encode(displayName)}, your account is ready.</p>");

    private async Task SendAsync(string toEmail, string displayName, string subject, string htmlBody)
    {
        using var smtp = new SmtpClient(Settings.Host, Settings.Port)
        {
            Credentials    = new NetworkCredential(Settings.Username, Settings.Password),
            EnableSsl      = true,
            DeliveryMethod = SmtpDeliveryMethod.Network,
        };
        using var msg = new MailMessage
        {
            From         = new MailAddress(Settings.FromAddress, Settings.FromName),
            Subject      = subject,
            Body         = htmlBody,
            IsBodyHtml   = true,
            BodyEncoding = Encoding.UTF8,
        };
        msg.To.Add(new MailAddress(toEmail, displayName));

        try
        {
            await smtp.SendMailAsync(msg);
            logger.LogInformation("Email sent to {Recipient} — {Subject}", toEmail, subject);
        }
        catch (SmtpException ex)
        {
            logger.LogError(ex, "Failed to send email to {Recipient}", toEmail);
            throw;
        }
    }

    private static string Encode(string s) => System.Net.WebUtility.HtmlEncode(s);
}
```

#### Registration (in Module or Program.cs)
```csharp
services
    .AddOptions<SmtpSettings>()
    .Bind(config.GetSection(SmtpSettings.SectionName))
    .ValidateDataAnnotations()
    .ValidateOnStart();

services.AddScoped<IEmailService, SmtpEmailService>();
```

#### LoggingEmailService.cs (for dev/test)
```csharp
public sealed class LoggingEmailService(ILogger<LoggingEmailService> logger) : IEmailService
{
    public Task SendPasswordResetAsync(string toEmail, string displayName, string token)
    {
        logger.LogInformation("[EMAIL] Password reset → {Email} | token: {Token}", toEmail, token);
        return Task.CompletedTask;
    }
    public Task SendEmailConfirmationAsync(string toEmail, string displayName, string token)
    {
        logger.LogInformation("[EMAIL] Confirm email → {Email} | token: {Token}", toEmail, token);
        return Task.CompletedTask;
    }
    public Task SendWelcomeAsync(string toEmail, string displayName)
    {
        logger.LogInformation("[EMAIL] Welcome → {Email}", toEmail);
        return Task.CompletedTask;
    }
}
```

#### Test host (WebApplicationFactory override)
```csharp
// In ConfigureServices — replace real SMTP with logger fake
var d = services.SingleOrDefault(s => s.ServiceType == typeof(IEmailService));
if (d != null) services.Remove(d);
services.AddScoped<IEmailService, LoggingEmailService>();
```

#### appsettings.Test.json (stub so ValidateOnStart passes)
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

### Node.js (Express / NestJS) — using `nodemailer`

```bash
npm install nodemailer
npm install -D @types/nodemailer
```

```typescript
import nodemailer from 'nodemailer';

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: Number(process.env.SMTP_PORT) || 587,
  secure: false, // STARTTLS
  auth: {
    user: process.env.SMTP_USERNAME,
    pass: process.env.SMTP_PASSWORD,
  },
});

export async function sendPasswordReset(to: string, name: string, token: string) {
  await transporter.sendMail({
    from: `"${process.env.SMTP_FROM_NAME}" <${process.env.SMTP_FROM_ADDRESS}>`,
    to,
    subject: 'Reset your password',
    html: `<p>Hi ${name},</p>
           <p><a href="${process.env.APP_URL}/reset-password?token=${encodeURIComponent(token)}">Reset Password</a></p>`,
  });
}
```

---

### Python (FastAPI) — using `aiosmtplib`

```bash
pip install aiosmtplib
```

```python
import aiosmtplib
from email.message import EmailMessage
import os

async def send_password_reset(to_email: str, display_name: str, token: str):
    msg = EmailMessage()
    msg["From"] = f"{os.getenv('SMTP_FROM_NAME')} <{os.getenv('SMTP_FROM_ADDRESS')}>"
    msg["To"] = to_email
    msg["Subject"] = "Reset your password"
    msg.set_content(
        f"<p>Hi {display_name},</p>"
        f"<p><a href='{os.getenv('APP_URL')}/reset-password?token={token}'>Reset Password</a></p>",
        subtype="html"
    )
    await aiosmtplib.send(
        msg,
        hostname=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT", 587)),
        username=os.getenv("SMTP_USERNAME"),
        password=os.getenv("SMTP_PASSWORD"),
        start_tls=True,
    )
```

---

## Step 5 — Smoke test

Create a one-off test that sends a real email to a safe test address to verify the full pipeline:

```csharp
// .NET — run with: dotnet test --filter "Category=Manual"
[Trait("Category", "Manual")]
public class EmailSmokeTests
{
    [Fact]
    public async Task SendPasswordReset_ToTestAddress()
    {
        var svc = new SmtpEmailService(
            Options.Create(new SmtpSettings
            {
                Host        = "smtp.gmail.com",
                Port        = 587,
                Username    = "you@domain.com",
                Password    = "your-app-password",
                FromAddress = "you@domain.com",
                FromName    = "My App (Test)",
            }),
            NullLogger<SmtpEmailService>.Instance);

        await svc.SendPasswordResetAsync("recipient@example.com", "Test User", "smoke-token-123");
    }
}
```

---

## Verification checklist

- [ ] App Password created in Google Account (not account password)
- [ ] Credentials stored in `.env` only — not in `appsettings.json` or source code
- [ ] `.env` is in `.gitignore`
- [ ] `SmtpSettings` validated at startup (`ValidateOnStart`)
- [ ] `IEmailService` interface exists — implementation is swappable
- [ ] Test host uses `LoggingEmailService` (no real SMTP in CI)
- [ ] `appsettings.Test.json` has stub `Smtp` section to satisfy options validation
- [ ] Smoke test passes (`dotnet test --filter "Category=Manual"`)
- [ ] Recipient receives HTML email with correct link format
- [ ] Logs show `Email sent to {Recipient}` on success, error on failure

---

## Common errors

| Error | Cause | Fix |
|---|---|---|
| `535 Authentication failed` | Wrong password or App Password not enabled | Re-generate App Password; ensure 2FA is on |
| `534 Please log in via your browser` | Account not using App Passwords | Enable 2-Step Verification first |
| `Connection refused` | Wrong host/port | Use `smtp.gmail.com:587` with STARTTLS |
| `ValidateOnStart fails in tests` | Missing `Smtp` section in test config | Add stub section to `appsettings.Test.json` |
| `SMTP provider limit reached` | Gmail has a 500/day limit | Use SendGrid/Mailgun for production volume |

---

## Production upgrade path

Gmail App Passwords work well for low-volume internal tools. For higher volume or branded domains:

| Provider | Free tier | Notes |
|---|---|---|
| **SendGrid** | 100/day | Good .NET SDK, reliable |
| **Mailgun** | 100/day | Strong API, good EU options |
| **Resend** | 3000/month | Modern API, great DX |
| **AWS SES** | 62,000/month (from EC2) | Cheapest at scale |

When upgrading, replace only `SmtpEmailService` — the `IEmailService` interface stays the same.
