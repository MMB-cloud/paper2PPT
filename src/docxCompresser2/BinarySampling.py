from pymoo.operators.sampling.rnd import FloatRandomSampling
import numpy as np


class BinarySampling(FloatRandomSampling):
    def _do(self, problem, n_samples, **kwargs):
        X = super()._do(problem, n_samples, **kwargs)
        X[X < 0.5] = 0
        X[X >= 0.5] = 1
        return X