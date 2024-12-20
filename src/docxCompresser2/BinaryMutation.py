from pymoo.core.mutation import Mutation
import numpy as np


def binary_mutation(individual):
    mutation_index = np.random.randint(0, len(individual))
    individual[mutation_index] = 1 - individual[mutation_index]
    return individual


class BinaryMutation(Mutation):
    def __init__(self):
        super().__init__()

    def _do(self, problem, X, **kwargs):
        for i in range(len(X)):
            X[i] = binary_mutation(X[i])
        return X
