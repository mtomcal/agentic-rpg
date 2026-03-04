"""Tests for ToolRegistry — register, discover, and retrieve LangChain tools."""

import pytest
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from agentic_rpg.tools.registry import ToolRegistry, build_all_tools


# ---------------------------------------------------------------------------
# Dummy tools for testing
# ---------------------------------------------------------------------------
class DummyInput(BaseModel):
    """Input for dummy tool."""

    value: str = Field(description="A test value")


@tool(args_schema=DummyInput)
def dummy_tool_a(value: str) -> str:
    """A dummy tool for testing."""
    return f"a:{value}"


@tool(args_schema=DummyInput)
def dummy_tool_b(value: str) -> str:
    """Another dummy tool for testing."""
    return f"b:{value}"


class DummyBaseTool(BaseTool):
    """A BaseTool subclass for testing."""

    name: str = "dummy_base_tool"
    description: str = "A BaseTool subclass for testing."
    args_schema: type = DummyInput

    def _run(self, value: str) -> str:
        return f"base:{value}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestToolRegistryCreation:
    def test_empty_registry_has_no_tools(self):
        registry = ToolRegistry()
        tools = registry.list_tools()
        assert tools == []

    def test_empty_registry_get_tools_for_binding_returns_empty(self):
        registry = ToolRegistry()
        assert registry.get_tools_for_binding() == []


class TestToolRegistration:
    def test_register_decorated_tool(self):
        registry = ToolRegistry()
        registry.register(dummy_tool_a, category="character")
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "dummy_tool_a"
        assert tools[0]["category"] == "character"
        assert "dummy tool" in tools[0]["description"].lower()

    def test_register_base_tool_instance(self):
        registry = ToolRegistry()
        base_tool = DummyBaseTool()
        registry.register(base_tool, category="world")
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "dummy_base_tool"
        assert tools[0]["category"] == "world"

    def test_register_multiple_tools(self):
        registry = ToolRegistry()
        registry.register(dummy_tool_a, category="character")
        registry.register(dummy_tool_b, category="inventory")
        tools = registry.list_tools()
        assert len(tools) == 2
        names = {t["name"] for t in tools}
        assert names == {"dummy_tool_a", "dummy_tool_b"}

    def test_duplicate_name_raises(self):
        registry = ToolRegistry()
        registry.register(dummy_tool_a, category="character")
        with pytest.raises(ValueError, match="already registered"):
            registry.register(dummy_tool_a, category="character")


class TestToolDiscovery:
    def test_list_by_category(self):
        registry = ToolRegistry()
        registry.register(dummy_tool_a, category="character")
        registry.register(dummy_tool_b, category="inventory")
        char_tools = registry.list_by_category("character")
        assert len(char_tools) == 1
        assert char_tools[0]["name"] == "dummy_tool_a"

    def test_list_by_category_no_match(self):
        registry = ToolRegistry()
        registry.register(dummy_tool_a, category="character")
        result = registry.list_by_category("world")
        assert result == []

    def test_get_tool_by_name(self):
        registry = ToolRegistry()
        registry.register(dummy_tool_a, category="character")
        retrieved = registry.get_tool("dummy_tool_a")
        assert retrieved is not None
        assert retrieved.name == "dummy_tool_a"

    def test_get_tool_unknown_name_returns_none(self):
        registry = ToolRegistry()
        assert registry.get_tool("nonexistent") is None

    def test_get_tools_for_binding(self):
        registry = ToolRegistry()
        registry.register(dummy_tool_a, category="character")
        registry.register(dummy_tool_b, category="inventory")
        binding_tools = registry.get_tools_for_binding()
        assert len(binding_tools) == 2
        # These should be actual LangChain tool objects
        names = {t.name for t in binding_tools}
        assert names == {"dummy_tool_a", "dummy_tool_b"}

    def test_get_tools_for_binding_with_categories_filter(self):
        registry = ToolRegistry()
        registry.register(dummy_tool_a, category="character")
        registry.register(dummy_tool_b, category="inventory")
        base_tool = DummyBaseTool()
        registry.register(base_tool, category="world")
        filtered = registry.get_tools_for_binding(categories=["character", "world"])
        assert len(filtered) == 2
        names = {t.name for t in filtered}
        assert names == {"dummy_tool_a", "dummy_base_tool"}

    def test_get_tools_for_binding_empty_categories_returns_empty(self):
        registry = ToolRegistry()
        registry.register(dummy_tool_a, category="character")
        filtered = registry.get_tools_for_binding(categories=[])
        assert filtered == []


class TestToolCategories:
    def test_categories_property(self):
        registry = ToolRegistry()
        registry.register(dummy_tool_a, category="character")
        registry.register(dummy_tool_b, category="inventory")
        cats = registry.categories
        assert set(cats) == {"character", "inventory"}

    def test_categories_empty_registry(self):
        registry = ToolRegistry()
        assert registry.categories == []


class TestBuildAllTools:
    """Tests for the build_all_tools factory function."""

    def test_returns_expected_tool_count(self, tool_game_state, tool_event_bus):
        tools = build_all_tools(tool_game_state, tool_event_bus)
        assert len(tools) == 24

    def test_all_tools_are_base_tools(self, tool_game_state, tool_event_bus):
        tools = build_all_tools(tool_game_state, tool_event_bus)
        for t in tools:
            assert isinstance(t, BaseTool), f"{t.name} is not a BaseTool"

    def test_contains_tools_from_all_categories(self, tool_game_state, tool_event_bus):
        tools = build_all_tools(tool_game_state, tool_event_bus)
        names = {t.name for t in tools}
        # One tool from each category
        assert "get_character" in names
        assert "get_inventory" in names
        assert "get_current_location" in names
        assert "get_story_outline" in names

    def test_tools_have_game_state_reference(self, tool_game_state, tool_event_bus):
        tools = build_all_tools(tool_game_state, tool_event_bus)
        for t in tools:
            assert t.game_state is tool_game_state
