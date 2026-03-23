---
name: aws-s3
description: Set up AWS S3 + CloudFront CDN file storage for a backend project. Use when the user wants to add S3 uploads, CDN serving, presigned URLs for private files, or integrate the full public/private storage pattern. Covers .NET, Node.js, and Python backends.
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# AWS S3 + CloudFront Storage Skill

You are setting up best-practice 2026 AWS S3 + CloudFront file storage. Follow this guide precisely.

## Architecture

```
Upload → Backend → S3 bucket
                    ├── public/{tenantId}/{context}/uuid.ext  ← CloudFront CDN (permanent URLs)
                    └── private/{tenantId}/{context}/uuid.ext ← Backend presigned URLs only (1 hr)

CDN domain:  https://media.aqlaan.com
Frontend never gets AWS credentials.
Database stores only the S3 key (e.g. "public/tenant-abc/company-logos/uuid.png"), never a full URL.
```

### Key design rules
| Rule | Rationale |
|------|-----------|
| Always store the **S3 key** in the database, never a full URL | CDN domain changes don't break old records |
| `public/` prefix → permanent CDN URL, no AWS call needed | Zero latency, cacheable by browser/CDN |
| `private/` prefix → 1-hour presigned URL issued by the backend | Sensitive docs never hit CloudFront |
| S3 bucket policy grants CloudFront OAC access to `public/*` only | Even if someone guesses a private key, CloudFront returns 403 |
| Tenant ID in the key path | Prevents cross-tenant key collisions; easy IAM policy scoping |
| Frontend receives a single `url` field | Frontend doesn't need to know public vs private logic |

## Step 1 — Understand the project stack

Read the main entrypoint and any existing config files to determine:
- Language/framework (.NET, Node/Express, Python/FastAPI, etc.)
- Existing storage or file upload code
- Config file format (appsettings.json, .env, config.py, etc.)

Ask the user for any missing values:
- AWS Access Key ID
- AWS Secret Access Key
- AWS Region (e.g. `me-central-1`, `us-east-1`)
- S3 Bucket name
- CloudFront distribution domain (e.g. `media.example.com` or `d1234.cloudfront.net`)
- CloudFront distribution ID

## Step 2 — AWS Infrastructure setup instructions

Tell the user to complete these steps in the AWS Console if not already done:

### S3 Bucket
1. Create bucket in correct region
2. **Block all public access** — keep this ON (CloudFront uses OAC, not public access)
3. Object Ownership: **BucketOwnerEnforced** (disables ACLs)

### CloudFront Distribution
1. Create distribution, origin = `<bucket>.s3.<region>.amazonaws.com`
2. Origin access: **Origin Access Control (OAC)** — create new OAC
3. After creation, copy the bucket policy AWS provides and apply it to the S3 bucket
4. Add CNAME for your CDN domain (e.g. `media.example.com`)

### KMS Encryption (critical if bucket uses KMS)
If the S3 bucket uses KMS encryption, CloudFront OAC needs decrypt access.
Add this statement to the KMS key policy:
```json
{
  "Sid": "AllowCloudFrontDecrypt",
  "Effect": "Allow",
  "Principal": { "Service": "cloudfront.amazonaws.com" },
  "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "AWS:SourceArn": "arn:aws:cloudfront::<ACCOUNT_ID>:distribution/<DISTRIBUTION_ID>"
    }
  }
}
```

## Step 3 — Implement based on stack

### .NET / ASP.NET Core

**Packages needed:**
```
AWSSDK.S3
AWSSDK.Extensions.NETCore.Setup
```

**appsettings.json** (no real credentials here):
```json
{
  "AppSettings": {
    "CdnBaseUrl": "https://media.example.com"
  },
  "AWS": {
    "AccessKeyId": "",
    "SecretAccessKey": "",
    "Region": "me-central-1",
    "BucketName": "your-bucket"
  }
}
```

**.env** (real credentials, double-underscore for nested .NET config):
```
AWS__AccessKeyId=AKIA...
AWS__SecretAccessKey=...
AWS__Region=me-central-1
AWS__BucketName=your-bucket
```

