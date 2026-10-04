from .queue import InMemoryJobQueue


# Shared only inside one process. Replace this implementation with a shared backend
# when API and worker run as separate processes or machines.
job_queue = InMemoryJobQueue()
