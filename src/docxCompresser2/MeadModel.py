from common.Utils import Utils
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import numpy as np

'''
    入参：
        node:最小层级的标题,包含1-n段
        max_length:压缩比例
    出参：
        node:包含选中节点
'''

utils = Utils()


# 去除冗余的句子（根据相似度矩阵）
# 去除冗余的句子（根据相似度矩阵）
def remove_redundant_sentences(sentences, similarity_matrix, selected_indices, threshold=0.5):
    non_redundant_indices = []
    for i in range(len(sentences)):
        if i not in selected_indices:
            is_redundant = False
            for j in selected_indices:
                if similarity_matrix[i][j] > threshold:  # 如果相似度大于阈值，则认为是冗余的
                    is_redundant = True
                    break
            if not is_redundant:
                non_redundant_indices.append(i)
    return non_redundant_indices



class MeadModel:
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
            # 计算句子相似度
            similarity_matrix = cosine_similarity(tfidf_matrix)
            # 聚类
            km = KMeans(n_clusters=topn)
            km.fit(tfidf_matrix)
            # 每个聚簇选择一个句子
            cluster_centers = km.cluster_centers_
            sentence_scores = np.array(
                [np.dot(tfidf_matrix[i].toarray(), cluster_centers[km.labels_[i]]).flatten()[0] for i in
                 range(len(sent_lst))])
            # 根据句子重要性排序，优先选择重要句子
            ranked_indices = sentence_scores.argsort()[-len(sent_lst):][::-1]  # 按照句子重要性排序，重要的在前
            # 从最重要的句子开始选择
            selected_indices = []
            for idx in ranked_indices:
                if len(selected_indices) < topn:
                    selected_indices.append(idx)
                else:
                    break
                # 去除冗余句子
            non_redundant_indices = remove_redundant_sentences(sent_lst, similarity_matrix, selected_indices)

            # 确保选择的句子数目不超过 topn
            final_selected_indices = selected_indices + non_redundant_indices
            final_selected_indices = final_selected_indices[:topn]
            # 从选中的句子中选择最重要的句子
            chosen_node_lst = [sent_node_lst[i] for i in final_selected_indices]
            # for node in chosen_node_lst:
            #     node.setChosen(True)
            return chosen_node_lst
        except:
            print("向量化出错，"','.join(sent_lst))
            return []
