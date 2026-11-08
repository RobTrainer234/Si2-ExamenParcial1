import os
import sys
from collections import defaultdict, deque

sys.path.insert(0, os.path.abspath('backend'))
from app.core.models import Base
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql

# Order tables topologically
adj = defaultdict(set)
in_degree = defaultdict(int)
tables = list(Base.metadata.tables.keys())

for tname in tables:
    in_degree[tname] = 0

for tname, table in Base.metadata.tables.items():
    for col in table.columns:
        for fk in col.foreign_keys:
            target = fk.column.table.name
            if target != tname:
                adj[target].add(tname)

for u in tables:
    for v in adj[u]:
        in_degree[v] += 1

q = deque([t for t in tables if in_degree[t] == 0])
sorted_tables = []
while q:
    u = q.popleft()
    sorted_tables.append(u)
    for v in adj[u]:
        in_degree[v] -= 1
        if in_degree[v] == 0:
            q.append(v)

print(f"Topological order determined for {len(sorted_tables)} tables.")

output_lines = [
    "-- ============================================================================",
    "-- SCRIPT DDL COMPLETO DE BASE DE DATOS - PLATAFORMA FASHIONSTORE SAAS",
    "-- Motor de Base de Datos: PostgreSQL 15+ / 16+",
    "-- Modelo Arquitectónico: SaaS Multi-tenant con esquema compartido e ID discriminador",
    "-- Resiliencia: Arquitectura Offline-First con sincronización transaccional Outbox",
    "-- Total de Tablas: 38",
    "-- ============================================================================",
    "",
    "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";",
    "CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";",
    "",
]

# Write drop tables in reverse topological order if needed
output_lines.append("-- ----------------------------------------------------------------------------")
output_lines.append("-- ELIMINACIÓN PREVENTIVA DE TABLAS (ORDEN INVERSO DE DEPENDENCIAS)")
output_lines.append("-- ----------------------------------------------------------------------------")
for tname in reversed(sorted_tables):
    output_lines.append(f"DROP TABLE IF EXISTS \"{tname}\" CASCADE;")
output_lines.append("")

for i, tname in enumerate(sorted_tables, 1):
    table = Base.metadata.tables[tname]
    output_lines.append(f"-- ============================================================================")
    output_lines.append(f"-- {i}. TABLA: {tname}")
    output_lines.append(f"-- ============================================================================")
    
    ddl = str(CreateTable(table).compile(dialect=postgresql.dialect())).strip()
    if not ddl.endswith(";"):
        ddl += ";"
    output_lines.append(ddl)
    output_lines.append("")
    
    # Indexes
    for ix in table.indexes:
        # Ignore primary key index or unique constraint implicit index if duplicate
        ix_ddl = str(CreateIndex(ix).compile(dialect=postgresql.dialect())).strip()
        if not ix_ddl.endswith(";"):
            ix_ddl += ";"
        output_lines.append(ix_ddl)
        
    output_lines.append("")

os.makedirs("database", exist_ok=True)
sql_content = "\n".join(output_lines)
with open("database/fashionstore_complete_schema.sql", "w", encoding="utf-8") as f:
    f.write(sql_content)

print(f"SQL written to database/fashionstore_complete_schema.sql ({len(sql_content)} chars)")
