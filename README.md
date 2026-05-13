# Test this out on hello rasa:

[![Launch on Hello Rasa Prod](launch-prod.svg)](https://hello.rasa.com/go?repo=amalsgit/rasa-agent-for-testing)
[![Launch on Hello Rasa Staging](launch-staging.svg)](https://staging.hello.rasa.com/go?repo=amalsgit/rasa-agent-for-testing)
[![Launch on Hello Rasa Localhost](launch-localhost.svg)](http://localhost:5173/go?repo=amalsgit/rasa-agent-for-testing)


# Basic Rasa Template

A simple, general-purpose conversational agent template that provides essential conversational capabilities.

## Install and run (with uv)

This repo pins dependencies in `uv.lock`. Use [uv](https://docs.astral.sh/uv/) so installs match that lockfile.

1. **Install uv** (if you do not have it yet): follow the [install instructions](https://docs.astral.sh/uv/getting-started/installation/).

2. **Create the environment and install dependencies** from the lockfile:

   ```bash
   uv sync
   ```

   This reads `uv.lock` and installs the exact versions recorded there (including `rasa-pro` from `pyproject.toml`). Python follows `.python-version` (3.10) when uv creates a project virtual environment.

3. **Run Rasa via uv** so commands use that environment:

   ```bash
   # Validate configuration and data
   uv run rasa data validate

   # Train a model
   uv run rasa train

   # Talk to the assistant 
   uv run rasa inspect --nextgen

   # Run the HTTP server (after training, or with a trained model path)
   uv run rasa run
   ```

   Add flags as needed (for example `uv run rasa train --fixed-model-name my-model`).

If you change dependencies in `pyproject.toml`, run `uv lock` to refresh `uv.lock`, then `uv sync` again.

## 🚀 What's Included

This template provides a foundation for building conversational agents with:
- **Basic conversational flows**: Greetings, help, feedback, and human handoff
- **Help system**: Users can ask for assistance and get guided responses
- **Public GitHub repository Q&A**: Ask about an `owner/repo` on GitHub; a **ReAct sub-agent** (`sub_agents/deepwiki_github/`) calls the **DeepWiki** MCP server so answers stay grounded in that repository's documentation
- **Library documentation Q&A**: Ask about a software library; a **ReAct sub-agent** (`sub_agents/library_docs/`) calls the **Context7** MCP server, resolves the library id, and fetches docs to answer (`data/general/ask_library_docs.yml`)
- **Library id lookup via direct MCP `call` step**: Skip the sub-agent loop and invoke a Context7 tool straight from a flow (`data/general/lookup_library_id.yml`)
- **Code assist with custom Python tools**: A **ReAct sub-agent** (`sub_agents/code_buddy/`) extends `MCPOpenAgent` with two Python tools — `count_lines` and `regex_search` — alongside Context7 docs lookup (`data/general/code_assist.yml`)
- **Book a demo (task-specific sub-agent)**: A **task-specific ReAct sub-agent** (`sub_agents/book_demo_agent/`) collects name, email, and time via auto-generated `set_slot_*` tools driven by `exit_if` on the flow's `call` step (`data/general/book_demo.yml`)
- **Feedback collection**: Gather user feedback to improve the agent
- **Human handoff**: Seamlessly transfer conversations to human agents when needed

The E2E tests under `tests/e2e_test_cases/without_stub/` call the live Context7 and DeepWiki MCP servers — they may be slow or flaky if those services are unavailable.

## Next-gen Inspector trace scenarios

This project includes explicit `inspector_*` diagnostic flows for manually testing
the next-gen Inspector. Run the assistant with:

```bash
uv run rasa inspect --nextgen
```

When validating or training these flows from the command line, load endpoints so
direct MCP call steps can resolve their configured servers:

```bash
uv run rasa data validate --endpoints endpoints.yml
uv run rasa train
```

The diagnostic prompts are also listed in the greeting and help responses under
an "Inspector testing" section. They are intentionally literal so they can be
reused later in Playwright tests.

| Trigger prompt | Scenario | Expected Inspector surface | Expected UI signal | Stability |
| --- | --- | --- | --- | --- |
| `"inspector test direct mcp success"` | Direct Context7 MCP tool call from a flow | Events, Event details, Memory | `mcp_tool_executed` row for `resolve-library-id`; `inspector_resolved_library_id` slot set | Stable when Context7 is reachable |
| `"inspector test custom tool success"` | ReAct sub-agent calls a diagnostic Python tool | Events, Event details, History | `agent_started` / `agent_completed`; tool row for `inspector_success_marker` | Stable when LLM/tool loop chooses the instructed tool |
| `"inspector test custom tool failure"` | ReAct sub-agent calls a diagnostic Python tool that returns `is_error=True` | Events, Event details, History | Tool error row for `inspector_failure_marker` with error details | Stable when LLM/tool loop chooses the instructed tool |
| `"inspector test agent success"` | Existing `library_docs` ReAct sub-agent completes normally | Events, History | Agent lifecycle row and Completed timeline item | Stable when Context7 is reachable |
| `"inspector test memory and buttons"` | Slot collection, buttons, custom payload, and rephrased bot response | Memory, Bot details, Events | `inspector_memory_note` and `inspector_trace_mode` slots; buttons/custom payload on bot response | Stable |
| `"inspector test agent timeout"` | ReAct sub-agent with `tool_timeout: 1` calls live Context7 | Events, Event details, History | Timeout or failure details on agent/tool rows; active or failed agent timeline state | Live edge; behavior depends on Context7 latency |
| `"inspector test direct mcp failure"` | Direct MCP call against `inspector_unreachable_mcp` | Events, Event details | MCP connection failure from a flow call step | Live edge; intentionally unreachable local endpoint |
| `"inspector test action failure"` | Custom action raises a real exception | Events, Event details | Action failure details for `action_inspector_raise_failure`; conversation may require restart | Stable failure probe |

Live-edge scenarios are diagnostic probes, not reliable assistant behavior tests.
They intentionally depend on network state, Context7/DeepWiki behavior, and short
timeouts. If a raw action failure leaves the conversation in an error state,
restart the conversation before running the next scenario.

Do not add an always-on ReAct sub-agent that points at an unreachable MCP server:
ReAct sub-agents connect to their MCP servers during Inspector startup, so that
configuration prevents the Inspector from loading. To manually verify that
startup-failure path, temporarily add a sub-agent connected to
`inspector_unreachable_mcp`, run `uv run rasa inspect --nextgen`, confirm startup
fails with MCP connection details, and then remove the sub-agent again.

### Future Inspector E2E targets

These manual traces are intended to become next-gen Inspector Playwright coverage
later in `rasa-private/rasa/core/channels/inspector-nextgen/e2e/tests`.

| Automation priority | Trigger prompt | Tracker event type | Inspector view | Assertion target |
| --- | --- | --- | --- | --- |
| High | `"inspector test direct mcp success"` | `mcp_tool_executed`, `slot` | Events, Event details, Memory | Tool name, arguments/result panel, resolved slot |
| High | `"inspector test custom tool failure"` | `agent_started`, `mcp_tool_executed`, `agent_completed` | Events, Event details, History | Tool error dot and error message details |
| High | `"inspector test action failure"` | `action` with failure metadata | Events, Event details | Action failure affordance and error message |
| Medium | `"inspector test memory and buttons"` | `slot`, `bot` | Memory, Bot details | Slot grouping, buttons, custom payload, rephrase details |
| Medium | `"inspector test agent success"` | `agent_started`, `agent_completed` | History | Completed agent timeline entry |
| Medium | `"inspector test agent timeout"` | `agent_started`, failure or timeout metadata | Events, History | Timeout/failure presentation without hanging the UI |
| Medium | `"inspector test direct mcp failure"` | `mcp_tool_executed` or internal error flow metadata | Events, Event details | Direct MCP failure details |
| Low | Manual unreachable ReAct sub-agent startup probe | Startup failure before tracker events | Startup/error handling | Inspector startup failure reporting for unreachable sub-agent MCP server |

## 📁 Directory Structure

```
├── actions/          # Custom Python logic for agent actions
├── data/            # Conversational flows and training data
├── domain/          # Agent configuration (slots, responses, actions)
├── docs/            # Knowledge base documents (optional)
├── prompts/         # LLM prompts for enhanced responses
├── sub_agents/      # ReAct sub-agent configs (e.g. DeepWiki MCP integration)
├── endpoints.yml    # MCP servers, model groups, NLG, etc.
└── config.yml       # Training pipeline configuration
```

