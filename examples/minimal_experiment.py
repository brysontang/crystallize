from crystallize.core.experiment import Experiment
from crystallize.core.pipeline import Pipeline
from crystallize.core.datasource import SimpleDataSource
from crystallize.core.pipeline_step import IdentityStep

if __name__ == "__main__":
  experiment = Experiment(pipeline=Pipeline([IdentityStep()]),
                        datasource=SimpleDataSource([1,2,3]))
  result = experiment.run()
  print(result)