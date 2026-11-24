# Type System Discipline

Make the compiler reject impossible states, mismatched primitives, and unhandled variants.

- **Brand semantic primitives.** If two arguments share a primitive type but mean different things, give each its own type. Validate once at creation.
- **External data is untyped until parsed.** JSON, RPC payloads, CLI args, config, environment variables, and database rows go through a parse function at the boundary that returns the typed model.
- **Exhaust variants.** Match every variant of a union or enum exhaustively so adding a new case causes a compile error instead of a silent fallthrough.
- **Derive types from authoritative schemas.** When a schema file owns a shape, derive the type from it instead of hand-rolling a parallel one.

Follow the repository's language-specific type conventions and strict compiler settings.
