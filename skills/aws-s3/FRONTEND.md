# File Storage — Frontend Integration Guide

> **CDN:** `https://media.aqlaan.com`  
> All file operations require a valid `Authorization: Bearer <token>` header.

---

## Endpoints at a glance

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/files/upload` | Upload a file |
| `GET` | `/api/files/{fileId}` | Get file metadata + URL |
| `GET` | `/api/files/{fileId}/url` | Get a fresh URL (presigned or CDN) |
| `GET` | `/api/files?context=xxx` | List files by context |
| `DELETE` | `/api/files/{fileId}` | Delete a file |

---

## Upload a file

```
POST /api/files/upload?context=company-logos&contextId=<guid>&tenantId=<guid>
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Form field:** `file` (binary)

**Query params:**

| Param | Required | Default | Example |
|-------|----------|---------|---------|
| `context` | No | `attachments` | `company-logos` |
| `contextId` | No | — | `<entity guid>` |
| `tenantId` | No | — | `<tenant guid>` |

**Response:**
```json
{
  "fileId": "0194f3a2-1234-7abc-8def-000000000001",
  "key": "public/tenant-id/company-logos/0194f3a2.png",
  "originalFileName": "logo.png",
  "contentType": "image/png",
  "sizeBytes": 24890,
  "context": "company-logos",
  "isPublic": true,
  "url": "https://media.aqlaan.com/public/tenant-id/company-logos/0194f3a2.png"
}
```

---

## The `url` field — the only URL you ever need

```
isPublic: true  →  Permanent CDN URL
                   https://media.aqlaan.com/public/.../uuid.png
                   ✅ Use directly in <img src>, <video src>, CSS background-image
                   ✅ Cache forever — this URL never changes

isPublic: false →  1-hour presigned S3 URL
                   https://s3.amazonaws.com/...?X-Amz-Expires=3600&...
                   ⚠️  Expires in 1 hour — always fetch a fresh URL right before use
```

> **Rule: always use the `url` from the API. Never construct URLs yourself.**

---

## Contexts — public vs private

| Context | `isPublic` | URL type | Use for |
|---------|------------|----------|---------|
| `company-logos` | ✅ `true` | Permanent CDN | Company / tenant logos |
| `profile-avatars` | ✅ `true` | Permanent CDN | User profile pictures |
| `product-images` | ✅ `true` | Permanent CDN | Product photos |
| `invoice-docs` | ❌ `false` | Presigned (1 hr) | Invoice PDFs |
| `contract-docs` | ❌ `false` | Presigned (1 hr) | Contract documents |
| `attachments` | ❌ `false` | Presigned (1 hr) | General file attachments |
| `exports` | ❌ `false` | Presigned (1 hr) | Report / data exports |

---

## Get a single file

```
GET /api/files/{fileId}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "fileId": "0194f3a2-...",
  "key": "private/tenant-id/invoice-docs/0194f3a2.pdf",
  "originalFileName": "invoice-2026-001.pdf",
  "contentType": "application/pdf",
  "sizeBytes": 102400,
  "context": "invoice-docs",
  "contextId": "company-guid",
  "tenantId": "tenant-guid",
  "uploaderId": "user-guid",
  "createdAt": "2026-03-08T10:00:00Z",
  "isPublic": false,
  "url": "https://s3.amazonaws.com/...?X-Amz-Expires=3600&..."
}
```

---

## Get a fresh URL

Use this endpoint right before displaying or linking to a private file:

```
GET /api/files/{fileId}/url?expiryHours=1
Authorization: Bearer <token>
```

| File type | Returns | Notes |
|-----------|---------|-------|
| Public | Permanent CDN URL | Instant — no AWS call |
| Private | Fresh presigned URL | Valid for `expiryHours` (1–168) |

---

## List files by context

```
GET /api/files?context=invoice-docs&contextId=<entityId>
Authorization: Bearer <token>
```

Returns an array of `FileRecordResponse` objects, each with its own `url`.

---

## Delete a file

```
DELETE /api/files/{fileId}
Authorization: Bearer <token>
```

Only the uploader can delete their own files. Returns `204 No Content` on success.

---

## File limits (enforce client-side too)

```ts
const MAX_FILE_SIZE  = 20 * 1024 * 1024;   // 20 MB — all files
const MAX_IMAGE_SIZE =  5 * 1024 * 1024;   //  5 MB — images only

const ALLOWED_IMAGE_TYPES = [
  'image/jpeg', 'image/png', 'image/webp',
  'image/gif',  'image/svg+xml', 'image/heic',
];

const ALLOWED_DOC_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'text/csv',
  'text/plain',
];
```

---

## Code patterns

### Upload (React + fetch)

```tsx
async function uploadFile(file: File, context: string, contextId?: string) {
  const form = new FormData();
  form.append('file', file);

  const params = new URLSearchParams({ context });
  if (contextId) params.set('contextId', contextId);

  const res = await fetch(`/api/files/upload?${params}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });

  if (!res.ok) throw new Error(await res.text());
  return res.json(); // { fileId, key, isPublic, url, ... }
}
```

### Display a public image

```tsx
// url is permanent — use directly, cache freely
<img src={file.url} alt={file.originalFileName} />
```

### Open a private document

```tsx
// Always fetch a fresh URL right before opening — never cache presigned URLs
async function openPrivateFile(fileId: string) {
  const res = await fetch(`/api/files/${fileId}/url`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const url = await res.json();
  window.open(url, '_blank');
}
```

### After upload — what to store

```ts
const { fileId, key, isPublic, url } = await uploadFile(file, 'company-logos');

// ✅ Store fileId (or key) on your entity in your own API call
await api.patch(`/companies/${companyId}`, { logoFileId: fileId });

// ✅ Use url immediately for display — it's already the right type
setLogoUrl(url);

// ❌ Never save `url` to your database — only fileId or key
```

---

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Caching a presigned URL in `localStorage` | Always call `GET /files/{id}/url` fresh before opening |
| Building `https://media.aqlaan.com/` + `key` yourself | Use the `url` field from the API response |
| Saving `url` to your own database | Save only `fileId` — URLs are always derived server-side |
| Showing a broken `<img>` for a private file | Check `isPublic`; private files need the presigned flow |
| Not checking file type/size before upload | Validate client-side first to avoid a wasted request |
