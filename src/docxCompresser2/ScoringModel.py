import os
import numpy as np
import math

from common.Utils import Utils

utils = Utils()


def check(node, strlist):
    matched = False
    for str in strlist:
        if str in node.getTextContent().replace(" ", ""):
            matched = True
            break
    return matched


"""
权重评分模型
    1. 句子的权重评分   三个评价指标
        1) 词语tfidf权重之和 (tfidf)
        2) 与摘要句子的最大余弦相似度 (maxCosine)
        3) 与论文题目、一级至三级章节标题、图表标题的词语重叠度 (overlap)
        final_score = \lambda_{1} * tfidf + \lambda_{2} * maxCosine + \lambda_{3} * maxCosine

        权重挑战规则如下:
            1. 单独一个句子成段, 权重 * 2
            2. 段落的句子数量大于3, 第一个句子的权重 * 2
    2. 图表的权重评分
        1) 全文句子的权重平均值 * 2 (2 * avgScore)
        2) 表格中词语tfidf中的权重之和 (tfidf)
        3) 惩罚因子  所在章节中含有的图表数量的倒数 (penalty)
        final_score = (2 * avgScore + tfidf) * penalty
    3. 章节的权重评分
        子节点的权重之和
"""


class ScoringModel:
    classifyScript = {}
    tfidf = {}
    abstractNode = None
    title = ""

    def __init__(self) -> None:
        pass

    def setScirpt(self, classifyResult):
        for script in utils.get_file_paths(utils.getScriptPath()):
            script_name = os.path.basename(script).replace('v2.json', '')
            if classifyResult == script_name:
                script_json = utils.json_to_dict(script)
                self.classifyScript = script_json
                self.tfidf = script_json["tfidf"]

    def setAbstractNode(self, node):
        self.abstractNode = node

    def sent_scoring(self, docxTree, classifyResult):
        # tfidf = {}
        # for script_path in utils.get_file_paths(utils.getScriptPath()):
        #     script_name = os.path.basename(script_path).replace(".json", "")
        #     if script_name == classifyResult:
        #         tfidf = utils.json_to_dict(script_path)["tfidf"]
        tfidf = self.classifyScript["tfidf"]
        scoreDic = {}  # 权重字典 {leafnode: [tfidf, maxCosine, overlap]}

        # 指标1: 词语tfidf权重之和
        for child in docxTree.getChildren():
            if check(child, ["摘要"]):
                pass
            else:
                leafnodes = child.getleafnodes()
                for leafnode in leafnodes:
                    score = 0.0
                    scoreDic[leafnode] = []  # 初始化评分向量
                    seg_list = utils.seg_depart(leafnode.getTextContent())
                    for word in set(seg_list):
                        if word in tfidf["main_text"]:
                            score += tfidf["main_text"][word] * math.sqrt(seg_list.count(word))
                    scoreDic[leafnode].append(score)

        # 指标2: 与摘要中句子集合的最大余弦相似度
        abstract_leafnodes = []
        for child in docxTree.getChildren():
            if check(child, ["摘要"]):
                abstract_leafnodes = child.getleafnodes()
            else:
                if len(abstract_leafnodes) != 0:
                    leafnodes = child.getleafnodes()
                    for leafnode in leafnodes:
                        maxCosine = 0.0
                        for abstract_leafnode in abstract_leafnodes:
                            seg_list1 = utils.seg_depart(leafnode.getTextContent(), delete_stopwords=True)
                            seg_list2 = utils.seg_depart(abstract_leafnode.getTextContent(), delete_stopwords=True)
                            list_word1 = (",".join(seg_list1)).split(",")
                            list_word2 = (",".join(seg_list2)).split(",")

                            # 列出所有的词，取并集
                            key_word = list(set(list_word1).union(list_word2))
                            # 给定形状和类型的用0填充的矩阵存储向量
                            word_vector1 = np.zeros(len(key_word))
                            word_vector2 = np.zeros(len(key_word))

                            # 计算词频
                            # 依次确定向量的每个位置的值
                            for i in range(len(key_word)):
                                # 遍历key_word中每个词在句子中的出现次数
                                for j in range(len(seg_list1)):
                                    if key_word[i] == seg_list1[j]:
                                        word_vector1[i] += 1
                                for k in range(len(seg_list2)):
                                    if key_word[i] == seg_list2[k]:
                                        word_vector2[i] += 1

                            # 余弦相似度计算
                            # dist1 = float(np.dot(word_vector1, word_vector2) / (np.linalg.norm(word_vector1) * np.linalg.norm(word_vector2)))
                            dist1 = float(np.dot(word_vector1, word_vector2) / (
                                    np.linalg.norm(word_vector1) * np.linalg.norm(word_vector2)))

                            if dist1 > maxCosine:
                                maxCosine = dist1
                        scoreDic[leafnode].append(maxCosine)

        # 指标3: 与论文题目、一级至三级章节标题的词语重叠度
        for child in docxTree.getChildren():
            if check(child, ["摘要"]):
                pass
            else:
                overlap = 0.0
                leafnodes = child.getleafnodes()
                title_word_list = utils.seg_depart(docxTree.getTitle(), delete_stopwords=True)
                # 与论文题目的词语重叠度
                for leafnode in leafnodes:
                    leafnode_word_list = utils.seg_depart(leafnode.getTextContent(), delete_stopwords=True)
                    overlap_word_list = list(set(title_word_list).intersection(set(leafnode_word_list)))
                    overlap += float(len(overlap_word_list)) / float(len(leafnode_word_list)) if len(
                        leafnode_word_list) != 0 else 0.0
                # 与一级至三级章节标题的词语重叠度
                for leafnode in leafnodes:
                    for ancestor in leafnode.getAncestors():
                        if ancestor.getOutLvl() in ['0', '1', '2']:
                            ancestor_word_list = utils.seg_depart(ancestor.getTextContent(), delete_stopwords=True)
                            leafnode_word_list = utils.seg_depart(leafnode.getTextContent(), delete_stopwords=True)
                            overlap_word_list = list(set(ancestor_word_list).intersection(set(leafnode_word_list)))
                            overlap += float(len(overlap_word_list)) / float(len(leafnode_word_list)) if len(
                                leafnode_word_list) != 0 else 0.0
                    scoreDic[leafnode].append(overlap)

        # 将三个指标先进行归一化处理，随后乘以它们各自的权重系数
        tfidf = []
        maxCosine = []
        overlap = []
        for leafnode in scoreDic:
            tfidf.append(scoreDic[leafnode][0])
            maxCosine.append(scoreDic[leafnode][1])
            overlap.append(scoreDic[leafnode][2])
        tfidf_max = max(tfidf)
        tfidf_min = min(tfidf)
        cosine_max = max(maxCosine)
        cosine_min = min(maxCosine)
        overlap_max = max(overlap)
        overlap_min = min(overlap)
        for leafnode in scoreDic:
            scoreDic[leafnode][0] = (scoreDic[leafnode][0] - tfidf_min) / (tfidf_max - tfidf_min)
            scoreDic[leafnode][1] = (scoreDic[leafnode][1] - cosine_min) / (cosine_max - cosine_min)
            scoreDic[leafnode][2] = (scoreDic[leafnode][2] - overlap_min) / (overlap_max - overlap_min)
            final_score = 0.5 * scoreDic[leafnode][0] + 0.3 * scoreDic[leafnode][1] + 0.2 * scoreDic[leafnode][2]
            leafnode.setScore(final_score)

        # 权重调整
        """
            1. 一个句子单独成一个段落->权重 * 2
            2. 一个段落的句子数量 > 3, 段落的首句权重 * 2
        """
        for child in docxTree.getChildren():
            if check(child, ["摘要"]):
                pass
            else:
                leafnodes = child.getleafnodes()
                for leafnode in leafnodes:
                    paranode = leafnode.getParent()
                    leafnode_num = len(paranode.getChildren())
                    if leafnode_num == 1:
                        leafnode.setScore(leafnode.getScore() * 2)
                    elif leafnode_num > 3:
                        if paranode.getChildren()[0] == leafnode:
                            leafnode.setScore(leafnode.getScore() * 2)

    # 最大Node作为入参，对句子评分
    # 7.18修改，二级Node，即一级标题作为入参
    def sentScoringByNodes(self, node):
        # if node.getType() != 0 or node.getOutLvl() != '0':
        if node.getType() != 0:
            return
        scoreDic = {}
        leafnodes = node.getleafnodes()
        for leafnode in leafnodes:
            scoreDic[leafnode] = []
            scoreDic[leafnode].append(self.tfidfScore(leafnode))  # 指标一：tfidf
            scoreDic[leafnode].append(self.cosScore(leafnode))  # 指标二：余弦相似度
            scoreDic[leafnode].append(self.overlapScore(leafnode))  # 指标三：摘要和题目的重叠度
            # 将三个指标先进行归一化处理，随后乘以它们各自的权重系数
        tfidf = []
        maxCosine = []
        overlap = []

        for leafnode in scoreDic:
            tfidf.append(scoreDic[leafnode][0])
            maxCosine.append(scoreDic[leafnode][1])
            overlap.append(scoreDic[leafnode][2])
            tfidf_max,tfidf_min = (0,0)
            cosine_max,cosine_min = (0,0)
            overlap_max,overlap_min = (0,0)
        if len(tfidf) > 1:
            tfidf_max = max(tfidf)
            tfidf_min = min(tfidf)
        if len(maxCosine) > 1:
            cosine_max = max(maxCosine)
            cosine_min = min(maxCosine)
        if len(overlap) > 1:
            overlap_max = max(overlap)
            overlap_min = min(overlap)
        for leafnode in scoreDic:
            # 存在 /0的可能
            scoreDic[leafnode][0] = (scoreDic[leafnode][0] - tfidf_min) / (tfidf_max - tfidf_min) if tfidf_max != tfidf_min else 0
            scoreDic[leafnode][1] = (scoreDic[leafnode][1] - cosine_min) / (cosine_max - cosine_min)if cosine_max != cosine_min else 0
            scoreDic[leafnode][2] = (scoreDic[leafnode][2] - overlap_min) / (overlap_max - overlap_min)if overlap_max != overlap_min else 0
            final_score = 0.5 * scoreDic[leafnode][0] + 0.3 * scoreDic[leafnode][1] + 0.2 * scoreDic[leafnode][2]
            leafnode.setScore(final_score)

    # 对leftnode计算tfidf得分
    def tfidfScore(self, leafnode):
        wordList = utils.seg_depart(leafnode.getTextContent())
        score = 0.0
        for word in set(wordList):
            if word in self.tfidf["main_text"]:
                score += self.tfidf["main_text"][word] * math.sqrt(wordList.count(word))
        return score

    def cosScore(self, leafnode):
        abstractLeafNodes = self.abstractNode.getleafnodes()
        #leafnodes = leafnode.getleafnodes()
        maxCosine = 0.0
        for abstractLeafNode in abstractLeafNodes:
            seg_list1 = utils.seg_depart(leafnode.getTextContent(), delete_stopwords=True)
            seg_list2 = utils.seg_depart(abstractLeafNode.getTextContent(), delete_stopwords=True)
            list_word1 = (",".join(seg_list1)).split(",")
            list_word2 = (",".join(seg_list2)).split(",")

            # 列出所有的词，取并集
            key_word = list(set(list_word1).union(list_word2))
            # 给定形状和类型的用0填充的矩阵存储向量
            word_vector1 = np.zeros(len(key_word))
            word_vector2 = np.zeros(len(key_word))
            # 计算词频
            # 依次确定向量的每个位置的值
            # for i in range(len(key_word)):
            #     # 遍历key_word中每个词在句子中的出现次数
            #     for j in range(len(seg_list1)):
            #         if key_word[i] == seg_list1[j]:
            #             word_vector1[i] += 1
            #     for k in range(len(seg_list2)):
            #         if key_word[i] == seg_list2[k]:
            #             word_vector2[i] += 1
            for i in range(len(seg_list1)):
                word_vector1[key_word.index(seg_list1[i])] += 1
            for i in range(len(seg_list2)):
                word_vector2[key_word.index(seg_list2[i])] += 1

            # 余弦相似度计算
            dist1 = 0.0
            # dist1 = float(np.dot(word_vector1, word_vector2) / (np.linalg.norm(word_vector1) * np.linalg.norm(word_vector2)))
            if np.linalg.norm(word_vector1) * np.linalg.norm(word_vector2) != 0:
                dist1 = float(np.dot(word_vector1, word_vector2) / (np.linalg.norm(word_vector1) * np.linalg.norm(word_vector2)))

            if dist1 > maxCosine:
                maxCosine = dist1
        return maxCosine

    def overlapScore(self, leafnode):
        overlap = 0.0
        title_word_list = utils.seg_depart(self.title, delete_stopwords=True)
        # 与论文题目的词语重叠度
        leafnode_word_list = utils.seg_depart(leafnode.getTextContent(), delete_stopwords=True)
        overlap_word_list = list(set(title_word_list).intersection(set(leafnode_word_list)))
        overlap += float(len(overlap_word_list)) / float(len(leafnode_word_list)) if len(
            leafnode_word_list) != 0 else 0.0
        # 与一级至三级章节标题的词语重叠度
        for ancestor in leafnode.getAncestors():
            if ancestor.getOutLvl() in ['0', '1', '2']:
                ancestor_word_list = utils.seg_depart(ancestor.getTextContent(), delete_stopwords=True)
                leafnode_word_list = utils.seg_depart(leafnode.getTextContent(), delete_stopwords=True)
                overlap_word_list = list(set(ancestor_word_list).intersection(set(leafnode_word_list)))
                overlap += float(len(overlap_word_list)) / float(len(leafnode_word_list)) if len(
                    leafnode_word_list) != 0 else 0.0
        return overlap


