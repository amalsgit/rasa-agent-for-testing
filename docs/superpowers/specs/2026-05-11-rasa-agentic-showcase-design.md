# Rasa Agentic Showcase — Design

**Date:** 2026-05-11
**Status:** Draft for review

## Goal

Extend the existing `rasa-agent-for-testing` project into a feature showcase
that exercises every Rasa agentic capability reachable with **zero
infrastructure setup** — i.e., relying only on already-running, publicly
accessible MCP servers and on features that run inside the Rasa process
itself.

## Non-goals

- **A2A external sub-agents** — explicitly out of scope; no free public A2A
  endpoint is available and the user does not want to host one.
- **OAuth- or token-authenticated MCP servers** — out of scope to preserve
  zero-setup. The auth=oauth / pre-issued-token paths in `endpoints.yml` are
  not demoed.
- New domain logic. This is a technical showcase; flows can be thin and
  contrived as long as each isolates a feature.

## Constraints

- Only **no-auth, cloud-hosted MCP servers**. Concretely: DeepWiki
  (`https://mcp.deepwiki.com/mcp`) and Context7 (`https://mcp.context7.com/mcp`).
- All sub-agents run **inside the Rasa process** (ReAct), not as external
  services.
- Existing pinned dependencies (`uv.lock`, `pyproject.toml`) should not need
  to change beyond `rasa-pro` itself.

## Feature coverage matrix

| Rasa agentic feature              | Where it's demoed                                  |
|-----------------------------------|----------------------------------------------------|
| SearchReadyLLMCommandGenerator    | `config.yml` (kept as-is)                          |
| FlowPolicy                        | `config.yml` (kept)                                |
| EnterpriseSearchPolicy (RAG)      | `config.yml` + `./docs` (kept)                     |
| Contextual response rephraser     | `endpoints.yml` `nlg:` block (kept)                |
| Multiple `model_groups`           | `endpoints.yml` — primary, fast, router-with-failover |
| Multi-model routing + failover    | `endpoints.yml` `fallback-router` group            |
| Multiple MCP servers              | `endpoints.yml` `mcp_servers:` — deepwiki + context7 |
| General-purpose ReAct sub-agent   | `sub_agents/deepwiki_github/` (kept)               |
| Task-specific ReAct sub-agent     | `sub_agents/library_docs/` (NEW)                   |
| ReAct sub-agent w/ custom Python tools | `sub_agents/code_buddy/` (NEW)                |
| MCP tool called directly from flow| `data/flows/system/lookup_library_id.yml` (NEW)    |
| Slot validation action            | `actions/validate_book_demo.py` (NEW)              |
| Dynamic ask action                | `actions/action_ask_demo_time.py` (NEW)            |
| Custom action (existing)          | `actions/action_human_handoff.py` (kept)           |
| E2E tests                         | `tests/e2e/*.yml` (NEW)                            |

## Components

### MCP servers (`endpoints.yml`)

```yaml
mcp_servers:
  - name: deepwiki
    url: https://mcp.deepwiki.com/mcp
    type: http
  - name: context7
    url: https://mcp.context7.com/mcp
    type: http
```

Both are anonymous HTTP. No auth, env vars, or token wiring.

### Model groups (`endpoints.yml`)

Three groups so we can demonstrate single-model, multi-model, and
failover-routed configurations without changing providers:

- `openai-gpt-5-1` — primary, single model (kept).
- `openai-gpt-5-mini` — fast/cheap, single model (kept).
- `openai-embeddings` — embeddings (kept).
- `chat-router` — NEW. Two models with `router: failover` so the group falls
  back from gpt-5.1 to gpt-5-mini on error/timeout. Used by the
  command generator so the demo is on the hot path.

The `SearchReadyLLMCommandGenerator` switches to `chat-router`. The rephraser
and EnterpriseSearchPolicy stay on their current groups so we still showcase
multiple distinct group references.

### Sub-agents

#### `deepwiki_github/` (kept)
General-purpose ReAct sub-agent. Wraps the entire DeepWiki MCP toolset.
Demoed by the existing `ask_about_repo` flow.

#### `library_docs/` (NEW)
Task-specific ReAct sub-agent against Context7.

- `type: task-specific`
- Tool filter that exposes only Context7's docs-lookup tools
  (`resolve-library-id`, `query-docs`), not every Context7 tool.
