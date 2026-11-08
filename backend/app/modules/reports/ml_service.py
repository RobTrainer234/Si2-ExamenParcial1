from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
import math
import random
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, silhouette_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.models import Branch, Sale, SaleItem
from app.modules.reports.schemas import (
    CustomerAnomalyItem,
    CustomerSegmentItem,
    CustomerSegmentationResponse,
    DemandForecastPoint,
    DemandForecastResponse,
    MLModelMetrics,
    MLTrainingResponse,
)

logger = logging.getLogger(__name__)


class SyntheticDataService:
    """Genera datos sintéticos calibrados al tenant para entrenamiento y evaluación de modelos."""

    @staticmethod
    def generate_sales_series(
        db: Session,
        tenant_id: int,
        days: int = 90,
    ) -> list[dict[str, Any]]:
        branches = db.scalars(
            select(Branch).where(Branch.tenant_id == tenant_id, Branch.is_active == True)  # noqa: E712
        ).all()
        branch_ids = [b.id for b in branches] or [1]

        rng = random.Random(tenant_id * 42)
        base_date = (datetime.now(timezone.utc) - timedelta(days=days)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        records: list[dict[str, Any]] = []

        base_daily_sales = 15.0 + (tenant_id % 5) * 5.0

        for day_offset in range(days):
            current_date = base_date + timedelta(days=day_offset)
            weekday = current_date.weekday()
            # Factor de fin de semana (viernes, sábado, domingo tienen más demanda)
            weekend_factor = 1.45 if weekday in (4, 5, 6) else 0.95
            # Factor de estacionalidad sinusoidal
            seasonality = 1.0 + 0.25 * math.sin(2 * math.pi * day_offset / 30.0)
            # Ruido estocástico
            noise = rng.uniform(0.85, 1.15)

            for branch_id in branch_ids:
                branch_multiplier = 1.0 + (branch_id % 3) * 0.2
                daily_volume = int(round(base_daily_sales * weekend_factor * seasonality * noise * branch_multiplier))
                daily_revenue = Decimal(str(round(daily_volume * rng.uniform(85.0, 160.0), 2)))

                records.append({
                    "date": current_date,
                    "branch_id": branch_id,
                    "units_sold": max(1, daily_volume),
                    "revenue": daily_revenue,
                })

        return records

    @staticmethod
    def generate_customer_rfm_profiles(
        db: Session,
        tenant_id: int,
        num_customers: int = 60,
    ) -> list[dict[str, Any]]:
        rng = random.Random(tenant_id * 101)
        profiles: list[dict[str, Any]] = []

        # Simula 4 patrones arquetípicos de moda
        for i in range(num_customers):
            archetype = i % 4
            if archetype == 0:  # VIP / Champions
                recency = rng.randint(1, 14)
                frequency = rng.randint(8, 25)
                monetary = Decimal(str(round(rng.uniform(1500.0, 5000.0), 2)))
            elif archetype == 1:  # Frecuentes
                recency = rng.randint(10, 35)
                frequency = rng.randint(4, 10)
                monetary = Decimal(str(round(rng.uniform(600.0, 1800.0), 2)))
            elif archetype == 2:  # En riesgo de abandono
                recency = rng.randint(45, 120)
                frequency = rng.randint(3, 8)
                monetary = Decimal(str(round(rng.uniform(500.0, 1600.0), 2)))
            else:  # Nuevos / Ocasionales
                recency = rng.randint(1, 30)
                frequency = rng.randint(1, 2)
                monetary = Decimal(str(round(rng.uniform(80.0, 400.0), 2)))

            profiles.append({
                "customer_id": i + 1,
                "recency_days": recency,
                "frequency": frequency,
                "monetary": monetary,
            })

        return profiles


class DemandForecastService:
    """Modelo supervisado de predicción de demanda de ventas con métricas MAE, RMSE y R²."""

    @staticmethod
    def forecast_demand(
        db: Session,
        tenant_id: int,
        branch_id: int | None = None,
        weeks_ahead: int = 6,
    ) -> DemandForecastResponse:
        # 1. Obtener datos reales de ventas
        query = (
            select(
                func.date(Sale.created_at).label("sale_date"),
                func.count(Sale.id).label("transactions"),
                func.coalesce(func.sum(SaleItem.quantity), 0).label("units"),
                func.coalesce(func.sum(Sale.total), 0).label("revenue"),
            )
            .join(SaleItem, Sale.id == SaleItem.sale_id, isouter=True)
            .where(
                Sale.tenant_id == tenant_id,
                Sale.status.in_(["CONFIRMED", "COMPLETED"]),
            )
            .group_by(func.date(Sale.created_at))
            .order_by(func.date(Sale.created_at))
        )
        if branch_id is not None:
            query = query.where(Sale.branch_id == branch_id)

        real_data = db.execute(query).all()
        real_samples_count = len(real_data)
        synthetic_samples_count = 0

        # Si el tenant tiene menos de 20 registros históricos, aumentamos con datos sintéticos
        if len(real_data) < 20:
            synthetic = SyntheticDataService.generate_sales_series(db, tenant_id, days=70)
            daily_agg: dict[str, dict[str, Any]] = {}
            synthetic_days: set[str] = set()
            for item in synthetic:
                if branch_id is not None and item["branch_id"] != branch_id:
                    continue
                d_str = item["date"].strftime("%Y-%m-%d")
                synthetic_days.add(d_str)
                if d_str not in daily_agg:
                    daily_agg[d_str] = {"units": 0, "revenue": Decimal(0)}
                daily_agg[d_str]["units"] += item["units_sold"]
                daily_agg[d_str]["revenue"] += item["revenue"]

            # Merge with real data; real observations replace synthetic observations for the same day.
            for r in real_data:
                d_str = str(r[0])
                daily_agg[d_str] = {"units": int(r[2]), "revenue": Decimal(str(r[3]))}
                synthetic_days.discard(d_str)

            synthetic_samples_count = len(synthetic_days)
            sorted_days = sorted(daily_agg.items(), key=lambda x: x[0])
            dates = [datetime.strptime(k, "%Y-%m-%d").replace(tzinfo=timezone.utc) for k, _ in sorted_days]
            units_series = [v["units"] for _, v in sorted_days]
            revenue_series = [float(v["revenue"]) for _, v in sorted_days]
        else:
            dates = [datetime.strptime(str(r[0]), "%Y-%m-%d").replace(tzinfo=timezone.utc) for r in real_data]
            units_series = [int(r[2]) for r in real_data]
            revenue_series = [float(r[3]) for r in real_data]

        # 2. Ingeniería de características temporales
        X: list[list[float]] = []
        y: list[float] = []

        for i in range(len(dates)):
            d = dates[i]
            day_of_week = float(d.weekday())
            day_of_month = float(d.day)
            is_weekend = 1.0 if d.weekday() in (4, 5, 6) else 0.0
            t_index = float(i)

            # Lags y medias móviles
            lag_1 = float(units_series[i - 1]) if i >= 1 else float(units_series[i])
            lag_7 = float(units_series[i - 7]) if i >= 7 else lag_1
            rolling_7 = float(np.mean(units_series[max(0, i - 6) : i + 1]))

            X.append([t_index, day_of_week, day_of_month, is_weekend, lag_1, lag_7, rolling_7])
            y.append(float(units_series[i]))

        X_mat = np.array(X)
        y_vec = np.array(y)

        # 3. Entrenamiento y validación supervisada
        mae: float | None = None
        rmse: float | None = None
        r2: float | None = None
        if len(X_mat) >= 10:
            split_at = max(1, min(len(X_mat) - 1, int(len(X_mat) * 0.75)))
            X_train, X_test = X_mat[:split_at], X_mat[split_at:]
            y_train, y_test = y_vec[:split_at], y_vec[split_at:]
            model = Ridge(alpha=1.0)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            mae = float(mean_absolute_error(y_test, y_pred))
            rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            raw_r2 = r2_score(y_test, y_pred) if len(y_test) > 1 else None
            calculated_r2 = float(raw_r2) if raw_r2 is not None else None
            r2 = calculated_r2 if calculated_r2 is not None and math.isfinite(calculated_r2) else None
        else:
            model = Ridge(alpha=1.0)
            model.fit(X_mat, y_vec)

        # 4. Proyección a futuro (semanas próximas)
        forecast_points: list[DemandForecastPoint] = []
        last_date = dates[-1] if dates else datetime.now(timezone.utc)
        avg_price_per_unit = (sum(revenue_series) / max(1, sum(units_series))) if sum(units_series) > 0 else 115.0

        current_t = len(dates)
        rolling_buffer = list(units_series[-7:]) if len(units_series) >= 7 else [15.0] * 7

        for w in range(1, weeks_ahead + 1):
            future_week_date = last_date + timedelta(weeks=w)
            # Predicción acumulada de los 7 días de la semana
            weekly_units = 0.0
            for d_idx in range(7):
                sim_date = future_week_date + timedelta(days=d_idx)
                f_dow = float(sim_date.weekday())
                f_dom = float(sim_date.day)
                f_weekend = 1.0 if sim_date.weekday() in (4, 5, 6) else 0.0
                feat = np.array([[current_t, f_dow, f_dom, f_weekend, rolling_buffer[-1], rolling_buffer[0], float(np.mean(rolling_buffer))]])
                pred_day = max(2.0, float(model.predict(feat)[0]))
                weekly_units += pred_day
                rolling_buffer.pop(0)
                rolling_buffer.append(pred_day)
                current_t += 1

            total_u = int(round(weekly_units))
            pred_rev = Decimal(str(round(total_u * avg_price_per_unit, 2)))
            validation_mae = mae if mae is not None else 0.0
            error_margin = Decimal(str(round(float(pred_rev) * (validation_mae / max(1.0, float(np.mean(y_vec)))), 2)))
            conf_lower = max(Decimal(0), pred_rev - error_margin)
            conf_upper = pred_rev + error_margin

            forecast_points.append(
                DemandForecastPoint(
                    period=f"Semana +{w} ({future_week_date.strftime('%d/%m')})",
                    predicted_units=total_u,
                    predicted_revenue=pred_rev,
                    confidence_lower=conf_lower,
                    confidence_upper=conf_upper,
                )
            )

        branch_name = None
        if branch_id is not None:
            b_obj = db.scalar(
                select(Branch).where(
                    Branch.id == branch_id,
                    Branch.tenant_id == tenant_id,
                    Branch.is_active == True,  # noqa: E712
                )
            )
            branch_name = b_obj.name if b_obj else None

        if mae is not None and rmse is not None and r2 is not None:
            validation_summary = f"MAE={mae:.2f} prendas/día, RMSE={rmse:.2f}, R²={r2:.2f}"
        elif mae is not None and rmse is not None:
            validation_summary = f"MAE={mae:.2f} prendas/día, RMSE={rmse:.2f}, R² no disponible"
        else:
            validation_summary = "las métricas de validación no están disponibles por insuficiencia de datos"
        narrative = (
            f"Proyección supervisada de demanda para {weeks_ahead} semanas: Se anticipa una demanda acumulada "
            f"de {sum(p.predicted_units for p in forecast_points)} unidades con ingresos proyectados de Bs {sum(p.predicted_revenue for p in forecast_points):,.2f}. "
            f"Precisión del modelo evaluada: {validation_summary}. "
            f"Recomendación logística: Surtir stock en las 2 primeras semanas de proyección para evitar quiebres durante los picos de fin de semana."
        )

        return DemandForecastResponse(
            target="ventas_semanales",
            branch_id=branch_id,
            branch_name=branch_name,
            forecast=forecast_points,
            metrics=MLModelMetrics(
                model_name="Ridge Regression con Ingeniería Temporal",
                model_type="supervised",
                mae=round(mae, 3) if mae is not None else None,
                rmse=round(rmse, 3) if rmse is not None else None,
                r2_score=round(r2, 3) if r2 is not None else None,
                samples_count=len(X_mat),
                real_samples_count=real_samples_count,
                synthetic_samples_count=synthetic_samples_count,
                trained_at=datetime.now(timezone.utc),
            ),
            narrative=narrative,
        )


class CustomerSegmentationService:
    """Modelo no supervisado de segmentación de clientes mediante K-Means RFM."""

    @staticmethod
    def segment_customers(
        db: Session,
        tenant_id: int,
        n_clusters: int = 4,
    ) -> CustomerSegmentationResponse:
        now = datetime.now(timezone.utc)

        # 1. Consultar historial de compras por cliente
        query = (
            select(
                Sale.customer_id,
                func.max(Sale.created_at).label("last_purchase"),
                func.count(Sale.id).label("frequency"),
                func.coalesce(func.sum(Sale.total), 0).label("monetary"),
            )
            .where(
                Sale.tenant_id == tenant_id,
                Sale.status.in_(["CONFIRMED", "COMPLETED"]),
                Sale.customer_id != None,  # noqa: E711
            )
            .group_by(Sale.customer_id)
        )
        real_rfm = db.execute(query).all()

        customer_profiles: list[dict[str, Any]] = []
        for r in real_rfm:
            last_date = r[1]
            if last_date.tzinfo is None:
                last_date = last_date.replace(tzinfo=timezone.utc)
            recency = max(0, (now - last_date).days)
            customer_profiles.append({
                "customer_id": r[0],
                "recency_days": recency,
                "frequency": int(r[2]),
                "monetary": Decimal(str(r[3])),
                "data_source": "real",
            })

        # Si el tenant tiene menos de 20 clientes registrados, aumentamos con el generador sintético
        synthetic_samples_count = 0
        if len(customer_profiles) < 20:
            synthetic_profiles = SyntheticDataService.generate_customer_rfm_profiles(db, tenant_id, num_customers=60)
            customer_profiles.extend({**profile, "data_source": "synthetic"} for profile in synthetic_profiles)
            synthetic_samples_count = len(synthetic_profiles)

        total_customers = len(customer_profiles)
        if total_customers == 0:
            return CustomerSegmentationResponse(
                algorithm="K-Means RFM Normalizado",
                clusters_count=0,
                silhouette_score=0.0,
                inertia=0.0,
                segments=[],
                anomalies=[],
                anomalies_count=0,
                metrics=MLModelMetrics(
                    model_name="K-Means Clustering RFM con StandardScaler",
                    model_type="unsupervised",
                    silhouette_score=0.0,
                    inertia=0.0,
                    samples_count=0,
                    real_samples_count=len(real_rfm),
                    synthetic_samples_count=synthetic_samples_count,
                    trained_at=datetime.now(timezone.utc),
                ),
                narrative="No fue posible ejecutar la segmentación ni detectar anomalías: datos RFM insuficientes.",
            )

        X_raw = np.array([
            [float(p["recency_days"]), float(p["frequency"]), float(p["monetary"])]
            for p in customer_profiles
        ], dtype=float)
        feature_values_are_valid = bool(np.isfinite(X_raw).all())
        unique_feature_rows = np.unique(X_raw, axis=0).shape[0]

        # 2. Preprocesamiento: StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_raw)

        # 3. K-Means clustering; collapse degenerate data to one safe cluster.
        effective_clusters = min(n_clusters, total_customers)
        if unique_feature_rows < 2 or effective_clusters < 2 or not feature_values_are_valid:
            labels = np.zeros(total_customers, dtype=int)
            sil_score = 0.0
            inertia = 0.0
            effective_clusters = 1
        else:
            kmeans = KMeans(n_clusters=effective_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_scaled)

            # 4. Métricas de evaluación no supervisada
            try:
                sil_score = float(silhouette_score(X_scaled, labels))
            except Exception:
                sil_score = 0.0
            inertia = float(kmeans.inertia_)

        # IsolationForest gives a deterministic, ID-free anomaly view over RFM.
        anomaly_records: list[CustomerAnomalyItem] = []
        anomalies_count = 0
        if total_customers >= 2 and unique_feature_rows >= 2 and feature_values_are_valid:
            try:
                detector = IsolationForest(random_state=42, contamination="auto")
                findings = detector.fit_predict(X_scaled)
                scores = -detector.decision_function(X_scaled)
                anomaly_indexes = [index for index, finding in enumerate(findings) if finding == -1]
                anomalies_count = len(anomaly_indexes)
                anomaly_indexes.sort(key=lambda index: float(scores[index]), reverse=True)
                anomaly_records = [
                    CustomerAnomalyItem(
                        recency_days=float(customer_profiles[index]["recency_days"]),
                        frequency=float(customer_profiles[index]["frequency"]),
                        monetary=Decimal(str(customer_profiles[index]["monetary"])),
                        anomaly_score=round(float(scores[index]), 6),
                        data_source=customer_profiles[index]["data_source"],
                    )
                    for index in anomaly_indexes[:10]
                ]
            except (ValueError, RuntimeError):
                anomalies_count = 0
                anomaly_records = []

        # 5. Agrupación y caracterización de segmentos
        cluster_data: dict[int, list[dict[str, Any]]] = {c: [] for c in range(effective_clusters)}
        for idx, lbl in enumerate(labels):
            cluster_data[lbl].append(customer_profiles[idx])

        # Ordenar clusters por valor monetario promedio
        sorted_clusters = sorted(
            ((cluster_id, members) for cluster_id, members in cluster_data.items() if members),
            key=lambda item: sum(float(x["monetary"]) for x in item[1]) / len(item[1]),
            reverse=True,
        )

        segment_names = [
            ("Clientes VIP / Champions", "Mayor frecuencia y ticket promedio más alto; clientes leales del atelier.", "Programa de fidelización exclusivo, acceso anticipado a nuevas colecciones."),
            ("Clientes Frecuentes en Crecimiento", "Compras periódicas con potencial de escalamiento de gasto.", "Descuentos en segunda prenda y beneficios por volumen."),
            ("Clientes en Riesgo de Abandono", "Historial valioso pero sin compras en los últimos 45-120 días.", "Campaña de reactivación con cupones personalizados por email/SMS."),
            ("Clientes Nuevos u Ocasionales", "Compra reciente o esporádica con ticket moderado.", "Secuencia de bienvenida y recomendación de prendas básicas."),
        ]

        segments: list[CustomerSegmentItem] = []

        for rank, (c_id, members) in enumerate(sorted_clusters):
            meta = segment_names[min(rank, len(segment_names) - 1)]
            count = len(members)
            pct = round((count / total_customers) * 100, 1)
            avg_rec = round(float(np.mean([m["recency_days"] for m in members])), 1)
            avg_freq = round(float(np.mean([m["frequency"] for m in members])), 1)
            avg_mon = Decimal(str(round(float(np.mean([float(m["monetary"]) for m in members])), 2)))

            segments.append(
                CustomerSegmentItem(
                    segment_id=rank + 1,
                    name=meta[0],
                    description=meta[1],
                    customer_count=count,
                    percentage=pct,
                    avg_recency_days=avg_rec,
                    avg_frequency=avg_freq,
                    avg_monetary=avg_mon,
                    suggested_action=meta[2],
                )
            )

        narrative = (
            f"Segmentación de clientes completada mediante K-Means RFM: {total_customers} clientes analizados y agrupados en {effective_clusters} clusters estratégicos. "
            f"Calidad de partición evaluada: Coeficiente Silhouette={sil_score:.3f}, Inercia={inertia:.1f}. "
            f"El segmento líder '{segments[0].name}' representa el {segments[0].percentage}% de los clientes con un ticket promedio de Bs {segments[0].avg_monetary}. "
            f"Acción prioritaria: Implementar la campaña de reactivación recomendada para el segmento '{segments[min(2, len(segments) - 1)].name}'. "
            f"Detección de anomalías RFM: {anomalies_count} perfiles atípicos encontrados; se muestran hasta {len(anomaly_records)}."
            + (" Datos RFM insuficientes o degenerados para detectar anomalías." if unique_feature_rows < 2 else "")
        )

        return CustomerSegmentationResponse(
            algorithm="K-Means RFM Normalizado",
            clusters_count=effective_clusters,
            silhouette_score=round(sil_score, 3),
            inertia=round(inertia, 2),
            segments=segments,
            anomalies=anomaly_records,
            anomalies_count=anomalies_count,
            metrics=MLModelMetrics(
                model_name="K-Means Clustering RFM con StandardScaler",
                model_type="unsupervised",
                silhouette_score=round(sil_score, 3),
                inertia=round(inertia, 2),
                samples_count=total_customers,
                real_samples_count=len(real_rfm),
                synthetic_samples_count=synthetic_samples_count,
                trained_at=datetime.now(timezone.utc),
            ),
            narrative=narrative,
        )

    @staticmethod
    def retrain_models(db: Session, tenant_id: int) -> MLTrainingResponse:
        forecast_res = DemandForecastService.forecast_demand(db, tenant_id)
        segment_res = CustomerSegmentationService.segment_customers(db, tenant_id)

        return MLTrainingResponse(
            status="SUCCESS",
            message="Modelos de Machine Learning supervisado y no supervisado reentrenados y calibrados con éxito.",
            supervised_metrics=forecast_res.metrics,
            unsupervised_metrics=segment_res.metrics,
        )
