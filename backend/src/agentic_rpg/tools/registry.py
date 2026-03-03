"""Central tool registry for LangChain tools."""

from __future__ import annotations

from langchain_core.tools import BaseTool


class ToolRegistry:
    """Central catalog of all LangChain tools available to the agent.

    Tools are registered with a category and can be discovered by name,
    category, or retrieved as a list for LLM binding.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._categories: dict[str, str] = {}  # tool_name -> category

    def register(self, tool: BaseTool, *, category: str) -> None:
        """Register a tool with a category.

        Args:
            tool: A LangChain tool (decorated function or BaseTool instance).
            category: Logical grouping (e.g., character, inventory, world).

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        name = tool.name
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")
        self._tools[name] = tool
        self._categories[name] = category

    def list_tools(self) -> list[dict[str, str]]:
        """Return all registered tools as dicts with name, description, category."""
        return [
            {
                "name": name,
                "description": tool.description,
                "category": self._categories[name],
            }
            for name, tool in self._tools.items()
        ]

    def list_by_category(self, category: str) -> list[dict[str, str]]:
        """Return tools matching the given category."""
        return [
            entry for entry in self.list_tools() if entry["category"] == category
        ]

    def get_tool(self, name: str) -> BaseTool | None:
        """Return a tool by name, or None if not found."""
        return self._tools.get(name)

    def get_tools_for_binding(
        self, *, categories: list[str] | None = None
    ) -> list[BaseTool]:
        """Return tools ready for ``llm.bind_tools()``.

        Args:
            categories: If provided, only return tools in these categories.
                        If None, return all tools.

        Returns:
            List of LangChain tool objects.
        """
        if categories is not None:
            cat_set = set(categories)
            return [
                tool
                for name, tool in self._tools.items()
                if self._categories[name] in cat_set
            ]
        return list(self._tools.values())

    @property
    def categories(self) -> list[str]:
        """Return sorted list of unique categories."""
        unique = sorted(set(self._categories.values()))
        return unique