- Custom prompt that frames the agent narrowly: "given a library name and a
  question, return a concise, doc-grounded answer; cite the source URL".
- Invoked from the new `ask_library_docs` flow.

#### `code_buddy/` (NEW)
General-purpose ReAct sub-agent that mixes an MCP toolset with **custom
Python tools**.

- MCP source: Context7 (for "what does this library do" questions).
- Custom Python tools (defined inside the sub-agent module):
  - `count_lines(text: str) -> int`
  - `regex_search(pattern: str, text: str) -> list[str]`
  These are intentionally tiny — their purpose is to exercise the
  custom-tool registration surface, not to be useful.
- Invoked from the new `code_assist` flow.

### Flows

All new flows live under `data/flows/system/` (or `general/`, following the
existing split).

- **`ask_library_docs`** — collects a library name and a question, delegates
  to `library_docs` sub-agent, returns the answer. One `collect` step per
  input; one sub-agent call; one response.
- **`lookup_library_id`** — collects a library name from the user, then uses
  a `call` step that invokes Context7's `resolve-library-id` MCP tool
  **directly** (no sub-agent). Result is mapped into a slot and read back.
  This is the only flow that calls an MCP tool without going through a
  sub-agent.
- **`code_assist`** — free-form question slot, delegates to `code_buddy`.
- **`book_demo`** — collects `name`, `email`, `preferred_time`.
  - `validate_book_demo` validation action rejects invalid emails and past
    times.
  - `action_ask_demo_time` is a dynamic-ask action that suggests two
    times based on the current weekday.
  - On completion, a thank-you response is sent. No real booking happens.

Existing flows (`greet`, `help`, `feedback`, `handoff`, `ask_about_repo`)
remain.

### Custom actions

- `action_human_handoff` (kept).
- `validate_book_demo` (NEW) — slot validation.
- `action_ask_demo_time` (NEW) — dynamic ask.

### Slots

New slots, all in the appropriate domain file:
- `library_name: text`
- `library_question: text`
- `resolved_library_id: text` (filled by `lookup_library_id` flow)
- `code_question: text`
- `demo_name: text`
- `demo_email: text` (validated)
- `demo_time: text` (dynamic-ask + validated)

### Responses

One thin response per new flow plus rephraser-friendly variations for the
`book_demo` confirmation. Existing responses untouched.

### Tests (`tests/e2e/`)

One happy-path E2E test per new flow:
- `test_ask_library_docs.yml`
- `test_lookup_library_id.yml`
- `test_code_assist.yml`
- `test_book_demo.yml`

MCP tool calls and sub-agent responses are stubbed in the test fixtures so
the suite is hermetic and doesn't depend on the public MCP servers being up.
The existing `ask_about_repo` happy-path test (if any) is preserved; if
absent it's added for parity.

## Data flow examples

**`lookup_library_id` (direct MCP call):**
```
user → command generator → start flow
  → collect library_name
  → call step: context7.resolve-library-id(name=library_name)
      → result mapped to resolved_library_id
  → utter "resolved_library_id is {resolved_library_id}"
  → end
```

**`ask_library_docs` (task-specific ReAct):**
```
user → command generator → start flow
  → collect library_name + library_question
  → invoke sub-agent library_docs
      → ReAct loop over context7 docs tools
      → returns answer
  → utter answer
  → end
```

## Error handling

- MCP server unreachable: the `call` step / sub-agent returns an error;
  flows fall back to `pattern_internal_error`. No custom error UX — relying
  on default Rasa patterns keeps the showcase clean.
- LLM timeout on `chat-router`: failover takes over silently. This is the
  point of including it.
- Slot validation failure in `book_demo`: handled by the validation action
  returning an explanation; default re-ask kicks in.

## Migration / rollout

Single PR. Order of changes inside the PR:
1. `endpoints.yml` — add `context7`, `chat-router`.
2. `config.yml` — point command generator at `chat-router`.
3. Sub-agents — add `library_docs/`, `code_buddy/`.
4. Slots/responses — domain additions.
5. Flows — add the four new flows.
6. Actions — `validate_book_demo`, `action_ask_demo_time`.
7. E2E tests.
8. README update — short section per feature, pointing to where it lives.

`uv sync` → `uv run rasa data validate` → `uv run rasa train` → run E2E
tests. No new dependencies expected.

## Open questions

None at spec time. Any discovered during implementation get raised back
before deviating from this doc.
