<!-- bedrot-repo feedback v1 -->
# Feedback Log: bedrot-data-ecosystem

This log records failures that came from this repo's context, so they get fixed where they start. Every
repo in the BEDROT registry has one (registry and full standard: `C:\Users\Earth\.claude\skills\bedrot-repo`).

**What goes here:** errors in agent reasoning, wrong assumptions, serious mistakes during execution, and
failures caused by wrong, missing or incomplete context. Log the entry in the repo that owns the context
to fix. A failure caused by a global skill or the global CLAUDE.md goes in `C:\Users\Earth\.claude\feedback.md`.

**How to log:** in the same turn, before anything else, without asking. Use the script, so the format
stays valid and Blake's words are kept exactly:

    python C:\Users\Earth\.claude\skills\bedrot-repo\scripts\bedrot_repo.py log --repo "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem" --type <type> --name <resource> --verbatim "<Blake's exact words>" --notes "<what went wrong and what to fix>"

Corrections go here, not to Claude's memory. A critical correction saved to memory instead is a failure.

**type values:**

- `skill`: a skill folder in this repo. `name` is the folder name.
- `claude.md`: a CLAUDE.md or AGENTS.md file, at the root or in a subfolder. `name` is the path from the
  repo root. A fix to one of the pair also checks the other.
- `base-doc`: repo documentation such as root markdown files, `docs`, `specs` or `references`. `name` is
  the path from the repo root.
- `other`: anything else, such as a memory file, a hook, settings, a subagent, a slash command, MCP
  config or a CLI tool. `name` is a path or a short label.

**Statuses:** `PENDING` means the fix is not made yet. `IMPLEMENTED (date, commit or note)` means the fix
is made. `REJECTED (date, reason)` means Blake decided not to act on it. Close an entry with
`bedrot_repo.py close`.

**Retention:** at most 30 entries here. `bedrot_repo.py archive` moves closed entries older than 90 days
to `feedback-archive.md`. PENDING entries never move.

**Entry schema:**

```
---
DATE: YYYY-MM-DD
STATUS: PENDING | IMPLEMENTED (YYYY-MM-DD, <commit or note>) | REJECTED (YYYY-MM-DD, <reason>)
type: skill | claude.md | base-doc | other
name: <resource; several of the same type are separated by commas>
Target: <optional: the file and section inside the resource>
Verbatim:
  "<Blake's exact words, never paraphrased>"
Notes:
  <what went wrong, which context was wrong or missing, and what must change>
Logged: YYYY-MM-DD HH:MM
---
```

Leave out Verbatim when the entry comes from an agent observation rather than a quote. Use one type per
entry. A failure that needs fixes in two kinds of resource gets two entries, and each one names the
other's Logged stamp in its Notes as `See also: <stamp>`.

<!-- New entries go below this line, newest first. -->
