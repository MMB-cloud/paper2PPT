from pymoo.core.termination import Termination
from pymoo.util.misc import has_feasible


class CustomTermination(Termination):
    def __init__(self, n_max_gen=100, min_progress=0.0):
        super().__init__()
        self.n_max_gen = n_max_gen
        self.min_progress = min_progress
        self.gen = 0
        self.last_f = None

    def _do(self, algorithm):
        # 获取当前迭代次数
        self.gen = algorithm.n_gen

        # 获取当前最优解的目标函数值
        f = algorithm.opt.get("F")

        # 初始化 last_f
        if self.last_f is None:
            self.last_f = f
            return False, {"progress": float('inf')}

        # 计算 progress
        change = abs(f - self.last_f)
        self.last_f = f

        # 避免除以零
        progress = change / (abs(self.last_f) + 1e-32)

        # 检查是否满足终止条件
        if self.gen >= self.n_max_gen:
            return True, {"progress": progress}

        if progress <= self.min_progress:
            print(f"Converged at generation {self.gen} with progress {progress}.")
            return True, {"progress": progress}

        return False, {"progress": progress}

#
# # 示例使用
# from pymoo.optimize import minimize
# from pymoo.algorithms.soo.nonconvex.ga import GA
# from pymoo.problems.single import Sphere
#
# problem = Sphere()
# algorithm = GA(pop_size=100)
# termination = CustomTermination(n_max_gen=100)
#
# res = minimize(problem, algorithm, termination=termination, seed=1)
# print(res.F)