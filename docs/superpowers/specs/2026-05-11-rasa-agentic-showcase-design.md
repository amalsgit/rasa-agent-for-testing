# Rasa Agentic Showcase — Design

**Date:** 2026-05-11
**Status:** Draft, post-grilling

## Goal

Extend `rasa-agent-for-testing` into a feature showcase that exercises
every Rasa agentic capability reachable with **zero infrastructure
setup** — relying only on already-running, publicly accessible MCP
servers and on features that run inside the Rasa process itself.

## Non-goals

- **A2A external sub-agents** — no free public A2A endpoint and the user
  does not want to host one.
- **OAuth- or token-authenticated MCP servers** — preserves zero-setup;
  the auth=oauth / pre-issued-token paths in `endpoints.yml` are not
  demoed.
- **Multi-LLM routing strategies** (`simple-shuffle`, `least-busy`, etc.) —
  Rasa docs explicitly warn against using these with mixed models, and
  same-model multi-deployment requires infra (Azure regions / a proxy /
  multiple providers). We instead demo the **resilience knobs** on a
  single-model group (see below).
- **Slot validation action** and **dynamic ask action** — dropped from
  the showcase. The `book_demo` use case is driven entirely by a
  task-specific ReAct sub-agent (LLM workflow), so the classic
  `collect`-step hook points for these actions don't apply.

## Constraints

- Only **no-auth, cloud-hosted MCP servers**: DeepWiki
  (`https://mcp.deepwiki.com/mcp`) and Context7
  (`https://mcp.context7.com/mcp`). Both verified to work anonymously
  during spec design.
- All sub-agents are **ReAct, in-process**.
- Existing pinned dependencies (`uv.lock`, `pyproject.toml`) should not
  need to change beyond `rasa-pro` itself.

## Feature coverage matrix

| Rasa agentic feature                          | Where it's demoed                                |
|-----------------------------------------------|--------------------------------------------------|
| SearchReadyLLMCommandGenerator                | `config.yml` (kept)                              |
| FlowPolicy                                    | `config.yml` (kept)                              |
| EnterpriseSearchPolicy (RAG)                  | `config.yml` + `./docs` (kept)                   |
| Contextual response rephraser                 | `endpoints.yml` `nlg:` block (kept)              |
| Multiple `model_groups`                       | `endpoints.yml` — three groups for distinct purposes |
| Router resilience config (retries / cooldown) | `endpoints.yml` — on the primary model group     |
| Multiple MCP servers                          | `endpoints.yml` `mcp_servers:` — deepwiki + context7 |
| General-purpose ReAct sub-agent               | `sub_agents/deepwiki_github/`, `sub_agents/library_docs/` |
| Task-specific ReAct sub-agent (slot-filling)  | `sub_agents/book_demo_agent/` (NEW)              |
| Tool filtering on a sub-agent                 | `sub_agents/deepwiki_github/` (filter to `ask_question`) |
| ReAct sub-agent w/ custom Python tools        | `sub_agents/code_buddy/` (NEW)                   |
| MCP tool called directly from a flow          | `data/flows/system/lookup_library_id.yml` (NEW)  |
| Custom action (regular)                       | `actions/action_human_handoff.py` (kept)         |
| Capability announcement on every conversation | `utter_greet` response (UPDATED)                 |
| E2E tests                                     | `tests/e2e/*.yml` (NEW)                          |

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

Both anonymous HTTP. No auth, env vars, or token wiring.

Verified during design:
- **DeepWiki** exposes `read_wiki_structure`, `read_wiki_contents`,
  `ask_question`.
- **Context7** exposes `resolve-library-id`, `query-docs`. Anonymous
  works; an optional API-key header exists for rate limit relief but is
  not used here.

### Model groups (`endpoints.yml`)

Three groups, each demonstrating a distinct usage:

```yaml
model_groups:
  - id: openai-gpt-5-1
    models:
      - provider: openai
        model: gpt-5.1-2025-11-13
        reasoning_effort: "none"
        timeout: 15
    router:
      num_retries: 2
      allowed_fails: 2
      cooldown_time: 10
  - id: openai-gpt-5-mini
    models:
      - provider: openai
        model: gpt-5-mini-2025-08-07
        reasoning_effort: "minimal"
        timeout: 15
  - id: openai-embeddings
    models:
      - provider: openai
        model: text-embedding-3-large
```

- `openai-gpt-5-1` — primary; carries the resilience config
  (`num_retries` / `allowed_fails` / `cooldown_time`). Used by the
  command generator and the rephraser, so the demo lives on hot paths.
- `openai-gpt-5-mini` — cheaper model used by `EnterpriseSearchPolicy`.
  Shows that different components reference different groups.
- `openai-embeddings` — embeddings, referenced by
  `EnterpriseSearchPolicy`.

Note: we do **not** define a `routing_strategy`. With only OpenAI
available, the docs' guidance ("designed to distribute requests across
different deployments of the same model") cannot be honored honestly, so
we limit the demo to the resilience knobs that always apply.

### Sub-agents

#### `deepwiki_github/` (UPDATED)
General-purpose ReAct sub-agent over DeepWiki.

- **Tool filter** restricts the agent to `ask_question` only;
  `read_wiki_structure` and `read_wiki_contents` are excluded. This is
  the tool-filtering demo. The chosen filter is load-bearing — without
  it the agent could perform low-level wiki crawls; restricted, it can
  only ask high-level Q&A questions, which is exactly what the existing
  `ask_about_repo` flow needs.
- Driven by the existing `ask_about_repo` flow (kept).

#### `library_docs/` (NEW)
General-purpose ReAct sub-agent over Context7.

