"""
Full schema audit + migration:
Compares SQLAlchemy model columns vs actual DB columns and adds any missing ones.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base
from sqlalchemy import text, inspect

# Import all models so Base.metadata is populated
from backend.models.user import User
from backend.models.photo import Photo
from backend.models.vault import VaultFile
from backend.models.receipt import Receipt
from backend.models.person import Person
from backend.models.face import Face

def get_db_columns(conn, table_name):
    try:
        rows = conn.execute(text(f"SHOW COLUMNS FROM `{table_name}`")).fetchall()
        return {r[0] for r in rows}
    except Exception as e:
        print(f"  WARNING: Table '{table_name}' does not exist yet: {e}")
        return None

def get_col_ddl(col):
    """Generate ALTER TABLE ADD COLUMN DDL from SQLAlchemy column."""
    from sqlalchemy import String, Integer, Boolean, DateTime, Date, Text, JSON, LargeBinary
    t = col.type
    nullable = "NULL" if col.nullable else "NOT NULL"
    
    if isinstance(t, String):
        sql_type = f"VARCHAR({t.length or 255})"
    elif isinstance(t, Integer):
        sql_type = "INT"
    elif isinstance(t, Boolean):
        sql_type = "BOOLEAN"
    elif isinstance(t, DateTime):
        sql_type = "DATETIME"
    elif isinstance(t, Date):
        sql_type = "DATE"
    elif isinstance(t, Text):
        sql_type = "TEXT"
    elif isinstance(t, JSON):
        sql_type = "JSON"
    elif isinstance(t, LargeBinary):
        sql_type = "LONGBLOB"
    else:
        sql_type = "TEXT"  # safe fallback

    default = ""
    if col.default is not None and hasattr(col.default, 'arg') and not callable(col.default.arg):
        val = col.default.arg
        if isinstance(val, str):
            default = f" DEFAULT '{val}'"
        elif isinstance(val, bool):
            default = f" DEFAULT {int(val)}"
        elif val is not None:
            default = f" DEFAULT {val}"
    elif col.server_default is not None:
        default = f" DEFAULT {col.server_default.arg}"

    return f"{sql_type} {nullable}{default}"

def run_audit():
    with engine.connect() as conn:
        for table_name, table in Base.metadata.tables.items():
            db_cols = get_db_columns(conn, table_name)
            if db_cols is None:
                continue
            
            model_cols = {c.name for c in table.columns}
            missing = model_cols - db_cols
            extra = db_cols - model_cols
            
            print(f"\n=== Table: {table_name} ===")
            print(f"  DB columns:    {sorted(db_cols)}")
            print(f"  Model columns: {sorted(model_cols)}")
            
            if missing:
                print(f"  MISSING in DB: {missing}")
                for col_name in missing:
                    col = table.columns[col_name]
                    ddl = get_col_ddl(col)
                    sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{col_name}` {ddl}"
                    print(f"  -> Running: {sql}")
                    try:
                        conn.execute(text(sql))
                        conn.commit()
                        print(f"     [OK] Added '{col_name}'")
                    except Exception as e:
                        print(f"     [FAIL] Failed: {e}")
            else:
                print(f"  [OK] All model columns present in DB")
            
            if extra:
                print(f"  Extra in DB (not in model, OK to ignore): {extra}")

    print("\n\nMigration complete!")

if __name__ == "__main__":
    run_audit()
