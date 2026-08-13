# OAuth

Phase 16 establishes an OAuth 2.0 Authorization Code + PKCE foundation.

Supported provider configuration foundations:

- GitHub
- Google / OpenID Connect

The platform includes:

- provider discovery;
- authorization URL generation;
- `state`;
- PKCE `S256`;
- OAuth identity persistence schema;
- callback contract.

The callback deliberately does not exchange authorization codes yet without
real provider credentials and server-side state/verifier persistence.

This avoids presenting an insecure demonstration callback as production-ready
OAuth authentication.
