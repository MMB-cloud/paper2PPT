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


class TFModel:
    script = {}

    def __init__(self) -> None:
        pass

    def set_script(self, script):
        self.script = script

    def build_and_solve_by_sent(self, node, topn=3):
        sent_node_lst = node.getleafnodes()  # 所有叶子节点
        # 计算句子权重
        sent_lst = [sent.getTextContent() for sent in sent_node_lst if sent.getTextContent() is not None]
        try:
            # 句子向量化
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(sent_lst)
            sentence_scores = []
            # 计算句子分数
            for i in range(tfidf_matrix.shape[0]):
                score = 0
                tfidf_scores = tfidf_matrix[i].toarray()[0]
                for j in range(len(tfidf_scores)):
                    if tfidf_scores[j] > 0:
                        score += tfidf_scores[j]
                sentence_scores.append(score)
            # 获取排名前 top_n 的句子
            sorted_sentences = sorted(((i, score) for i, score in enumerate(sentence_scores)), key=lambda x: x[1],
                                      reverse=True)[:topn]
            summary_indices = [index for index, _ in sorted_sentences]
            # 标记chosen
            chosen_node_lst = [sent_node_lst[i] for i in summary_indices]
            for node in chosen_node_lst:
                node.setChosen(True)
            return chosen_node_lst
        except:
            print("向量化出错，"','.join(sent_lst))
            return []
