from common.Utils import Utils
import networkx as nx
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

'''
    入参：
        node:最小层级的标题,包含1-n段
        max_length:压缩比例
    出参：
        node:包含选中节点
'''

utils = Utils()


# 考虑图片[[图表描述，关键字眼：如图……\如下图\如上图],[图表],[图4-1 xxx]]
# 出现图片描述时需要增加权重，然后绑定三元组一起选中

def calculate_weight(sent_lst, keywords):
    position_weights = []
    length_weights = []
    keyword_weights = []
    # 数据需要做归一化
    for i, sentence in enumerate(sent_lst):
        # 句子位置权重：首句和尾句权重较高
        position_weight = 1.0 if i == 0 or i == len(sentence) - 1 else 0.8
        position_weights.append(position_weight)
        # 句子长度权重：较长的句子权重较高
        length_weight = min(len(sentence) / 50.0, 1.0)
        length_weights.append(length_weight)
        # 句子中关键词数量权重：关键词越多权重越高 用剧本中的词
        # 分词
        seg_sent = utils.seg_depart(sentence)
        # 计算剧本权重
        keyword_weight = 0
        for word in seg_sent:
            keyword_weight += keywords[word] if word in keywords.keys() else 0
        keyword_weights.append(keyword_weight)
        # 图片权重
        # keywords = jieba.analyse.extract_tags(sentence, topK=5)
        # 综合权重
        # weight = position_weight * 0.4 + length_weight * 0.3 + keyword_weight * 0.3

    position_weights = min_max_normalize(np.array(position_weights))
    length_weights = min_max_normalize(np.array(length_weights))
    keyword_weights = min_max_normalize(np.array(keyword_weights))
    weights = position_weights * 0.3 + length_weights * 0.3 + keyword_weights * 0.4
    return weights


def min_max_normalize(data):
    min_val = np.min(data)
    max_val = np.max(data)
    return (data - min_val) / (max_val - min_val)


class TextRankModel:
    script = {}

    def __init__(self) -> None:
        pass

    def set_script(self, script):
        self.script = script

    def build_and_solve_by_node(self, node, keywords, topn=3):
        # 获取所有节点（考虑图和表）
        graph_node_lst = []  # 包含图表和描述的节点
        sent_node_lst = node.getleafnodes()  # 所有叶子节点
        # 计算句子权重
        sent_lst = [sent.getTextContent() for sent in sent_node_lst]
        weights = calculate_weight(sent_lst, keywords)
        # 句子向量化
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(sent_lst)
        # 计算句子之间的相似度矩阵
        similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
        # 加入权重信息
        weight_similarity_matrix = similarity_matrix * weights
        # 构建图
        g = nx.from_numpy_array(weight_similarity_matrix)
        # 计算textrank分数
        scores = nx.pagerank(g, alpha=0.85)
        # 获取排名前 top_n 的句子
        sorted_sentences = sorted(((i, score) for i, score in enumerate(scores)), key=lambda x: x[1], reverse=True)[
                           :topn]
        summary_indices = [index for index, _ in sorted_sentences]
        summary = [sent_lst[i] for i in summary_indices]
        # 标记chosen
        chosen_node_lst = [sent_node_lst[i] for i in summary_indices]
        for node in chosen_node_lst:
            node.setChosen(True)
        print(','.join(summary) + '\n')
        # for sent_node in sent_node_lst:
        #    seg_word_lst = utils.seg_depart(sent_node.getTextContent())
        #    g.add_node(sent_node)
        #    seg_sent_node_lst.append(seg_word_lst)
        # 相似度 建边
        # 余弦/jaccard

        # textrank做迭代
