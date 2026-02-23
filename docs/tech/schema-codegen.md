# Technology Choice: JSON Schema Codegen

## Decision

Use JSON Schema as the single source of truth for all data structures. Generate Go structs and TypeScript types from these schemas.

## Rationale

- **Single source of truth**: One schema definition, two generated outputs. No manual synchronization.
- **Stack-agnostic specs**: The system specs reference data structures by schema, not by Go struct or TS interface. If the stack changes, only the codegen changes.
- **Runtime validation**: The same JSON Schema files used for codegen are also used at runtime for event validation and API request validation.
- **gRPC-lite**: JSON Schema + codegen gives us many of the benefits of Protobuf/gRPC (shared types, validation, documentation) without the complexity.

## JSON Schema Version

Use JSON Schema draft 2020-12. It's the current standard with good tooling support.

## Codegen Tools

### Go

**Tool**: `atombender/go-jsonschema` or `omissis/go-jsonschema`

Generates Go structs with:
- JSON struct tags
- Validation methods
- Nested type definitions

If the available tools don't meet our needs, we can write a simple custom generator. The schemas are well-structured enough that Go codegen is straightforward.

### TypeScript

**Tool**: `json-schema-to-typescript` (npm package)

Generates TypeScript interfaces with:
- All fields typed
- Optional fields marked with `?`
- Enum types from `enum` constraints
- `$ref` resolved to type references

## Generation Script

A single script regenerates all code from schemas:

```bash
#!/bin/bash
# scripts/generate.sh

set -e

SCHEMA_DIR="schemas"
GO_OUT="backend/generated"
TS_OUT="frontend/src/generated"

# Clean
rm -rf "$GO_OUT" "$TS_OUT"
mkdir -p "$GO_OUT" "$TS_OUT"

# Generate Go
echo "Generating Go types..."
go-jsonschema \
  --package generated \
  --output "$GO_OUT/" \
  "$SCHEMA_DIR"/**/*.json

# Generate TypeScript
echo "Generating TypeScript types..."
npx json-schema-to-typescript \
  --input "$SCHEMA_DIR" \
  --output "$TS_OUT" \
  --cwd "$SCHEMA_DIR"

echo "Done."
```

## Workflow

### During Development

1. Edit a schema file in `schemas/`
2. Run `./scripts/generate.sh`
3. Fix any compile errors in Go or TypeScript (the types changed)
4. Commit the schema change AND the generated code together

### In CI

1. Run `./scripts/generate.sh`
2. Check that the generated code matches what's committed (`git diff --exit-code`)
3. If they differ, the build fails (someone forgot to regenerate)

### Adding a New Schema

1. Create the JSON Schema file in the appropriate `schemas/` subdirectory
2. Follow the conventions in [Schema Registry](../specs/schema-registry.md)
3. Run the generation script
4. Import the generated type in Go/TypeScript
5. Write tests that use the generated type

## Schema → Code Mapping

| JSON Schema | Go | TypeScript |
|---|---|---|
| `object` | `struct` | `interface` |
| `string` | `string` | `string` |
| `integer` | `int` / `int64` | `number` |
| `number` | `float64` | `number` |
| `boolean` | `bool` | `boolean` |
| `array` | `[]T` | `T[]` |
| `enum` | custom type + constants | `type X = "a" \| "b"` |
| `$ref` | embedded struct or field | type reference |
| nullable | `*T` (pointer) | `T \| null` |

## Generated Code Rules

- Generated code lives in `generated/` directories (Go and TS)
- Generated files have a header comment: `// Code generated from JSON Schema. DO NOT EDIT.`
- Generated code is committed to git (so builds don't require the codegen tool)
- Never hand-edit generated files

## Future Extensions

- **OpenAPI generation**: Generate an OpenAPI spec from the schemas for API docs
- **Validation code generation**: Generate runtime validators from schemas (not just types)
- **Mock data generation**: Generate test fixtures from schema `examples`
- **Schema documentation**: Generate human-readable docs from schema `description` fields
