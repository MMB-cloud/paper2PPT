import json
import os
from common.Utils import Utils

utils = Utils()


class DocxTree:
    def __init__(self, file_path, output_dir_path):
        self.__children = []
        self.__sec_children = []
        self.__leafnodes = []

        self.__file_path = file_path
        self.__title = os.path.basename(file_path).replace(".docx", "")
        self.__output_dir_path = output_dir_path
        self.__avg_score = 0.0

    # 添加子节点(一级标题
    def setChildren(self, nodeList):
        indexs = []
        for node in nodeList:
            if node.getOutLvl() == '0':
                indexs.append(nodeList.index(node))
        for i in range(len(indexs)):
            if i == len(indexs) - 1:
                nodeList[indexs[i]].setChildren(nodeList[indexs[i] + 1:])
            else:
                nodeList[indexs[i]].setChildren(nodeList[indexs[i] + 1: indexs[i + 1]])  # 19-22
            self.__children.append(nodeList[indexs[i]])

        # 删除中文摘要之前的一级章节内容
        for child in self.__children:
            if '摘要' in child.getTextContent().replace(" ", ""):
                index = self.__children.index(child)
                if index != 0:
                    self.__children = self.__children[index:]
                    break

        # 删除参考文献及以后的章节内容
        for child in self.__children:
            if '参考文献' in child.getTextContent().replace(" ", ""):
                self.__children = self.__children[: self.__children.index(child)]
                break

        # 删除Abstract
        index = -1
        for child in self.__children:
            if 'Abstract' in child.getTextContent().replace(" ", "") or 'abstract' in child.getTextContent().replace(
                    " ", ""):
                index = self.__children.index(child)
                break
        list1 = self.__children[: index]
        list2 = self.__children[index + 1:]
        self.__children = list1 + list2

        # 删除目录
        index = -1
        for child in self.__children:
            if '目录' in child.getTextContent().replace(" ", ""):
                index = self.__children.index(child)
                break
        list1 = self.__children[: index]
        list2 = self.__children[index + 1:]
        self.__children = list1 + list2

    def getChildren(self):
        return self.__children

    def getTreeDic(self):
        if self.__output_dir_path == "":
            return
        treeDic = {}
        treeDic["title"] = self.__title
        treeDic["children"] = []
        for child in self.__children:
            treeDic["children"].append(child.getTreeDic())
        utils.dict_to_json(treeDic, self.__output_dir_path + "\\treeDic1.json")

    def getCompressedTreeDic(self):
        compressedTreeDic = {"title": self.__title, "children": []}
        for child in self.__children:
            if len(child.getCompressedTreeDic()) != 0:
                compressedTreeDic["children"].append(child.getCompressedTreeDic())
        utils.dict_to_json(compressedTreeDic, self.__output_dir_path + "\compressedTreeDic.json")

    def getleafnodes(self):
        if len(self.__leafnodes) != 0:
            return self.__leafnodes
        else:
            for child in self.__children:
                self.__leafnodes.extend(child.getleafnodes())
            return self.__leafnodes

    # 逆向得到nodeList列表，用于生成<w:body>的xml内容
    def getNodeList(self):
        nodeList = []
        for child in self.__children:
            nodeList.extend(child.getNodeList())
        return nodeList

    def getSelectedNodeList(self):
        selectedNodeList = []
        for child in self.__children:
            if child.getSelected():
                selectedNodeList.extend(child.getSelectedNodeList())
        return selectedNodeList

    def getTitle(self):
        return self.__title

    def getOutputDirPath(self):
        return self.__output_dir_path

    def getFilePath(self):
        return self.__file_path

    """计算全文句子的tfidf权重平均值"""

    def getAvgScore(self):
        if self.__avg_score != 0.0:
            return self.__avg_score
        leafnodeNum = 0
        score = 0.0
        for child in self.__children:
            if '摘要' in child.getTextContent().replace(" ", ""):
                pass
            else:
                for leafnode in child.getleafnodes():
                    score += leafnode.getScore()
                    leafnodeNum += 1
        self.__avg_score = float(score) / float(leafnodeNum)
        return self.__avg_score

    @staticmethod
    def parseJsonToClz(jsonStr, DocTree):
        parseData = json.loads(jsonStr.strip('\t\r\n'))
        result = DocTree("", "")
        result.__dict__ = parseData
        return result

    @staticmethod
    def ParseObjToJson(yourObj):
        return yourObj.__dict__.__str__().replace("\'", "\"")
