from pathlib import Path
from crystallize.experiments.experiment import Experiment

if __name__ == "__main__":
    exp = Experiment.from_yaml(Path(__file__).parent / "config.yaml")
    exp.validate()
    res = exp.run()
    print(res.metrics.baseline.metrics)
