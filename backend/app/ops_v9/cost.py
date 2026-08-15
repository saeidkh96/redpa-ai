from app.ops_v9.schemas import CostEstimate, CostEstimateRequest


class CostEstimator:
    @staticmethod
    def estimate(payload: CostEstimateRequest) -> CostEstimate:
        backend = payload.backend_replicas * payload.monthly_backend_replica_eur
        workers = payload.worker_replicas * payload.monthly_worker_replica_eur
        total = backend + workers + payload.managed_data_services_eur + payload.observability_eur + payload.other_eur
        return CostEstimate(
            backend_eur=round(backend,2), workers_eur=round(workers,2),
            data_services_eur=round(payload.managed_data_services_eur,2),
            observability_eur=round(payload.observability_eur,2), other_eur=round(payload.other_eur,2),
            monthly_total_eur=round(total,2), annual_total_eur=round(total*12,2),
        )
