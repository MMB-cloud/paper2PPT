from pymoo.core.crossover import Crossover
import numpy as np


# 交叉
def binary_crossover(parent1, parent2):
    crossover_point = np.random.randint(1, len(parent1))
    child1 = np.concatenate((parent1[:crossover_point], parent2[crossover_point:]))
    child2 = np.concatenate((parent2[:crossover_point], parent1[crossover_point:]))
    return child1, child2


class BinaryCrossover(Crossover):
    def __init__(self):
        super().__init__(2, 2)  # 表示对2个父代进行操作，生成2个子代

    def _do(self, problem, X, **kwargs):
        _, n_matings, n_var = X.shape
        children = []
        for k in range(n_matings):
            parent1 = X[0, k, :]
            parent2 = X[1, k, :]
            child1, child2 = binary_crossover(parent1, parent2)
            children.append(np.array([child1, child2]))
        return np.array(children).transpose((1, 0, 2))
