"""Authentication models and runtime integrations.

Import concrete submodules explicitly. Keeping the package initializer free of
runtime dependencies lets Alembic load authentication models without creating
the application's async database engine.
"""
