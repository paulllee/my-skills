---
name: search-docs
description: |
  Look up documentation for any library or tool. Use this when the user asks to look up docs, check an API, or asks how to use a library. Trigger phrases: "look up docs for", "check the X docs", "how do I use X", "/search-docs". Uses WebFetch/curl against official docs.
argument-hint: "(query) [library-name]"
---

# search-docs

Look up documentation for the query in `$ARGUMENTS`. Parse out the library name (last arg if provided, otherwise infer from query).

## Lookup Strategy

1. Use `WebFetch` against the library's official docs URL.
2. If WebFetch is unavailable or times out, use `curl -sL` via Bash.
3. If the docs URL is unknown, use `WebSearch` to find it first.

Never fabricate versions, API signatures, or behavior. Say so if authoritative docs cannot be found.

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

- **WebFetch blocked or times out:** Fall back to `curl -sL [url]` via Bash.
- **Docs URL unknown:** Use WebSearch to find the official docs URL, then WebFetch it.
- **No authoritative source found:** Tell the user clearly — do not guess or fabricate API details.
