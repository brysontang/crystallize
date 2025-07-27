from pathlib import Path
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph

if __name__ == "__main__":
    exp = Experiment.from_yaml(Path(__file__).parent / "config.yaml")
    exp.validate()
    res = exp.run()
    print(res.metrics.baseline.metrics)

    # Build a graph from the same YAML and visualize dependencies
    graph = ExperimentGraph.from_yaml(Path(__file__).parent / "config.yaml")
    ExperimentGraph.visualize_from_yaml(Path(__file__).parent / "config.yaml")
