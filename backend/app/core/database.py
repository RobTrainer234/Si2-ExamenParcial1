from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import ORMExecuteState, Session, sessionmaker, with_loader_criteria

from app.core.config import settings
from app.core.models import (
    AIRecommendation,
    Bitacora,
    Branch,
    Cart,
    Category,
    Collection,
    Inventory,
    InventoryMovement,
    Payment,
    Product,
    ProductVariant,
    Promotion,
    Reservation,
    Sale,
    Season,
    Supplier,
    SupplierSupplyOffer,
    SyncOperation,
    User,
    VirtualFittingSession,
)

TENANT_SCOPED_MODELS = (
    Branch,
    User,
    Category,
    Supplier,
    Season,
    Promotion,
    Collection,
    Product,
    ProductVariant,
    SupplierSupplyOffer,
    Inventory,
    Reservation,
    Cart,
    Sale,
    Payment,
    InventoryMovement,
    VirtualFittingSession,
    AIRecommendation,
    Bitacora,
    SyncOperation,
)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@event.listens_for(Session, "do_orm_execute")
def _apply_tenant_loader_criteria(orm_execute_state: ORMExecuteState) -> None:
    if (
        (orm_execute_state.is_select or orm_execute_state.is_update or orm_execute_state.is_delete)
        and not orm_execute_state.is_column_load
        and not orm_execute_state.execution_options.get("ignore_tenant_scope", False)
    ):
        session = orm_execute_state.session
        if session.info.get("tenant_context_active"):
            tid = session.info.get("tenant_id")
            if tid is None:
                criteria_fn = lambda cls: cls.tenant_id.is_(None)
            else:
                criteria_fn = lambda cls: cls.tenant_id == tid
            orm_execute_state.statement = orm_execute_state.statement.options(
                *(
                    with_loader_criteria(
                        model_cls,
                        criteria_fn,
                        include_aliases=True,
                    )
                    for model_cls in TENANT_SCOPED_MODELS
                )
            )


@event.listens_for(Session, "before_flush")
def _enforce_tenant_on_flush(session: Session, flush_context: object, instances: object) -> None:
    del flush_context, instances
    if not session.info.get("tenant_context_active"):
        return
    tid = session.info.get("tenant_id")
    for obj in session.new:
        if isinstance(obj, TENANT_SCOPED_MODELS):
            if obj.tenant_id is None:
                obj.tenant_id = tid
            elif obj.tenant_id != tid:
                raise PermissionError("Operación cross-tenant bloqueada en creación de entidad.")
    for obj in list(session.dirty) + list(session.deleted):
        if isinstance(obj, TENANT_SCOPED_MODELS) and obj.tenant_id != tid:
            raise PermissionError("Operación cross-tenant bloqueada en modificación o eliminación de entidad.")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
