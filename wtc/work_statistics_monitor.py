from work_statistics import WorkStatistics


class WordStatisticsMonitor:
    __slots__ = ('_stats', )

    def __enter__(self, db: str):
        self._stats = WorkStatistics.from_db(db)
        ...  # TODO

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb):
        ...  # TODO

    def print(self):
        ...  # TODO

    def update(self):
        ...  # TODO