**Program.cs** — load .env before builder, register S3 explicitly:
```csharp
// Load .env into environment variables BEFORE WebApplication.CreateBuilder
var envFile = Path.Combine(Directory.GetCurrentDirectory(), ".env");
if (File.Exists(envFile))
{
    foreach (var line in File.ReadAllLines(envFile))
    {
        var trimmed = line.Trim();
        if (string.IsNullOrEmpty(trimmed) || trimmed.StartsWith('#')) continue;
        var idx = trimmed.IndexOf('=');
        if (idx < 0) continue;
        Environment.SetEnvironmentVariable(trimmed[..idx].Trim(), trimmed[(idx + 1)..].Trim());
    }
}

var builder = WebApplication.CreateBuilder(args);

// Register S3 client — GetAWSOptions() does NOT read AccessKeyId/SecretAccessKey from config
var awsAccessKey = builder.Configuration["AWS:AccessKeyId"];
var awsSecretKey = builder.Configuration["AWS:SecretAccessKey"];
var awsRegion = builder.Configuration["AWS:Region"] ?? "us-east-1";

Amazon.Runtime.AWSCredentials awsCredentials =
    !string.IsNullOrEmpty(awsAccessKey) && !string.IsNullOrEmpty(awsSecretKey)
    ? new Amazon.Runtime.BasicAWSCredentials(awsAccessKey, awsSecretKey)
    : new Amazon.Runtime.EnvironmentVariablesAWSCredentials();

var s3Config = new Amazon.S3.AmazonS3Config
{
    RegionEndpoint = Amazon.RegionEndpoint.GetBySystemName(awsRegion)
};

builder.Services.AddSingleton<Amazon.S3.IAmazonS3>(
    _ => new Amazon.S3.AmazonS3Client(awsCredentials, s3Config));
builder.Services.AddScoped<IStorageService, S3StorageService>();
```

**IStorageService.cs:**
```csharp
public interface IStorageService
{
    /// <summary>Upload to public/ prefix — served via CloudFront CDN permanently.</summary>
    Task<string> UploadPublicFileAsync(Stream fileStream, string fileName, string contentType, string folder);

    /// <summary>Upload to private/ prefix — only accessible via backend presigned URL proxy.</summary>
    Task<string> UploadPrivateFileAsync(Stream fileStream, string fileName, string contentType, string folder);

    Task DeleteFileAsync(string keyOrUrl);

    /// <summary>Synchronous. Returns permanent CDN URL. No AWS call needed.</summary>
    string GetPublicUrl(string key);

    /// <summary>Returns a short-lived presigned URL for private files only.</summary>
    Task<string> GetPresignedUrlAsync(string key, int expiryMinutes = 15);
}
```

