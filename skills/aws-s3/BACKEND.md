# AWS S3 + CloudFront — Backend Setup (Ovovex Backend v3)

This guide is tailored to the current Ovovex backend implementation.

---

## Current backend setup (verified)

### 1) Runtime wiring exists
- `.env` is loaded at startup in `Program.cs`.
- `Storage` settings are bound via `StorageSettings`.
- `AWSSDK.S3` package is installed.
- `IAmazonS3` is registered in DI inside `FilesModule`.
- `IStorageProvider` is implemented by `S3StorageProvider`.

### 2) Public/private storage model exists
- Key format used: `{public|private}/{tenant|system}/{context}/{guid}.{ext}`.
- Public contexts are CDN-served (permanent URL).
- Private contexts are presigned URL only.

### 3) API endpoints already implemented
- `POST /api/files/upload`
- `GET /api/files/{fileId}`
- `GET /api/files/{fileId}/url?expiryHours=1`
- `GET /api/files?context=...&contextId=...`
- `DELETE /api/files/{fileId}`
- Alias: `POST /api/storage/upload`

### 4) Validation exists
- Max file: 20 MB
- Max image: 5 MB
- MIME whitelist for image/docs

---

## Required configuration (for this codebase)

Use `.env` (already gitignored) and set:

```env
# S3 credentials (SDK default chain supports these)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=me-central-1

# App storage settings (bound from "Storage" section)
Storage__BucketName=your-bucket-name
Storage__Region=me-central-1
Storage__CdnBaseUrl=https://media.aqlaan.com
Storage__PresignedExpiryHours=1
```

Notes:
- `Storage__BucketName` is required in practice.
- CDN URL should be your CloudFront custom domain (or distribution domain).
- Keep S3 bucket private; expose only `public/*` through CloudFront OAC.

---

## Context behavior in current code

### Public (permanent CDN URL)
- `company-logos`
- `profile-avatars`
- `product-images`

### Private (presigned URL)
- `invoice-docs`
- `contract-docs`
- `attachments`
- `exports`
- any unknown context defaults to private

---

## What to check in AWS Console

### S3 Bucket
1. Block Public Access: ON
2. Object Ownership: BucketOwnerEnforced
3. CORS (if browser uploads are ever used directly)

### CloudFront
1. Origin: S3 bucket endpoint
2. Origin Access Control (OAC): attached
3. Alternate domain (CNAME): `media.aqlaan.com` (or your domain)
4. TLS certificate valid for CDN domain

### Bucket policy
- Allow CloudFront distribution to read only `public/*`.
- Do **not** allow `private/*` via CloudFront.

### If using KMS encryption
- KMS key policy must allow CloudFront service principal with distribution ARN condition.

---

## Expected request/response behavior

### Upload
`POST /api/files/upload?context=company-logos&tenantId=<guid>&contextId=<guid>`

Response includes:
- `fileId`
- `key`
- `isPublic`
- `url` (CDN for public, presigned for private)

### Get file by id
`GET /api/files/{fileId}`
- returns metadata + fresh-access URL model

### Refresh URL
`GET /api/files/{fileId}/url?expiryHours=1`
- public: permanent CDN URL
- private: fresh presigned URL (1..168 hours)

---

## Quick verification checklist

1. Upload image with `context=company-logos`
   - key starts with `public/`
   - URL starts with CDN base URL
   - URL should be stable and cacheable

2. Upload PDF with `context=invoice-docs`
   - key starts with `private/`
   - URL should be presigned and expire

3. Call `GET /api/files/{id}/url`
   - private file should return a different signed URL over time

4. Try opening `https://<cdn>/private/...`
   - should return 403 (or inaccessible)

---

## Operational rules for backend developers

1. Store only `key` in DB; never store full URL.
2. Use `GetPublicUrl()` only for `public/*` objects.
3. Use presigned URLs for all `private/*` objects.
4. Keep tenant in key path to avoid collisions and simplify isolation.
5. Keep `.env` secrets out of git.

---

## Suggested hardening (optional but recommended)

1. Fail fast at startup if `Storage:BucketName` is empty.
2. Add startup log line showing active `Storage:Region`, `BucketName`, and `CdnBaseUrl` (without secrets).
3. Add integration test that asserts:
   - public context => CDN URL
   - private context => presigned URL
4. Add health check that validates S3 bucket access permissions.

---

If you need to scaffold this pattern in another .NET project, reuse this guide plus `SKILL.md` in the same folder.