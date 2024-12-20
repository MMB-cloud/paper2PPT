from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.visualization.scatter import Scatter
from pymoo.core.problem import Problem
import numpy as np


class MooModelSolver(Problem):

    def __init__(self, n_var, n_obj, n_constr, c_coef, constr_coef):
        # n_var:决策变量数量
        # n_obj:目标函数数量
        # n_constr:约束函数数量
        # f1_coef:目标函数f1系数向量
        # xl:决策变量下限
        # xu:决策变量上限
        super().__init__(n_var=n_var, n_obj=n_obj, n_constr=n_constr, xl=np.zeros(n_var), xu=np.ones(n_var))
        self.f1_coef = c_coef[0]
        self.f2_coef = c_coef[1]
        self.f3_coef = c_coef[2]
        self.n_var = n_var
        self.constr_coef = constr_coef

    def _evaluate(self, x, out, *args, **kwargs):
        # 目标函数一: 权重分数最大化
        f1 = -x[:, :] * self.f1_coef
        # 目标函数二：信息简洁性
        f2 = x[:, :] * self.f2_coef
        i, j = np.indices((self.f3_coef.shape[0], self.f3_coef.shape[1]))
        x_all = x[:, i] * x[:, j]
        coef_all = self.f3_coef[i, j]
        f3 = -np.sum(x_all * coef_all, axis=2)
        out["F"] = np.column_stack([np.sum(f1, axis=1), np.sum(f2, axis=1), np.sum(f3, axis=1)])
        # 计算约束违反值
        g = self.constr_coef[0] - np.sum(x[:, :] * self.f2_coef, axis=1)  # 长度下限约束
        h = np.sum(x[:, :] * self.f2_coef, axis=1) - self.constr_coef[1]  # 长度上限约束
        #out["G"] = np.column_stack([np.maximum(0, g), np.maximum(0, -h)])
        out["G"] = np.column_stack([g, h])
        # print(out)
