import type { Character } from "@/types/game";

interface CharacterPanelProps {
  character: Character | null;
}

function StatBar({
  label,
  current,
  max,
  color,
  testId,
}: {
  label: string;
  current: number;
  max: number;
  color: string;
  testId: string;
}) {
  const pct = max > 0 ? (current / max) * 100 : 0;
  return (
    <div className="mb-2">
      <div className="flex justify-between text-sm mb-1">
        <span>{label}</span>
        <span>{current} / {max}</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-3" data-testid={testId}>
        <div
          className={`${color} rounded-full h-3 transition-all`}
          style={{ width: `${pct}%` }}
          data-testid={`${testId}-fill`}
        />
      </div>
    </div>
  );
}

function getHealthColor(health: number, maxHealth: number): string {
  const pct = maxHealth > 0 ? health / maxHealth : 0;
  if (pct > 0.5) return "bg-green-500";
  if (pct > 0.25) return "bg-yellow-500";
  return "bg-red-500";
}

export default function CharacterPanel({ character }: CharacterPanelProps) {
  if (!character) {
    return (
      <div className="p-4 text-gray-500 italic">No character data</div>
    );
  }

  const health = character.stats.health ?? 0;
  const maxHealth = character.stats.max_health ?? 100;
  const energy = character.stats.energy ?? 0;
  const maxEnergy = character.stats.max_energy ?? 50;
  const money = character.stats.money ?? 0;

  return (
    <div className="p-4 space-y-4">
      <div>
        <h2 className="text-xl font-bold">{character.name}</h2>
        <p className="text-gray-400">Level {character.level} {character.profession}</p>
      </div>

      <StatBar
        label="Health"
        current={health}
        max={maxHealth}
        color={getHealthColor(health, maxHealth)}
        testId="health-bar"
      />

      <StatBar
        label="Energy"
        current={energy}
        max={maxEnergy}
        color="bg-blue-500"
        testId="energy-bar"
      />

      <div className="text-sm">
        <span className="text-gray-400">Money: </span>
        <span>{money}</span>
      </div>

      <div className="text-sm">
        <span className="text-gray-400">XP: {character.experience}</span>
      </div>

      {character.status_effects.length > 0 && (
        <div>
          <h3 className="text-sm text-gray-400 mb-1">Status Effects</h3>
          <div className="flex flex-wrap gap-2">
            {character.status_effects.map((effect, i) => (
              <span
                key={i}
                className="bg-gray-700 text-gray-200 text-xs px-2 py-1 rounded"
                title={effect.description}
              >
                {effect.name}
                <span className="text-gray-400 ml-1">{effect.duration} turns</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