**S3StorageService.cs:**
```csharp
public class S3StorageService : IStorageService
{
    private readonly Amazon.S3.IAmazonS3 _s3;
    private readonly string _bucket;
    private readonly string _cdnBaseUrl;
    private readonly ILogger<S3StorageService> _logger;

    public S3StorageService(Amazon.S3.IAmazonS3 s3, IConfiguration config, ILogger<S3StorageService> logger)
    {
        _s3 = s3;
        _bucket = config["AWS:BucketName"] ?? throw new Exception("AWS:BucketName not configured");
        _cdnBaseUrl = (config["AppSettings:CdnBaseUrl"] ?? throw new Exception("AppSettings:CdnBaseUrl not configured")).TrimEnd('/');
        _logger = logger;
    }

    public async Task<string> UploadPublicFileAsync(Stream fileStream, string fileName, string contentType, string folder)
        => await UploadAsync(fileStream, fileName, contentType, $"public/{folder}");

    public async Task<string> UploadPrivateFileAsync(Stream fileStream, string fileName, string contentType, string folder)
        => await UploadAsync(fileStream, fileName, contentType, $"private/{folder}");

    private async Task<string> UploadAsync(Stream stream, string fileName, string contentType, string prefix)
    {
        var ext = Path.GetExtension(fileName).ToLowerInvariant();
        var key = $"{prefix}/{Guid.NewGuid()}{ext}";
        await _s3.PutObjectAsync(new Amazon.S3.Model.PutObjectRequest
        {
            BucketName = _bucket,
            Key = key,
            InputStream = stream,
            ContentType = contentType
        });
        _logger.LogInformation("S3 upload: {Key}", key);
        return key;
    }

    public string GetPublicUrl(string key)
    {
        if (key.StartsWith("http://") || key.StartsWith("https://")) return key;
        return $"{_cdnBaseUrl}/{key}";
    }

    public async Task<string> GetPresignedUrlAsync(string key, int expiryMinutes = 15)
    {
        var request = new Amazon.S3.Model.GetPreSignedUrlRequest
        {
            BucketName = _bucket,
            Key = key,
            Expires = DateTime.UtcNow.AddMinutes(expiryMinutes),
            Protocol = Amazon.S3.Model.Protocol.HTTPS
        };
        return await Task.FromResult(_s3.GetPreSignedURL(request));
    }

    public async Task DeleteFileAsync(string keyOrUrl)
    {
        var key = keyOrUrl.StartsWith("http") ? new Uri(keyOrUrl).AbsolutePath.TrimStart('/') : keyOrUrl;
        await _s3.DeleteObjectAsync(_bucket, key);
    }
}
```

**Controller pattern — file upload endpoint:**
```csharp
[HttpPost("upload")]
public async Task<IActionResult> Upload(IFormFile file)
{
    if (file.Length > 10 * 1024 * 1024) return BadRequest("File too large");

    using var stream = file.OpenReadStream();
    string key;

    if (file.ContentType.StartsWith("image/"))
        key = await _storage.UploadPublicFileAsync(stream, file.FileName, file.ContentType, "images");
    else
        key = await _storage.UploadPrivateFileAsync(stream, file.FileName, file.ContentType, "documents");

    // Save `key` to database — never the full URL
    var media = new MediaEntity { Key = key, /* ... */ };
    await _db.Media.AddAsync(media);
    await _db.SaveChangesAsync();

    return Ok(new {
        id = media.Id,
        url = file.ContentType.StartsWith("image/")
            ? _storage.GetPublicUrl(key)      // permanent CDN URL
            : $"/api/media/file/{media.Id}"    // proxy URL
    });
}

// Private file proxy — redirects to 15-min presigned URL
[HttpGet("file/{id}")]
public async Task<IActionResult> GetFile(int id)
{
    var media = await _db.Media.FindAsync(id);
    if (media == null) return NotFound();
    // Add auth check here
    var url = await _storage.GetPresignedUrlAsync(media.Key, 15);
    return Redirect(url);
}
```

---

### Node.js / Express

**Install:**
```bash
npm install @aws-sdk/client-s3 @aws-sdk/s3-request-presigner
```

**.env:**
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=me-central-1
AWS_BUCKET_NAME=your-bucket
CDN_BASE_URL=https://media.example.com
```

**storage.js:**
```js
import { S3Client, PutObjectCommand, DeleteObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3'
import { getSignedUrl } from '@aws-sdk/s3-request-presigner'
import { randomUUID } from 'crypto'
import path from 'path'

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  }
})

const BUCKET = process.env.AWS_BUCKET_NAME
const CDN = process.env.CDN_BASE_URL.replace(/\/$/, '')

export async function uploadPublic(stream, fileName, contentType, folder) {
  const ext = path.extname(fileName).toLowerCase()
  const key = `public/${folder}/${randomUUID()}${ext}`
  await s3.send(new PutObjectCommand({ Bucket: BUCKET, Key: key, Body: stream, ContentType: contentType }))
  return key
}

export async function uploadPrivate(stream, fileName, contentType, folder) {
  const ext = path.extname(fileName).toLowerCase()
  const key = `private/${folder}/${randomUUID()}${ext}`
  await s3.send(new PutObjectCommand({ Bucket: BUCKET, Key: key, Body: stream, ContentType: contentType }))
  return key
}