def table_image_scoring(self, docxTree, classifyResult):
    tfidf = {}
    for script_path in utils.get_file_paths(utils.getScriptPath()):
        script_name = os.path.basename(script_path).replace(".json", "")
        if script_name == classifyResult:
            tfidf = utils.json_to_dict(script_path)["tfidf"]

    avgScore = docxTree.getAvgScore()

    # 指标1: 全文句子的权重平均值的2倍
    for child in docxTree.getChildren():
        if check(child, ["摘要"]):
            pass
        else:
            for treenode in child.getLowerTreeNodes():
                children = treenode.getChildren()
                for i in range(len(children)):
                    if children[i].getType() in [3, 4]:
                        children[i].setScore(children[i].getScore() + avgScore * 2)

    # 指标2: 表格中的tfidf的词语的tfidf权重之和
    for child in docxTree.getChildren():
        if check(child, ["摘要"]):
            pass
        else:
            for treenode in child.getLowerTreeNodes():
                children = treenode.getChildren()
                for i in range(len(children)):
                    if children[i].getType() == 3:  # 表格
                        score = 0.0
                        table_data = children[i].getTableData()  # 表格数据
                        for row_data in table_data:
                            for cell_data in row_data:
                                if cell_data != "":
                                    seg_list = utils.seg_depart(cell_data, delete_stopwords=True)
                                    for word in set(seg_list):
                                        if word in tfidf["main_text"]:
                                            score += tfidf["main_text"][word] * math.sqrt(seg_list.count(word))
                        children[i].setScore(children[i].getScore() + score)

    # 指标3: 惩罚因子
    for child in docxTree.getChildren():
        if check(child, ["摘要"]):
            pass
        else:
            for treenode in child.getLowerTreeNodes():
                children = treenode.getChildren()
                num = 0  # 图表的数量
                for i in range(len(children)):
                    if children[i].getType() in [3, 4]:
                        num += 1
                if num > 1:
                    for i in range(len(children)):
                        if children[i].getType() in [3, 4]:
                            children[i].setScore(children[i].getScore() / num)


