from pathlib import Path

def test_v181_model_avoids_reserved_metadata_attribute():
    source = Path("backend/app/models/production_hardening_v181.py").read_text(encoding="utf-8")
    assert 'run_metadata: Mapped[dict[str, Any]] = mapped_column("metadata"' in source

def test_v181_router_is_explicitly_versioned():
    source = Path("backend/app/api/v1/production_hardening_v181.py").read_text(encoding="utf-8")
    assert 'prefix="/production-hardening/v18.1"' in source

def test_v181_migration_follows_v18():
    source = Path("backend/alembic/versions/v270a1b2c3d4e_v181_production_hardening.py").read_text(encoding="utf-8")
    assert 'down_revision = "v260a1b2c3d4e"' in source