export function getPublicUrl(key) {
  if (key.startsWith('http')) return key
  return `${CDN}/${key}`
}

export async function getPresignedUrl(key, expiresInSeconds = 900) {
  const command = new GetObjectCommand({ Bucket: BUCKET, Key: key })
  return getSignedUrl(s3, command, { expiresIn: expiresInSeconds })
}

export async function deleteFile(keyOrUrl) {
  const key = keyOrUrl.startsWith('http') ? new URL(keyOrUrl).pathname.slice(1) : keyOrUrl
  await s3.send(new DeleteObjectCommand({ Bucket: BUCKET, Key: key }))
}
```

---

### Python / FastAPI

**Install:**
```bash
pip install boto3 python-multipart
```

**storage.py:**
```python
import boto3, os, uuid
from pathlib import Path

s3 = boto3.client(
    's3',
    region_name=os.environ['AWS_REGION'],
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
)
BUCKET = os.environ['AWS_BUCKET_NAME']
CDN = os.environ['CDN_BASE_URL'].rstrip('/')

def upload_public(file, filename: str, content_type: str, folder: str) -> str:
    ext = Path(filename).suffix.lower()
    key = f"public/{folder}/{uuid.uuid4()}{ext}"
    s3.upload_fileobj(file, BUCKET, key, ExtraArgs={'ContentType': content_type})
    return key

def upload_private(file, filename: str, content_type: str, folder: str) -> str:
    ext = Path(filename).suffix.lower()
    key = f"private/{folder}/{uuid.uuid4()}{ext}"
    s3.upload_fileobj(file, BUCKET, key, ExtraArgs={'ContentType': content_type})
    return key

def get_public_url(key: str) -> str:
    if key.startswith('http'):
        return key
    return f"{CDN}/{key}"

def get_presigned_url(key: str, expires: int = 900) -> str:
    return s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET, 'Key': key},
        ExpiresIn=expires
    )

def delete_file(key_or_url: str):
    from urllib.parse import urlparse
    key = urlparse(key_or_url).path.lstrip('/') if key_or_url.startswith('http') else key_or_url
    s3.delete_object(Bucket=BUCKET, Key=key)
```

---

## Step 4 — Key rules to enforce

1. **Database always stores the S3 key** (`public/folder/uuid.jpg`), never a full URL
2. **`GetPublicUrl(key)` is synchronous** — no AWS call, just string concat with CDN prefix
3. **Images → public prefix** → permanent CDN URL returned to frontend
4. **PDFs, videos, private docs → private prefix** → backend proxy URL returned
5. **Frontend never has AWS credentials**
6. **`.env` is in `.gitignore`** — verify this

## Step 5 — Verify end-to-end

After implementation, test with:
```bash
# Check a file is in S3
AWS_DEFAULT_REGION=<region> aws s3 ls s3://<bucket>/public/ --recursive

# Verify CloudFront serves it
curl -I https://<cdn-domain>/public/<key>
# Should return: HTTP/2 200

# If 403, check:
# 1. Bucket policy allows CloudFront distribution ARN
# 2. KMS key policy allows cloudfront.amazonaws.com kms:Decrypt (if bucket uses KMS)
# 3. OAC is attached to the CloudFront origin
```

## Common pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| 403 from CloudFront | KMS key blocks CF | Add `kms:Decrypt` for `cloudfront.amazonaws.com` to KMS key policy |
| 403 from CloudFront | No bucket policy | Apply the policy AWS generates when you attach OAC |
| Credentials not loading in .NET | `GetAWSOptions()` ignores `AccessKeyId` in config | Use `BasicAWSCredentials` directly (see Program.cs above) |
| Old URLs break after upload | Storing full URL in DB | Store only the key; reconstruct URL with `GetPublicUrl()` |
| Private files indexed by Google | Wrong prefix | Ensure private docs go to `private/` not `public/` |
