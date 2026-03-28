# Nightly Memory Repack Template

## What to Remember (Long-Term)

### 1. Active Projects
- Project ID, name, status
- Key technical decisions (ADRs)
- Current blockers
- Next actions

### 2. Technical Knowledge
- Stack preferences
- Patterns and conventions
- Hard-learned lessons (the "don't do this again" moments)
- Working configurations

### 3. Preferences & Boundaries
- Communication style
- Things that annoy Jan
- Things that work well
- Explicit preferences stated

### 4. Standing Instructions
- Recurring tasks
- Monitoring/checking duties
- Special behaviors

### 5. Relationships & Context
- Key integrations (Discord, etc.)
- Team/guild members
- External dependencies

---

## Daily → Memory Flow

```
memory/YYYY-MM-DD.md (raw daily log)
        ↓
[Review each night]
        ↓
MEMORY.md (distilled long-term)
projects/PROJECTS.md (project registry)
projects/<ID>/ (project-specific details)
context/ (technical context, patterns)
```

## Review Checklist (Every Night)

- [ ] Read today's memory file
- [ ] Update active projects in PROJECTS.md
- [ ] Move completed projects to "Archived"
- [ ] Extract technical decisions worth keeping
- [ ] Update any changed preferences
- [ ] Check for new standing instructions
- [ ] Remove outdated MEMORY.md entries (mark with ~~strikethrough~~ first, delete after 7 days)
- [ ] Update "Last Updated" date

---

## Structure Standards

### PROJECTS.md entries:
```markdown
### PRJ-XXX: Project Name
**Status:** active | paused | archived
**Started:** YYYY-MM-DD
**Goal:** One sentence
**Stack:** Language/Framework
**Key Files:** path/to/main.md
**Blockers:** Any?
**Next:** What's next
```

### Memory entries:
- **Dated events:** Use ISO dates (2026-03-27)
- **Decisions:** Link to context file if detailed
- **Preferences:** Bold the preference, context after
