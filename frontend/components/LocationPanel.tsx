import type { Location } from "@/types/game";

interface LocationPanelProps {
  location: Location | null;
  locations: Record<string, Location>;
}

export default function LocationPanel({ location, locations }: LocationPanelProps) {
  if (!location) {
    return <div className="p-4 text-gray-500 italic">No location data</div>;
  }

  return (
    <div className="p-4 space-y-4">
      <div>
        <h2 className="text-xl font-bold">{location.name}</h2>
        <p className="text-gray-400 text-sm mt-1">{location.description}</p>
      </div>

      {location.connections.length > 0 && (
        <div>
          <h3 className="text-sm text-gray-400 mb-1">Connected Locations</h3>
          <ul className="space-y-1">
            {location.connections.map((connId) => {
              const conn = locations[connId];
              return (
                <li key={connId} className="text-sm bg-gray-800 rounded px-3 py-1">
                  {conn ? conn.name : connId}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {location.npcs_present.length > 0 && (
        <div>
          <h3 className="text-sm text-gray-400 mb-1">NPCs</h3>
          <ul className="space-y-1">
            {location.npcs_present.map((npc) => (
              <li key={npc} className="text-sm">{npc}</li>
            ))}
          </ul>
        </div>
      )}

      {location.items_present.length > 0 && (
        <div>
          <h3 className="text-sm text-gray-400 mb-1">Items Here</h3>
          <ul className="space-y-1">
            {location.items_present.map((item) => (
              <li key={item} className="text-sm">{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
