from crystallize.core.experiment import Experiment
from crystallize.core.pipeline import Pipeline
from crystallize.datasources.simple_data_source import SimpleDataSource
from crystallize.steps.identity_step import IdentityStep
from crystallize.core.stat_test import StatisticalTest
from crystallize.core.treatment import Treatment
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.pipeline_step import PipelineStep

class DummyStatTest(StatisticalTest):
    def run(self, baseline, treatment, alpha=0.05):
        return {"p_value": 1.0, "significant": False}

class DummyStep(PipelineStep):
    def __call__(self, data, ctx):
        return {'dummy_metric': 1}
    
    @property
    def params(self):
        return {}

if __name__ == "__main__":
  datasource = SimpleDataSource([1, 2, 3])
  pipeline = Pipeline([IdentityStep(), DummyStep()])

  # Minimal no-op treatment
  treatment = Treatment(name="noop", apply_fn=lambda ctx: None)

  # Minimal dummy hypothesis
  hypothesis = Hypothesis(
      metric="dummy_metric",
      direction="equal",
      statistical_test=DummyStatTest()
  )

  experiment = Experiment(
      pipeline=pipeline,
      datasource=datasource,
      treatments=[treatment],
      hypothesis=hypothesis
  )

  result = experiment.run()
  print(result.metrics)
  print(result.errors)