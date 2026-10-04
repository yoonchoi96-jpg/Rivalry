from core.intelligence.engine import IntelligenceStore
from .queue import InMemoryJobQueue


# Shared only inside one process. Replace both with shared persistence when
# API and worker run as separate processes or machines.
job_queue = InMemoryJobQueue()
intelligence_store = IntelligenceStore()
