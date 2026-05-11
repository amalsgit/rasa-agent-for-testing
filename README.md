# Test this out on hello rasa:

[![Launch on Hello Rasa](https://hello.rasa.com/launch.svg)](https://hello.rasa.com/go?repo=amalsgit/rasa-agent-for-testing)


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

