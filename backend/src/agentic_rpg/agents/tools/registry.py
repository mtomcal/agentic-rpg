"""Tool registry for dynamic tool registration."""
from .base import GameTool


class ToolRegistry:
    """Central registry for agent tools - prevents merge conflicts."""

    _tools: dict[str, GameTool] = {}
    _categories: dict[str, list[str]] = {}

    @classmethod
    def register(cls, tool: GameTool, category: str = "general") -> None:
        """Register a tool."""
        if tool.name in cls._tools:
            raise ValueError(f"Tool {tool.name} already registered")

        cls._tools[tool.name] = tool
        cls._categories.setdefault(category, []).append(tool.name)

    @classmethod
    def get_tool(cls, name: str) -> GameTool:
        """Get tool by name."""
        if name not in cls._tools:
            raise KeyError(f"Tool {name} not registered")
        return cls._tools[name]

    @classmethod
    def get_tools_by_category(cls, category: str) -> list[GameTool]:
        """Get all tools in a category."""
        tool_names = cls._categories.get(category, [])
        return [cls._tools[name] for name in tool_names]

    @classmethod
    def list_all(cls) -> list[str]:
        """List all registered tool names."""
        return list(cls._tools.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (for testing)."""
        cls._tools.clear()
        cls._categories.clear()