def sec_scoring(self, docxTree, classifyResult):
    # 确定剧本
    tfidf = {}
    for script_path in utils.get_file_paths(utils.getScriptPath()):
        script_name = os.path.basename(script_path).replace(".json", "")
        if script_name == classifyResult:
            tfidf = utils.json_to_dict(script_path)["tfidf"]

    # 1) 词语tfidf权重之和
    for child in docxTree.getChildren():
        if check(child, ["摘要"]):
            pass
        else:
            self.sec_scoring_text(child, tfidf)

    # 2）子节点权重之和
    for child in docxTree.getChildren():
        if check(child, ["摘要"]):
            pass
        else:
            self.sec_scoring_child(child)


def sec_scoring_text(self, node, tfidf):
    score = 0.0

    if node.getOutLvl() != "":
        seg_list = utils.seg_depart(node.getTextContent(), delete_stopwords=True)
        if node.getOutLvl() in ['0', '1', '2']:
            for word in seg_list:
                heading = 'heading' + str(int(node.getOutLvl()) + 1)
                if word in tfidf[heading]:
                    score += tfidf[heading][word] * seg_list.count(word)
        else:
            for word in seg_list:
                if word in tfidf['main_text']:
                    score += tfidf['main_text'][word] * seg_list.count(word)

        for child in node.getChildren():
            self.sec_scoring_text(child, tfidf)

        node.setScore(node.getScore() + score)


def sec_scoring_child(self, node):
    score = 0.0

    if node.getType() == 0:  # 章节节点  子节点有段落节点、表格节点和图像节点
        for child in node.getChildren():
            if child.getType() in [0, 1]:
                self.sec_scoring_child(child)
                score += child.getScore()
            elif child.getType() in [3, 4]:
                score += child.getScore()
        node.setScore(node.getScore() + score)
    elif node.getType() == 1:
        for child in node.getChildren():
            score += child.getScore()
        node.setScore(node.getScore() + score)
