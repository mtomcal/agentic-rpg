"""Central tool registry for LangChain tools."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.game_state import GameState
from agentic_rpg.tools.character import (
    AddStatusEffectTool,
    GetCharacterTool,
    RemoveStatusEffectTool,
    UpdateEnergyTool,
    UpdateHealthTool,
    UpdateMoneyTool,
)
from agentic_rpg.tools.inventory import (
    AddItemTool,
    EquipItemTool,
    GetInventoryTool,
    RemoveItemTool,
    UnequipItemTool,
    UseItemTool,
)
from agentic_rpg.tools.narrative import (
    AdaptOutlineTool,
    AddBeatTool,
    AdvanceBeatTool,
    GetStoryOutlineTool,
    ResolveBeatTool,
    UpdateStorySummaryTool,
)
from agentic_rpg.tools.world import (
    AddLocationTool,
    GetConnectionsTool,
    GetCurrentLocationTool,
    InspectEnvironmentTool,
    MoveCharacterTool,
    SetWorldFlagTool,
)


def build_all_tools(
    game_state: GameState, event_bus: EventBus
) -> list[BaseTool]:
    """Instantiate all game tools and return them ready for LLM binding.

    Creates a ToolRegistry, registers every tool from all 4 categories
    (character, inventory, world, narrative), and returns the tool list.
    """
    registry = ToolRegistry()
    kwargs = {"game_state": game_state, "event_bus": event_bus}

    # Character tools
    for cls in (
        GetCharacterTool,
        UpdateHealthTool,
        UpdateEnergyTool,
        UpdateMoneyTool,
        AddStatusEffectTool,
        RemoveStatusEffectTool,
    ):
        registry.register(cls(**kwargs), category="character")

    # Inventory tools
    for cls in (
        GetInventoryTool,
        AddItemTool,
        RemoveItemTool,
        EquipItemTool,
        UnequipItemTool,
        UseItemTool,
    ):
        registry.register(cls(**kwargs), category="inventory")

    # World tools
    for cls in (
        GetCurrentLocationTool,
        GetConnectionsTool,
        MoveCharacterTool,
        InspectEnvironmentTool,
        AddLocationTool,
        SetWorldFlagTool,
    ):
        registry.register(cls(**kwargs), category="world")

    # Narrative tools
    for cls in (
        GetStoryOutlineTool,
        ResolveBeatTool,
        AdvanceBeatTool,
        AdaptOutlineTool,
        AddBeatTool,
        UpdateStorySummaryTool,
    ):
        registry.register(cls(**kwargs), category="narrative")

    return registry.get_tools_for_binding()


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
