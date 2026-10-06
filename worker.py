from core.jobs.handlers import JobHandlers
from core.jobs.runtime import (
    decision_policy_registry,
    decision_recommendation_repository,
    evidence_repository,
    observation_repository,
    measurement_repository,
    impact_repository,
    intelligence_store,
    job_queue,
    signal_repository,
    source_repository,
)
from core.research.executor import ResearchExecutor
from core.jobs.worker import JobWorker


research = ResearchExecutor(source_repository, evidence_repository)
handlers_obj = JobHandlers(
    store=intelligence_store,
    impact_repository=impact_repository,
    decision_policies=decision_policy_registry,
    decision_recommendations=decision_recommendation_repository,
    signal_repository=signal_repository,
    observation_repository=observation_repository,
)
handlers_obj.research = research
worker = JobWorker(job_queue, handlers_obj.registry())


if __name__ == "__main__":
    worker.drain()
