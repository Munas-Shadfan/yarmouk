---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, write evals to test a skill, or improve a skill description for better triggering accuracy.
metadata:
  version: 1.0.0-copilot
---

# Skill Creator

A skill for creating and iteratively improving skills in the `aqlaanskills` repo.

**Environment:** GitHub Copilot in VS Code — no subagents, no `claude` CLI, no browser. All iteration happens in this chat.

## Validate a skill

```bash
uv run --with pyyaml python3 skills/skill-creator/scripts/quick_validate.py skills/<skill-name>
```

---

## Skill Structure

```
skills/<skill-name>/
├── SKILL.md              # required — frontmatter + instructions
├── evals/
│   └── evals.json        # test cases and assertions
├── scripts/              # executable helpers bundled with the skill
├── references/           # docs loaded into context as needed
└── assets/               # templates, icons, other static files
```

### SKILL.md frontmatter (required)

```yaml
---
name: skill-name
description: When to trigger AND what it does. Be specific and slightly "pushy" — Claude undertriggers by default.
metadata:
  version: 1.0.0
---
```

### Progressive disclosure

Skills use three loading levels:

1. **name + description** — always in context (~100 words)
2. **SKILL.md body** — in context when skill triggers (keep under 500 lines)
3. **Bundled resources** — loaded on demand (scripts run without loading)

Keep SKILL.md under 500 lines. If approaching the limit, move content to `references/` and add clear pointers in SKILL.md.

---

## Creating a skill

### 1. Capture intent

Understand what the skill should do:

- What task does it enable?
- When should it trigger? (specific phrases, contexts)
- What is the expected output format?
- Are there objectively verifiable outputs that could have test assertions?

If the user has been working through a task in this chat, extract the workflow from the conversation history first — tools used, sequence of steps, corrections made, input/output formats.

### 2. Research and interview

Ask about edge cases, input/output formats, example files, success criteria, dependencies. Check if scripts already exist in the repo that could be bundled.

### 3. Write SKILL.md

Fill in:

- **name** — skill identifier (kebab-case)
- **description** — trigger conditions + what it does. Include both explicit requests and implicit ones. Make it slightly pushy.
- **body** — instructions, patterns, output formats, references to bundled scripts

#### Writing style

- Use imperative form for instructions
- Explain the *why* behind rules — don't just write ALWAYS or NEVER
- Use theory of mind — make it general, not narrowly fitted to examples
- Define output formats explicitly with templates where helpful

### 4. Write evals

Create 2–5 realistic test prompts in `evals/evals.json`:

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "A realistic user prompt",
      "expected_output": "Description of what a good response looks like",
      "assertions": [
        "Checks X",
        "Does not do Y",
        "Output contains Z"
      ],
      "files": []
    }
  ]
}
```

See `references/schemas.md` for full schema.

Make prompts realistic — specific, with context, casual phrasing. Bad: `"Do an SEO audit"`. Good: `"our blog traffic dropped 40% after we moved to Next.js last month, help"`.

### 5. Test in chat

For each eval prompt, run it here in Copilot chat with the skill in context. Evaluate:

- Does the output match `expected_output`?
- Does it pass all `assertions`?
- Compare against what the response would be without the skill

### 6. Iterate

Based on test results:

- Generalize from failures — don't overfit to specific examples
- Remove instructions that aren't pulling their weight
- Add bundled scripts to `scripts/` if the same helper code was reinvented across test runs
- Update assertions in `evals/evals.json` to capture new requirements

Repeat steps 5–6 until satisfied.

---

## Improving an existing skill

1. Read the current `SKILL.md` and `evals/evals.json`
2. Validate: `uv run --with pyyaml python3 skills/skill-creator/scripts/quick_validate.py skills/<name>`
3. Run eval prompts in chat and assess against assertions
4. Identify patterns in failures — structural or missing coverage?
5. Rewrite SKILL.md, update assertions, add scripts if needed
6. Validate again and re-run evals

---

## Description optimization (manual)

The description field is the primary trigger mechanism. To improve it:

1. Write 10–15 test queries — mix of should-trigger and should-not-trigger
2. For each query, assess whether the current description would cause triggering
3. Focus on near-misses: queries that share keywords but should NOT trigger, and natural phrasings that SHOULD trigger but currently wouldn't
4. Rewrite description to cover gaps without over-broadening
5. Re-test the query set

---

## Committing a skill

After creating or improving a skill:

1. Add it to `CLAUDE.md`: `@skills/<name>/SKILL.md`
2. Validate: `uv run --with pyyaml python3 skills/skill-creator/scripts/quick_validate.py skills/<name>`
3. Commit and push:

```bash
git add -A && git commit -m "skill: <name> — <what changed>" && git push
```