- No tool filter (Context7 only has two tools, both required for any
  real query).
- Custom prompt frames the agent: "given a library name and a question,
  return a concise, doc-grounded answer; cite the source URL".
- Driven by the new `ask_library_docs` flow.

#### `code_buddy/` (NEW)
General-purpose ReAct sub-agent that mixes Context7 MCP tools with
**custom Python tools**.

- MCP source: Context7.
- Custom Python tools registered via `get_custom_tool_definitions`:
  - `count_lines(text: str) -> int`
  - `regex_search(pattern: str, text: str) -> list[str]`
- These tools are intentionally trivial — their purpose is to exercise
  the custom-tool registration surface, not to be useful. The README
  notes this explicitly so readers don't search for cleverness that
  isn't there.
- Driven by the new `code_assist` flow.

#### `book_demo_agent/` (NEW)
**Task-specific** ReAct sub-agent for slot-filling.

- `exit_if` conditions cover `demo_name`, `demo_email`, `demo_time`
  — the agent exits when all three are filled.
- No MCP tools; the agent's job is conversation + slot filling. The
  auto-generated `set_slot_<name>` tools are sufficient.
- Driven by the new `book_demo` flow.

### Flows

All new flows live under `data/flows/system/` or `data/flows/general/`
following the existing split.

- **`ask_library_docs`** — collects a library name and a question,
  delegates to `library_docs`, returns the answer.
- **`lookup_library_id`** — direct MCP call demo.
  - Collects two slots: `library_name`, `library_question`.
  - A flow `call` step invokes Context7's `resolve-library-id` tool with
    both parameters mapped from those slots.
  - Result stored in `resolved_library_id`; utterance reads it back.
  - No sub-agent involved — this is the only flow that reaches an MCP
    tool directly from a flow step.
- **`code_assist`** — collects `code_question`, delegates to
  `code_buddy`.
- **`book_demo`** — delegates immediately to `book_demo_agent` (no
  `collect` steps). The task-specific agent drives the conversation
  until all three slots are filled, then the flow utters a thank-you
  response. No backend booking happens.

Existing flows (`greet`, `help`, `feedback`, `handoff`, `ask_about_repo`)
remain.

### Custom actions

- `action_human_handoff` (kept) — covers the "regular custom action"
  feature.
- **No new custom actions.** `validate_book_demo` and
  `action_ask_demo_time` from the prior spec are dropped, since the
  `book_demo` flow no longer has classic `collect` steps for them to
  attach to.

### Slots

New slots (in the appropriate domain file):
- `library_name: text`
- `library_question: text`
- `resolved_library_id: text` (filled by `lookup_library_id` flow's
  `call` step)
- `code_question: text`
- `demo_name: text`
- `demo_email: text`
- `demo_time: text`

### Responses

- **`utter_greet` is updated** to introduce the showcase capabilities at
  the start of every conversation. One concise paragraph listing the
  things the user can ask about (e.g., "ask about a public GitHub repo,
  look up library docs, get code-style help, or book a demo").
- One thin response per new flow.
- Rephraser-friendly response variations on the `book_demo` confirmation.
- Existing non-greet responses untouched.

### Tests (`tests/e2e/`)

One happy-path E2E test per new flow:
- `test_ask_library_docs.yml`
- `test_lookup_library_id.yml`
- `test_code_assist.yml`
- `test_book_demo.yml`

MCP tool calls and sub-agent responses are stubbed in the test fixtures
so the suite is hermetic and does not depend on the public MCP servers
being up. The existing `ask_about_repo` E2E test (if present) is
preserved; if absent it is added for parity.

## Data flow examples

**`lookup_library_id` (direct MCP call):**
```
user → command generator → start flow
  → collect library_name
  → collect library_question
  → call step: context7.resolve-library-id(
        libraryName=library_name,
        query=library_question
    )
      → result mapped to resolved_library_id
  → utter "resolved_library_id is {resolved_library_id}"
  → end
```

**`book_demo` (task-specific ReAct):**
```
user → command generator → start flow
  → delegate to book_demo_agent
      → ReAct loop with auto-generated
        set_slot_demo_name, set_slot_demo_email, set_slot_demo_time
      → exits when exit_if conditions met
  → utter thank-you
  → end
```

## Error handling

- MCP server unreachable: `call` step / sub-agent surfaces an error;
  flows fall back to `pattern_internal_error`. No custom error UX — we
  rely on default Rasa patterns to keep the showcase clean.
- LLM transient failure on `openai-gpt-5-1`: covered by `num_retries` /
  `allowed_fails` / `cooldown_time` — this is the resilience demo.
- Task-specific agent failing to extract slots: agent loops within its
  own budget; if it gives up, the flow's default error pattern handles
  it.

## Migration / rollout

Single PR, applied in this order:
1. `endpoints.yml` — add `context7` MCP server; add resilience config to
   `openai-gpt-5-1` group.
2. `config.yml` — no changes needed (command generator still references
   `openai-gpt-5-1`, which now carries resilience config).
3. Sub-agents — add `library_docs/`, `code_buddy/`, `book_demo_agent/`;
   update `deepwiki_github/` with the tool filter.
4. Domain — add new slots, update `utter_greet`, add new responses.
5. Flows — add `ask_library_docs`, `lookup_library_id`, `code_assist`,
   `book_demo`.
6. E2E tests.
7. README — short section per feature, pointing at file paths.

Verification:
`uv sync` → `uv run rasa data validate` → `uv run rasa train`
→ run E2E tests. No new dependencies expected.

## Open questions

None at spec time. Any discovered during implementation get raised back
before deviating from this doc.
