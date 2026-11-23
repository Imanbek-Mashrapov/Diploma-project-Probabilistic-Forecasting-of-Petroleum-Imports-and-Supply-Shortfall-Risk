"""Apply sql/schema.sql and load everything into a throwaway embedded PostgreSQL,
then confirm the constraints hold. Run with: python -m tests.db_smoke (needs pgserver)."""
import tempfile

import pgserver
from sqlalchemy import create_engine, text

from src.database.load import apply_schema, load_all
from src.utils.logging_config import setup_logging

setup_logging("db_smoke")
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    server = pgserver.get_server(tmp)
    engine = create_engine(server.get_uri().replace("postgresql://", "postgresql+psycopg2://"))
    apply_schema(engine)
    print(load_all(engine))
    with engine.connect() as c:
        print("version", c.execute(text("select version()")).scalar()[:30])
        print("view rows", c.execute(text("select count(*) from analytics.bilateral_petroleum_imports")).scalar())
        print("jsonb sample", c.execute(text("select record->>'cmdCode', record->>'partnerDesc' from raw.un_comtrade_imports limit 1")).fetchone())
        print("KGZ 2024 gasoline kt", c.execute(text(
            "select round((sum(mass_t)/1000)::numeric, 1) from analytics.monthly_petroleum_imports "
            "where iso3='KGZ' and product_group='gasoline' and flow='M' and period between 202401 and 202412")).scalar())
        print("external series", c.execute(text("select count(distinct series) from analytics.monthly_external_indicators")).scalar())
    engine.dispose()
    server.cleanup()
