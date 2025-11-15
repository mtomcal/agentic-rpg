"""Tests for inventory models."""
import pytest
from pydantic import ValidationError
from agentic_rpg.models.inventory import Inventory, InventoryItem


class TestInventoryItem:
    """Test InventoryItem model."""

    def test_valid_inventory_item(self):
        """Test creating valid inventory item."""
        item = InventoryItem(
            id="item_sword_001",
            name="Plasma Sword",
            description="A glowing blade of pure energy",
            quantity=1,
            weight=2.5,
            properties={"damage": 15, "type": "weapon", "rarity": "rare"}
        )
        assert item.id == "item_sword_001"
        assert item.name == "Plasma Sword"
        assert item.description == "A glowing blade of pure energy"
        assert item.quantity == 1
        assert item.weight == 2.5
        assert item.properties["damage"] == 15

    def test_inventory_item_default_description(self):
        """Test default description is empty string."""
        item = InventoryItem(id="item_001", name="Test Item")
        assert item.description == ""

    def test_inventory_item_default_quantity(self):
        """Test default quantity is 1."""
        item = InventoryItem(id="item_001", name="Test Item")
        assert item.quantity == 1

    def test_inventory_item_default_weight(self):
        """Test default weight is 1.0."""
        item = InventoryItem(id="item_001", name="Test Item")
        assert item.weight == 1.0

    def test_inventory_item_default_properties(self):
        """Test default properties is empty dict."""
        item = InventoryItem(id="item_001", name="Test Item")
        assert item.properties == {}

    def test_inventory_item_name_min_length(self):
        """Test that name must be at least 1 character."""
        with pytest.raises(ValidationError) as exc_info:
            InventoryItem(id="item_001", name="")
        assert "name" in str(exc_info.value)

    def test_inventory_item_name_max_length(self):
        """Test that name cannot exceed 100 characters."""
        with pytest.raises(ValidationError) as exc_info:
            InventoryItem(id="item_001", name="a" * 101)
        assert "name" in str(exc_info.value)

    def test_inventory_item_quantity_must_be_positive(self):
        """Test that quantity must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            InventoryItem(id="item_001", name="Test Item", quantity=0)
        assert "quantity" in str(exc_info.value)

    def test_inventory_item_weight_cannot_be_negative(self):
        """Test that weight cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            InventoryItem(id="item_001", name="Test Item", weight=-1.0)
        assert "weight" in str(exc_info.value)

    def test_inventory_item_json_schema_extra(self):
        """Test that JSON schema examples are defined."""
        schema = InventoryItem.model_json_schema()
        assert "examples" in schema
        assert len(schema["examples"]) > 0


class TestInventory:
    """Test Inventory model."""

    def test_empty_inventory(self):
        """Test creating empty inventory."""
        inventory = Inventory()
        assert inventory.items == []
        assert inventory.capacity == 20
        assert inventory.max_weight == 100.0

    def test_inventory_with_items(self):
        """Test creating inventory with items."""
        item = InventoryItem(id="item_001", name="Test Item")
        inventory = Inventory(items=[item])
        assert len(inventory.items) == 1
        assert inventory.items[0].id == "item_001"

    def test_inventory_custom_capacity(self):
        """Test custom capacity."""
        inventory = Inventory(capacity=50)
        assert inventory.capacity == 50

    def test_inventory_custom_max_weight(self):
        """Test custom max weight."""
        inventory = Inventory(max_weight=200.0)
        assert inventory.max_weight == 200.0

    def test_current_weight_empty(self):
        """Test current_weight with empty inventory."""
        inventory = Inventory()
        assert inventory.current_weight == 0.0

    def test_current_weight_single_item(self):
        """Test current_weight with single item."""
        item = InventoryItem(id="item_001", name="Test Item", quantity=1, weight=5.0)
        inventory = Inventory(items=[item])
        assert inventory.current_weight == 5.0

    def test_current_weight_multiple_items(self):
        """Test current_weight with multiple items."""
        item1 = InventoryItem(id="item_001", name="Item 1", quantity=2, weight=5.0)
        item2 = InventoryItem(id="item_002", name="Item 2", quantity=3, weight=2.0)
        inventory = Inventory(items=[item1, item2])
        assert inventory.current_weight == 16.0  # (2 * 5.0) + (3 * 2.0)

    def test_is_full_empty_inventory(self):
        """Test is_full with empty inventory."""
        inventory = Inventory(capacity=20)
        assert inventory.is_full is False

    def test_is_full_at_capacity(self):
        """Test is_full when at capacity."""
        items = [InventoryItem(id=f"item_{i}", name=f"Item {i}") for i in range(20)]
        inventory = Inventory(items=items, capacity=20)
        assert inventory.is_full is True

    def test_is_full_below_capacity(self):
        """Test is_full when below capacity."""
        items = [InventoryItem(id=f"item_{i}", name=f"Item {i}") for i in range(19)]
        inventory = Inventory(items=items, capacity=20)
        assert inventory.is_full is False

    def test_can_add_to_empty_inventory(self):
        """Test can_add with empty inventory."""
        inventory = Inventory()
        item = InventoryItem(id="item_001", name="Test Item")
        can_add, message = inventory.can_add(item)
        assert can_add is True
        assert message == ""

    def test_can_add_when_full(self):
        """Test can_add when inventory is full."""
        items = [InventoryItem(id=f"item_{i}", name=f"Item {i}") for i in range(20)]
        inventory = Inventory(items=items, capacity=20)
        new_item = InventoryItem(id="item_new", name="New Item")
        can_add, message = inventory.can_add(new_item)
        assert can_add is False
        assert "full" in message.lower()

    def test_can_add_when_too_heavy(self):
        """Test can_add when item would exceed max weight."""
        item1 = InventoryItem(id="item_001", name="Heavy Item", weight=90.0)
        inventory = Inventory(items=[item1], max_weight=100.0)
        item2 = InventoryItem(id="item_002", name="Another Item", weight=15.0)
        can_add, message = inventory.can_add(item2)
        assert can_add is False
        assert "heavy" in message.lower() or "weight" in message.lower()

    def test_can_add_exact_weight_limit(self):
        """Test can_add when item exactly reaches max weight."""
        item1 = InventoryItem(id="item_001", name="Item 1", weight=90.0)
        inventory = Inventory(items=[item1], max_weight=100.0)
        item2 = InventoryItem(id="item_002", name="Item 2", weight=10.0)
        can_add, message = inventory.can_add(item2)
        assert can_add is True
        assert message == ""

    def test_inventory_capacity_must_be_positive(self):
        """Test that capacity must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            Inventory(capacity=0)
        assert "capacity" in str(exc_info.value)

    def test_inventory_max_weight_cannot_be_negative(self):
        """Test that max_weight cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            Inventory(max_weight=-1.0)
        assert "max_weight" in str(exc_info.value)
