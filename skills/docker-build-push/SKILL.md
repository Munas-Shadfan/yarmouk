---
name: docker-build-push
description: Build and push Docker images to GHCR. Automatically runs a security audit before every build/push and blocks on any issues. If docker setup is missing, scaffolds VERSION, docker/, Dockerfiles, and build-and-push.sh. If already set up, bumps the version and pushes. Use whenever the user says "build and push", "release", "deploy docker", or "bump version".
argument-hint: "[patch|minor|major]  (default: patch)"
allowed-tools: Read, Write, Bash(cat *), Bash(echo *), Bash(ls *), Bash(mkdir *), Bash(chmod *), Bash(bash *), Bash(docker *), Bash(git *), Bash(grep *), Bash(stat *)
metadata:
  version: 1.0.5
---

# Docker Build & Push

## Overview

Full Docker release lifecycle with a mandatory security audit gate:

```
Security Audit → [BLOCK if issues] → Version Bump → Build & Push → Git Commit
```

Scripts live in this skill folder and are always run from the **project root**:
- `scripts/security-audit.sh` — pre-flight security check
- `scripts/build-and-push.sh` — version bump + docker build/push

---

## Step 1 — Load Environment

Source the project `.env` if it exists:

```bash
[ -f .env ] && source .env
```

---

## Step 2 — Run Security Audit (MANDATORY)

Always run before anything else. This will BLOCK if there are issues:

```bash
bash ~/.claude/skills/docker-build-push/scripts/security-audit.sh
```

If exit code is non-zero → **stop immediately**, report the issues, do NOT proceed.

To run in strict mode (warnings also block):
```bash
bash ~/.claude/skills/docker-build-push/scripts/security-audit.sh --strict
```

---

## Step 3 — Detect Project State

```bash
ls docker/build-and-push.sh 2>/dev/null && echo "EXISTS" || echo "MISSING"
ls VERSION 2>/dev/null && echo "EXISTS" || echo "MISSING"
```

---

## Step 4A — First-Time Setup (docker/build-and-push.sh is MISSING)

### Gather project info

Infer from `package.json`, `pyproject.toml`, or git remote — or ask:
- **Project name** (image name slug, e.g. `my-app`)
- **GitHub username / org** — default: `husainf4l`
- **Project** — default: `alina`
- **Image** — default: `alina-frontend`
- **Services** (e.g. `backend`, `frontend`, `agent` — or just `app`)

### Scaffold

```bash
echo "1.0.0" > VERSION
mkdir -p docker
```

Create `docker/Dockerfile.<service>` for each service using detected stack.
**Always target `linux/amd64`** — platform is passed at build time via `docker build --platform linux/amd64`, never hard-coded in the `FROM` line.

| Stack    | Base Image                    |
|----------|-------------------------------|
| Node.js  | `node:20-alpine`              |
| Python   | `python:3.12-slim`            |
| .NET     | `mcr.microsoft.com/dotnet/aspnet:<ver>` (multi-stage with `sdk`) |
| Next.js  | multi-stage `node:20-alpine`  |
| Static   | `nginx:alpine`                |
| Unknown  | `ubuntu:24.04`                |

Copy `scripts/build-and-push.sh` from this skill to `docker/build-and-push.sh`, set `PROJECT`, `GITHUB_USER`, and `SERVICES`:

```bash
cp ~/.claude/skills/docker-build-push/scripts/build-and-push.sh docker/build-and-push.sh
chmod +x docker/build-and-push.sh
```

Also copy the security audit script:
```bash
cp ~/.claude/skills/docker-build-push/scripts/security-audit.sh docker/security-audit.sh
chmod +x docker/security-audit.sh
```

---

## Step 4B — Existing Setup (docker/build-and-push.sh EXISTS)

### Bump version

Read current version:
```bash
cat VERSION
```

Apply bump (`$ARGUMENTS` defaults to `patch`):

```
patch  →  MAJOR.MINOR.(PATCH+1)   e.g. 1.0.4 → 1.0.5
minor  →  MAJOR.(MINOR+1).0       e.g. 1.0.4 → 1.1.0
major  →  (MAJOR+1).0.0           e.g. 1.0.4 → 2.0.0
```

Write new version:
```bash
echo "NEW_VERSION" > VERSION
```

---

## Step 5 — Build & Push

All builds **must target `linux/amd64`** regardless of the host machine architecture (e.g. Apple Silicon M-series). The build scripts pass `--platform linux/amd64` automatically.

```bash
SERVICES="backend,frontend" bash docker/build-and-push.sh NEW_VERSION
```

Or using the skill script directly:
```bash
SERVICES="backend,frontend" bash ~/.claude/skills/docker-build-push/scripts/build-and-push.sh NEW_VERSION
```

To build locally without pushing (verify image works):
```bash
docker build --platform linux/amd64 -t myimage:test .
```

---

## Step 6 — Commit Version Bump

```bash
git add VERSION && git commit -m "chore: bump version to NEW_VERSION" && git push
```

---

## Step 7 — Summary

Print:
```
✅ Released vNEW_VERSION to GHCR
   ghcr.io/husainf4l/alina/alina-frontend:NEW_VERSION
   ...
🔗 https://github.com/husainf4l/alina/packages
```

---

## Security Audit — What It Checks

| Check | Blocks? |
|-------|---------|
| `.env` tracked by git | ✅ Yes |
| Secrets in staged files | ✅ Yes |
| Hardcoded API keys in source | ⚠️ Warning (blocks in `--strict`) |
| `.gitignore` missing sensitive patterns | ⚠️ Warning |
| Credential file permissions != 600 | ✅ Yes |
| `GITHUB_TOKEN` not set | ✅ Yes |

---

## Error Handling

| Error | Action |
|-------|--------|
| Security audit fails | Stop immediately, report issues |
| `GITHUB_TOKEN` not set | Stop, print export instruction |
| `docker login` fails | Stop, check token `write:packages` scope |
| `docker build` fails | Stop, print service + last 20 lines |
| `docker push` fails | Suggest `docker logout ghcr.io` + retry |
| `VERSION` missing | Create `1.0.0`, apply bump, continue |
| `Dockerfile` missing | Generate from template for detected stack |

---

## Examples

```
/docker-build-push           → patch bump  (1.0.4 → 1.0.5)
/docker-build-push minor     → minor bump  (1.0.4 → 1.1.0)
/docker-build-push major     → major bump  (1.0.4 → 2.0.0)
```
