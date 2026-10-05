from .models import Competitor
from .repository import CompetitorRepository, InMemoryCompetitorRepository


class CompetitorService:
    def __init__(self, repository: CompetitorRepository | None = None) -> None:
        self._repository = repository or InMemoryCompetitorRepository()

    def list(self) -> list[Competitor]:
        return self._repository.list()

    def add(self, competitor: Competitor) -> Competitor:
        return self._repository.add(competitor)
