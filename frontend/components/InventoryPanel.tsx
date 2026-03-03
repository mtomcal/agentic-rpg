import type { Inventory, Item } from "@/types/game";

interface InventoryPanelProps {
  inventory: Inventory | null;
}

const typeColors: Record<Item["item_type"], string> = {
  weapon: "bg-red-900 text-red-300",
  armor: "bg-blue-900 text-blue-300",
  consumable: "bg-green-900 text-green-300",
  key: "bg-yellow-900 text-yellow-300",
  misc: "bg-gray-700 text-gray-300",
};

export default function InventoryPanel({ inventory }: InventoryPanelProps) {
  if (!inventory) {
    return <div className="p-4 text-gray-500 italic">No inventory data</div>;
  }

  const equippedItems = Object.entries(inventory.equipment);

  return (
    <div className="p-4 space-y-4">
      {equippedItems.length > 0 && (
        <div>
          <h3 className="text-sm text-gray-400 mb-2">Equipment</h3>
          <div className="space-y-1">
            {equippedItems.map(([slot, itemId]) => {
              const item = itemId
                ? inventory.items.find((i) => i.id === itemId)
                : null;
              return (
                <div key={slot} className="flex justify-between text-sm">
                  <span className="text-gray-400 capitalize">{slot}</span>
                  <span>{item ? item.name : "Empty"}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div>
        <h3 className="text-sm text-gray-400 mb-2">Items</h3>
        {inventory.items.length === 0 ? (
          <p className="text-gray-500 italic text-sm">Your inventory is empty</p>
        ) : (
          <div className="space-y-2">
            {inventory.items.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between bg-gray-800 rounded px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${typeColors[item.item_type]}`}>
                    {item.item_type}
                  </span>
                  <span className="text-sm">{item.name}</span>
                </div>
                {item.quantity > 1 && (
                  <span className="text-gray-400 text-sm">x{item.quantity}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
