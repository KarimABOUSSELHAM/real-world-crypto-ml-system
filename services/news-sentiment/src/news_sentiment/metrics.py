from typing import Any

from opik.evaluation.metrics import base_metric, score_result


class SameETHScoreMetric(base_metric.BaseMetric):
    def __init__(self, name: str):
        self.name = name

    def score(self, input: str, output: str, **ignored_kwargs: Any):
        # Add you logic here

        return score_result.ScoreResult(
            value=0, name=self.name, reason='Optional reason for the score'
        )
