import re
from typing import Any, Dict, List

from rasa.agents.protocol.mcp.mcp_open_agent import MCPOpenAgent
from rasa.agents.schemas import AgentToolContext, AgentToolResult


class CodeBuddyAgent(MCPOpenAgent):
    def get_custom_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "count_lines",
                    "description": "Count the number of lines in the given text.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to count lines of.",
                            },
                        },
                        "required": ["text"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self._count_lines,
            },
            {
                "type": "function",
                "function": {
                    "name": "regex_search",
                    "description": "Return all non-overlapping matches of pattern in text.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string"},
                            "text": {"type": "string"},
                        },
                        "required": ["pattern", "text"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
                "tool_executor": self._regex_search,
            },
        ]

    async def _count_lines(
        self, arguments: Dict[str, Any], _tool_context: AgentToolContext
    ) -> AgentToolResult:
        text = arguments["text"]
        return AgentToolResult(
            tool_name="count_lines", result=str(len(text.splitlines()))
        )

    async def _regex_search(
        self, arguments: Dict[str, Any], _tool_context: AgentToolContext
    ) -> AgentToolResult:
        try:
            matches = re.findall(arguments["pattern"], arguments["text"])
        except re.error as exc:
            return AgentToolResult(
                tool_name="regex_search", is_error=True, error_message=str(exc)
            )
        return AgentToolResult(tool_name="regex_search", result=str(matches))
