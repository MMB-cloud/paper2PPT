import cvxpy as cp
from numpy import array
import numpy as np
import pandas as pd
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.visualization.scatter import Scatter
from pymoo.core.problem import Problem
from pymoo.operators.sampling.rnd import FloatRandomSampling
from src.docxCompresser2.BinarySampling import BinarySampling
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from src.docxCompresser2.MooModelSolver import MooModelSolver
from src.docxCompresser2.BinaryCrossover import BinaryCrossover
from src.docxCompresser2.BinaryMutation import BinaryMutation
from src.docxCompresser2.CustomTermination import CustomTermination
from pymoo.termination import get_termination
from pymoo.termination.collection import TerminationCollection
from common.Utils import Utils

utils = Utils()


def check(node, strlist):
    matched = False
    for str in strlist:
        if str in node.getTextContent().replace(" ", ""):
            matched = True
            break
    return matched


# 考虑图片[[图表描述，关键字眼：如图……\如下图\如上图],[图表],[图4-1 xxx]]
# 出现图片描述时需要增加权重，然后绑定三元组一起选中
def calculate_weight(para_lst, keywords, ab_sent_lst, seg_title_lst):
    # 首段和尾段特殊处理
    w_pos = []  # 位置权重
    w_tf = []  # 特征词权重
    w_sim = []  # 相似度权重
    w_cov = []  # 重叠度权重
    # 计算位置权重
    for i_para, para in enumerate(para_lst):
        sents = para.getleafnodes()
        # 首段句子
        if i_para == 0:
            x = len(sents)
            for i_sent, sent in enumerate(sents):
                w_pos.append(1 + (x - i_sent) / x)
        # 尾段句子
        elif i_para == len(para_lst) - 1:
            y = len(sents)
            for i_sent, sent in enumerate(sents):
                w_pos.append(1 + ((y - i_sent) / y) * 0.5)
        # 非首尾段句子 位置权重只关注首尾
        else:
            for i_sent, sent in enumerate(sents):
                if i_sent == 0:
                    w_pos.append(1)
                elif i_sent == len(sents) - 1:
                    w_pos.append(0.5)
                else:
                    w_pos.append(0.2)

    sent_lst = []
    for para in para_lst:
        sent_lst.extend(para.getChildren())
    for sent in sent_lst:
        seg_sent = utils.seg_depart(sent.getTextContent(), delete_stopwords=True)
        # 计算特征词权重
        wtf = 0.0
        for word in seg_sent:
            wtf += keywords[word] if word in keywords.keys() else 0
        w_tf.append(wtf / len(seg_sent) if len(seg_sent) != 0 else 0)
        # 计算相似度权重
        wsim = 0.0
        for ab_sent in ab_sent_lst:
            ab_seg_sent = utils.seg_depart(ab_sent.getTextContent(), delete_stopwords=True)
            wsim = max(wsim, getCosScore(seg_sent, ab_seg_sent))
        w_sim.append(wsim)
        # 计算重叠度权重：论文标题和这一级的重叠度
        wcov = 0.0
        overlap_word_list = list(set(seg_title_lst).intersection(set(seg_sent)))
        wcov = float(len(overlap_word_list)) / float(len(seg_sent)) if len(
            seg_sent) != 0 else 0.0
        w_cov.append(wcov)

    w_pos = min_max_normalize(np.array(w_pos))
    w_tf = min_max_normalize(np.array(w_tf))
    w_sim = min_max_normalize(np.array(w_sim))
    w_cov = min_max_normalize(np.array(w_cov))
    weights = w_pos * 0.3 + w_tf * 0.4 + w_sim * 0.2 + w_cov * 0.1
    return weights


def calculate_len(para_lst):
    sents = [node for para in para_lst for node in para.getleafnodes()]
    lens = np.array([len(sent.getTextContent()) for sent in sents])
    return lens


def calculate_similarity(para_lst):
    sents = [node for para in para_lst for node in para.getleafnodes()]
    seg_sents = [utils.seg_depart(sent.getTextContent(), delete_stopwords=True) for sent in sents]
    len_ = len(seg_sents)
    sim = np.zeros((len_, len_))
    for i in range(len(seg_sents)):
        for j in range(i + 1, len(seg_sents)):
            cosScore = getCosScore(seg_sents[i], seg_sents[j])
            sim[i, j] = cosScore
            sim[j, i] = cosScore
    if np.isnan(sim).any():
        sim[np.isnan(sim)] = 0
    return sim


def calculate_constr_len(para_lst, xl, xu):
    res = []
    sents = [node for para in para_lst for node in para.getleafnodes()]
    lens = np.array([len(sent.getTextContent()) for sent in sents])
    res = [np.sum(lens) * xl * 0.01, np.sum(lens) * xu * 0.01]
    return res


