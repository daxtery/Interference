from typing import Any, List

from dataclasses import dataclass

from trigger.train.cluster.ecm.ecm import ECM
from matplotlib import pyplot as plt
from sklearn.metrics.cluster import adjusted_rand_score

import numpy as np
import pickle as pk
import json
import os

import time


@dataclass
class TestCase:
    inputs: List[Any]
    correct: List[Any]
    path: str = ""
    name: str = ""
    description: str = ""


def read_pkl(input_path: str, name: str = "", description: str = "") -> TestCase:
    with open(input_path, 'rb') as f:
        stream = pk.load(f)

    return TestCase(
        inputs=[np.array([data[0], data[1]]) for data in stream],
        correct=[],
        path=input_path,
        name=name,
        description=description,
    )


def test_2d(ecm: ECM, case: TestCase, should_do_plot: bool = True, want_to_know_clusters: bool = False, want_to_know_inputs_and_correct: bool = False) -> object:
    X = [data[0] for data in case.inputs]
    Y = [data[1] for data in case.inputs]

    tic = time.perf_counter()

    for v in case.inputs:
        ecm.add(v)

    toc = time.perf_counter()

    time_to_add = f"{toc - tic:0.4f} seconds"

    if should_do_plot:
        # If there are some reds, this means we didn't put them in a cluster, which *SHOULDN'T* happen
        plt.scatter(X, Y, c='red', edgecolors='black', marker='o')

        colors = ['#6b6b6b', '#ff2994', '#b3b3b3', '#ffd1e8',
                  '#6b00bd', '#0000f0', '#c880ff', '#8080ff',
                  '#005757', '#00b300', '#00b3b3', '#005700',
                  '#ada800', '#bd7b00', '#fff957', '#ff974d',
                  '#ff4d4d']

        for i, cluster in enumerate(sorted(ecm.clusters, key=lambda cluster: cluster.center[0])):
            color = colors[i % len(colors)]
            position = (cluster.center[0], cluster.center[1])

            # circle = plt.Circle(position, cluster.radius,
            #                     color=color, fill=False, linestyle="--")
            # plt.gcf().gca().add_artist(circle)

            plt.scatter(position[0], position[1], c=color,
                        edgecolors='black', marker='D', linewidths=2)

            _X = []
            _Y = []

            for instance in cluster.instances:
                _X.append(instance[0])
                _Y.append(instance[1])

            plt.scatter(_X, _Y, c=color, edgecolors='black')

        plt.show()

    tic = time.perf_counter()

    predicted = [ecm.index_of_cluster_containing(
        instance) for instance in case.inputs]

    toc = time.perf_counter()

    time_to_predict = f"{toc - tic:0.4f} seconds"

    results = {
        "used algorithm": ecm.describe(),
        "test": {
            "name": case.name,
            "path": case.path,
            "description": case.description,
            "inputs": case.inputs if want_to_know_inputs_and_correct else [],
            "correct": case.correct if want_to_know_inputs_and_correct else [],
        },
        "time to add": time_to_add,
        "time to predict": time_to_predict,
        "clusters": [
            {
                "#": i,
                "center": cluster.center.tolist(),
                "radius": cluster.radius,
                "instances": [instance.tolist() for instance in cluster.instances]
            } for i, cluster in enumerate(ecm.clusters)
        ] if want_to_know_clusters else [],
        "scores": {
            "sklearn.metrics.cluster.adjusted_rand_score": adjusted_rand_score(case.correct, predicted),
        }

    }

    return results


def save_results(results: Any, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as outfile:
        # TODO indent=4 is just so it's easier to see, not needed!
        json.dump(results, outfile, indent=4)


def compute_filename(base: str, ecm: ECM, case: TestCase, override: bool = False) -> str:
    algorithm = ecm.describe()

    algorithm_name = algorithm["name"] + " v2"
    algorithm_parameters = algorithm["parameters"]

    algorithm_parameters_parts = [
        f"{name}={value}" for name, value in algorithm_parameters.items()
    ]

    wanted = f"{case.name} ; {algorithm_name} = {';'.join(algorithm_parameters_parts)}"
    proposed = wanted + ".json"

    if not override:
        extra = 0
        while os.path.exists(f"{base}/{proposed}"):
            proposed = wanted + f"_{extra}.json"
            extra += 1

    return proposed


if __name__ == "__main__":

    cases = [read_pkl("examples/2D_stream/1_r", "1_r",
                      "2D stream")
             ]

    dts = [1000, 100, 10, 250]

    for case in cases:
        for dt in dts:
            ecm = ECM(distance_threshold=dt)

            results = test_2d(ecm, case, False, False, False)

            filename = compute_filename(
                "examples/2D_points_results", ecm, case, True)

            save_results(results, "examples/2D_points_results/" + filename)
