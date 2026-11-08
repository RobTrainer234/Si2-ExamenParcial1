import os
import sys
import json

sys.path.insert(0, os.path.abspath('backend'))
from app.core.models import Base
from sqlalchemy.dialects import postgresql

data = {}
for name, table in Base.metadata.tables.items():
    cols = []
    for c in table.columns:
        pks = bool(c.primary_key)
        fks = []
        for fk in c.foreign_keys:
            ondelete = fk.ondelete if fk.ondelete else 'NO ACTION'
            fks.append(f"{fk.column.table.name}({fk.column.name}) ON DELETE {ondelete}")
        
        if pks and fks:
            key_tag = "PK / FK"
        elif pks:
            key_tag = "PK"
        elif fks:
            key_tag = "FK"
        else:
            key_tag = "-"
            
        col_type = str(c.type.compile(dialect=postgresql.dialect()))
        
        default_val = None
        if c.server_default is not None:
            default_val = str(c.server_default.arg)
        elif c.default is not None:
            default_val = str(c.default.arg if hasattr(c.default, 'arg') else c.default)
            
        cols.append({
            "name": c.name,
            "type": col_type,
            "key": key_tag,
            "fks": fks,
            "nullable": bool(c.nullable),
            "default": default_val
        })
        
    ucs = []
    for uc in table.constraints:
        if uc.__class__.__name__ == 'UniqueConstraint' and hasattr(uc, 'columns') and uc.columns:
            ucs.append({
                "name": uc.name,
                "columns": [col.name for col in uc.columns]
            })
            
    cks = []
    for ck in table.constraints:
        if ck.__class__.__name__ == 'CheckConstraint':
            cks.append({
                "name": ck.name,
                "sql": str(ck.sqltext)
            })
            
    idxs = []
    for ix in table.indexes:
        idxs.append({
            "name": ix.name,
            "columns": [col.name for col in ix.columns],
            "unique": bool(ix.unique)
        })
        
    data[name] = {
        "columns": cols,
        "unique_constraints": ucs,
        "check_constraints": cks,
        "indexes": idxs
    }

with open("scripts/metadata_tables.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Exported {len(data)} tables to scripts/metadata_tables.json")
