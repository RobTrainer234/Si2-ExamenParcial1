"""Muestra el modelo SQLAlchemy y genera su DDL PostgreSQL."""
from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy.dialects import postgresql

from app.core.models import Base
from app.core import models  # noqa: F401  Importa todas las clases del modelo.


def construir_esquema() -> str:
    """Devuelve un informe legible de clases, tablas y relaciones."""
    dialecto = postgresql.dialect()
    lineas = [
        "-- Esquema generado desde las clases SQLAlchemy de FashionStore",
        "-- Incluye los tres ciclos y la bitacora de auditoria.",
        "",
        "\n-- CLASES, TABLAS Y COLUMNAS\n",
    ]

    mapeadores = sorted(Base.registry.mappers, key=lambda mapper: mapper.local_table.name)
    for mapeador in mapeadores:
        tabla = mapeador.local_table
        lineas.append(f"-- Clase: {mapeador.class_.__name__} | Tabla: {tabla.name}")
        for columna in tabla.columns:
            nulabilidad = "NULL" if columna.nullable else "NOT NULL"
            lineas.append(f"--   {columna.name}: {columna.type} {nulabilidad}")
        for restriccion in tabla.constraints:
            if restriccion.name:
                lineas.append(f"--   Restriccion: {restriccion.name}")
        for indice in tabla.indexes:
            lineas.append(f"--   Indice: {indice.name}")
        lineas.append("")

    lineas.append("\n-- RELACIONES\n")
    for mapeador in mapeadores:
        for relacion in sorted(mapeador.relationships, key=lambda item: item.key):
            lineas.append(
                f"-- {mapeador.class_.__name__}.{relacion.key} -> "
                f"{relacion.mapper.class_.__name__} ({relacion.direction.name})"
            )

    lineas.extend(["", "\n-- DDL POSTGRESQL\n"])
    for tabla in sorted(Base.metadata.sorted_tables, key=lambda item: item.name):
        lineas.append(str(CreateTable(tabla).compile(dialect=dialecto)).rstrip() + ";")
        for indice in sorted(tabla.indexes, key=lambda item: item.name):
            lineas.append(str(CreateIndex(indice).compile(dialect=dialecto)).rstrip() + ";")
        lineas.append("")

    return "\n".join(lineas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspecciona el modelo completo de la base de datos.")
    parser.add_argument(
        "--salida",
        type=Path,
        help="Archivo opcional donde guardar el informe y el DDL generado.",
    )
    argumentos = parser.parse_args()
    esquema = construir_esquema()
    if argumentos.salida:
        argumentos.salida.write_text(esquema, encoding="utf-8")
        print(f"Esquema generado en {argumentos.salida}")
    else:
        print(esquema)


if __name__ == "__main__":
    main()
