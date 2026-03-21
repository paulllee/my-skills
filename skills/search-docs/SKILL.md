---
name: search-docs
description: |
  Look up documentation for any library or tool. Use this when the user asks to look up docs, check an API, or asks how to use a library. Trigger phrases: "look up docs for", "check the X docs", "how do I use X", "/search-docs". Uses `WebFetch`/`WebSearch` tools; falls back to `Bash` (curl) if WebFetch is unavailable.
argument-hint: "(query) [library-name]"
---

# search-docs

Look up documentation for the query in `$ARGUMENTS`. Parse out the library name (last arg if provided, otherwise infer from query).

## Lookup Strategy

1. **Resolve the URL** — if the official docs URL is unknown, use `WebSearch` to find it first (up to 2 searches). If no authoritative URL is found after 2 searches, tell the user and stop.
2. **Fetch with `WebFetch`** — use the resolved URL.
3. **Fallback to curl** — if `WebFetch` is unavailable or times out, use the `Bash` tool to run `curl -sL [url]`.
4. **Give up cleanly** — if no authoritative source can be retrieved after the above steps, tell the user clearly and stop. Do not guess or fabricate API details.

Never fabricate versions, API signatures, or behavior.

## Output

```
**Source:** [URL or "Context7 MCP"]
**Library:** [name] [version if known]

[relevant excerpt]

**Example:**
[code example if available]
```

Keep it concise — no padding, no restating the question.

## Examples

**Example 1**
User: `/search-docs how to mock in pytest`
Claude: Fetches the pytest docs, returns the `monkeypatch` fixture section with a usage example.

**Example 2**
User: `/search-docs useEffect cleanup react`
Claude: Fetches the React docs, returns the `useEffect` cleanup pattern with a code snippet.

**Example 3**
User: `/search-docs retry policy polly`
Claude: Fetches the Polly (.NET) docs, returns the `RetryPolicy` API with a configuration example.

## Troubleshooting

| Symptom | Fix |
|---|---|
| WebFetch blocked or times out | Use the `Bash` tool to run `curl -sL [url]` as fallback |
| Docs URL unknown | Use `WebSearch` to find the official docs URL, then `WebFetch` it |
| No authoritative source found after 2 searches | Tell the user clearly — do not guess or fabricate API details |
