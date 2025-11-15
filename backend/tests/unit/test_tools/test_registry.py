"""Tests for Tool Registry."""
import pytest

from agentic_rpg.agents.tools.registry import ToolRegistry


class MockTool:
    """Mock tool for testing."""

    def __init__(self, name: str, description: str = "Test tool"):
        self.name = name
        self.description = description
        self.schema = {
            "type": "object",
            "properties": {},
        }

    def execute(self, **kwargs) -> dict:
        """Execute the tool."""
        return {"result": "success", "input": kwargs}

    def validate(self, **kwargs) -> bool:
        """Validate parameters."""
        return True


class TestToolRegistry:
    """Test ToolRegistry functionality."""

    @pytest.fixture(autouse=True)
    def clear_registry(self):
        """Clear registry before each test."""
        ToolRegistry.clear()
        yield
        ToolRegistry.clear()

    def test_register_tool(self):
        """Test registering a tool."""
        tool = MockTool("test_tool")
        ToolRegistry.register(tool)

        registered_tool = ToolRegistry.get_tool("test_tool")
        assert registered_tool is tool
        assert registered_tool.name == "test_tool"

    def test_register_tool_with_category(self):
        """Test registering a tool with a category."""
        tool = MockTool("test_tool")
        ToolRegistry.register(tool, category="combat")

        tools = ToolRegistry.get_tools_by_category("combat")
        assert len(tools) == 1
        assert tools[0].name == "test_tool"

    def test_register_duplicate_tool_raises_error(self):
        """Test that registering duplicate tool name raises error."""
        tool1 = MockTool("duplicate")
        tool2 = MockTool("duplicate")

        ToolRegistry.register(tool1)

        with pytest.raises(ValueError, match="already registered"):
            ToolRegistry.register(tool2)

    def test_get_nonexistent_tool_raises_error(self):
        """Test that getting nonexistent tool raises error."""
        with pytest.raises(KeyError, match="not registered"):
            ToolRegistry.get_tool("nonexistent")

    def test_get_tools_by_category(self):
        """Test getting tools by category."""
        combat_tool1 = MockTool("attack")
        combat_tool2 = MockTool("defend")
        world_tool = MockTool("explore")

        ToolRegistry.register(combat_tool1, category="combat")
        ToolRegistry.register(combat_tool2, category="combat")
        ToolRegistry.register(world_tool, category="world")

        combat_tools = ToolRegistry.get_tools_by_category("combat")
        assert len(combat_tools) == 2
        assert all(t.name in ["attack", "defend"] for t in combat_tools)

        world_tools = ToolRegistry.get_tools_by_category("world")
        assert len(world_tools) == 1
        assert world_tools[0].name == "explore"

    def test_get_tools_by_nonexistent_category(self):
        """Test getting tools by nonexistent category returns empty list."""
        tools = ToolRegistry.get_tools_by_category("nonexistent")
        assert tools == []

    def test_list_all_tools(self):
        """Test listing all registered tool names."""
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")
        tool3 = MockTool("tool3")

        ToolRegistry.register(tool1)
        ToolRegistry.register(tool2)
        ToolRegistry.register(tool3)

        all_tools = ToolRegistry.list_all()
        assert len(all_tools) == 3
        assert set(all_tools) == {"tool1", "tool2", "tool3"}

    def test_list_all_empty_registry(self):
        """Test listing all tools from empty registry."""
        all_tools = ToolRegistry.list_all()
        assert all_tools == []

    def test_clear_registry(self):
        """Test clearing the registry."""
        tool1 = MockTool("tool1")
        tool2 = MockTool("tool2")

        ToolRegistry.register(tool1, category="cat1")
        ToolRegistry.register(tool2, category="cat2")

        assert len(ToolRegistry.list_all()) == 2

        ToolRegistry.clear()

        assert len(ToolRegistry.list_all()) == 0
        assert ToolRegistry.get_tools_by_category("cat1") == []
        assert ToolRegistry.get_tools_by_category("cat2") == []

    def test_multiple_tools_same_category(self):
        """Test registering multiple tools in the same category."""
        tools = [MockTool(f"tool{i}") for i in range(5)]

        for tool in tools:
            ToolRegistry.register(tool, category="general")

        general_tools = ToolRegistry.get_tools_by_category("general")
        assert len(general_tools) == 5
        assert all(t.name in [f"tool{i}" for i in range(5)] for t in general_tools)

    def test_tool_with_default_category(self):
        """Test that tools use 'general' category by default."""
        tool = MockTool("default_tool")
        ToolRegistry.register(tool)  # No category specified

        general_tools = ToolRegistry.get_tools_by_category("general")
        assert len(general_tools) == 1
        assert general_tools[0].name == "default_tool"

    def test_registry_is_class_level(self):
        """Test that registry is shared across all instances."""
        tool = MockTool("shared_tool")
        ToolRegistry.register(tool)

        # Should be accessible without creating instance
        retrieved = ToolRegistry.get_tool("shared_tool")
        assert retrieved is tool


class TestGameToolProtocol:
    """Test that tools follow the GameTool protocol."""

    def test_mock_tool_has_required_attributes(self):
        """Test that mock tool has all required protocol attributes."""
        tool = MockTool("test")

        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert hasattr(tool, "schema")
        assert callable(tool.execute)
        assert callable(tool.validate)

    def test_tool_execute_returns_dict(self):
        """Test that execute method returns dict."""
        tool = MockTool("test")
        result = tool.execute(param1="value1")

        assert isinstance(result, dict)

    def test_tool_validate_returns_bool(self):
        """Test that validate method returns bool."""
        tool = MockTool("test")
        result = tool.validate(param1="value1")

        assert isinstance(result, bool)

    def test_tool_schema_is_dict(self):
        """Test that schema is a dict."""
        tool = MockTool("test")
        assert isinstance(tool.schema, dict)