def getCosScore(seg_sent1, seg_sent2):
    list_word1 = (",".join(seg_sent1)).split(",")
    list_word2 = (",".join(seg_sent2)).split(",")

    # 列出所有的词，取并集
    key_word = list(set(list_word1).union(list_word2))
    # 给定形状和类型的用0填充的矩阵存储向量
    word_vector1 = np.zeros(len(key_word))
    word_vector2 = np.zeros(len(key_word))
    # 计算词频
    # 依次确定向量的每个位置的值
    for i in range(len(key_word)):
        # 遍历key_word中每个词在句子中的出现次数
        for j in range(len(seg_sent1)):
            if key_word[i] == seg_sent1[j]:
                word_vector1[i] += 1
        for k in range(len(seg_sent2)):
            if key_word[i] == seg_sent2[k]:
                word_vector2[i] += 1
    # 余弦相似度计算
    # dist1 = float(np.dot(word_vector1, word_vector2) / (np.linalg.norm(word_vector1) * np.linalg.norm(word_vector2)))
    norm = np.linalg.norm(word_vector1) * np.linalg.norm(word_vector2)

    dist1 = float(np.dot(word_vector1, word_vector2) / (
            np.linalg.norm(word_vector1) * np.linalg.norm(word_vector2)))
    # dist1 = dist1 if dist1 != nan else 0.0
    return dist1


def min_max_normalize(data):
    if data.size == 0:
        return 0
    min_val = np.min(data)
    max_val = np.max(data)
    return (data - min_val) / (max_val - min_val)


def add_para_node(para_lst, node):
    if node.getType() != 0 and node.getType() != 1:
        return
    if node.getType() == 1:
        para_lst.append(node)
        return
    for c in node.getChildren():
        add_para_node(para_lst, c)


def get_chosen(result, para_lst):
    sent_lst = []
    for para in para_lst:
        sent_lst.extend(para.getChildren())
    chosen_lst = []
    for i, res in enumerate(result):
        if res == 1:
            chosen_lst.append(sent_lst[i])
    return chosen_lst


"""
用于内容选取的多目标规划模型
    目标: 最大化生成的幻灯片的内容单元总权重
    约束:
        - 静态约束
            1. 总文字量约束
            2. 图表、图标题和对图表的描述性句子是绑定在一起的，要么都选，要么都不选
        - 动态约束(基于制作学术论文幻灯片的经验设定的内容选取的规则约束，存储在剧本当中，需要加载并转化为约束条件)
            1. 哪些子章节必须被选中
            2. 子章节内容选取的句子的数量的期望值
            3. 哪些章节中如果出现了图表，则图表必须被保留
"""


class MooModel:
    def __init__(self) -> None:
        pass

    """模型构建与求解"""

    # solver = MooModelSolver()

    def build_and_solve_by_node(self, node, keywords, abstract, title):
        leafNodes = node.getleafnodes()
        # 需要保留段落关系计算权重
        para_lst = []
        add_para_node(para_lst, node)
        # sent_lst = [sent.getTextContent() for sent in leafNodes]
        ab_sent_lst = abstract.getleafnodes()
        title_lst = []
        title_lst.extend(utils.seg_depart(title, delete_stopwords=True))
        title_lst.extend(utils.seg_depart(node.getTextContent(), delete_stopwords=True))
        # 目标函数系数
        c_coef = []
        c_coef.append(calculate_weight(para_lst, keywords, ab_sent_lst, title_lst))
        c_coef.append(calculate_len(para_lst))
        c_coef.append(calculate_similarity(para_lst))
        # 约束变量系数
        constr_coef = calculate_constr_len(para_lst, 10, 25)
        # 决策变量数量
        n_var = len(c_coef[0]) if isinstance(c_coef[0],np.ndarray) else 0
        # 创建问题实例
        solver = MooModelSolver(n_var, 3, 2, c_coef, constr_coef)
        # 设置算法参数
        algorithm = NSGA2(
            pop_size=100,
            # sampling=FloatRandomSampling(),
            sampling=BinarySampling(),
            # crossover=SBX(prob=0.9, eta=15),
            crossover=BinaryCrossover(),
            mutation=BinaryMutation(),
            # mutation=PM(eta=20),
            eliminate_duplicates=True
        )
        # 设置混合终止准则
        #termination1 = get_termination("n_gen", 100)  # 函数评估次数不超过10000次
        #termination2 = get_termination("ftol", 1e-6)  # 目标函数相对改进小于1e-6
        #termination3 = get_termination("cv", 1e-8)  # 函数评估次数不超过10000次
        #mixed_termination = TerminationCollection([termination1, termination2, termination3])
        # 执行优化
        try:
            res = minimize(
                problem=solver,
                algorithm=algorithm,
                #termination=mixed_termination,
                termination=get_termination('moo', n_max_gen=100),
                seed=1,
                verbose=False,
                return_least_infeasible=True
            )
            # 进行最小-最大归一化
            F = res.F * [-1, 1, -1]
            min_vals = np.min(F, axis=0)
            max_vals = np.max(F, axis=0)
            normalized_F = (F - min_vals) / (max_vals - min_vals)

            # 根据给定权重进行加权计算
            weights = np.array([0.5, 0.2, 0.3])
            weighted_result = np.dot(normalized_F, weights)
            idx = np.argmax(weighted_result, axis=0)
            result = res.X[idx]
            chosen_lst = get_chosen(result, para_lst)
            for chosen in chosen_lst:
                chosen.setChosen(True)
                # print(chosen.getTextContent())
            return chosen_lst
        except Exception as e:
            # 捕获到任何异常后，进入这个代码块
            print(f"优化过程出现异常: {str(e)}")
            return []

        #print(res.X)
        # target_weight = res.F[0] * 0.5 + res.F[1] * 0.2 +

        # 可视化结果
        # plot = Scatter()
        # plot.add(res.F)
        # plot.show()
