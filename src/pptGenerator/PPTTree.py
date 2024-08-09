from common.Utils import Utils
from src.pptGenerator.PPTNode import PPTNode
utils = Utils()

"""幻灯片树"""


class PPTTree:
    title = ''
    index = []
    pptDic = {}

    """
    :param file_path: pptTree.json的绝对路径
    """

    def __init__(self, file_path) -> None:
        self.__file_path = file_path

    def buildPPTDic(self, classifiedByPartDic,outputPath):
        # 填充标题
        result = {}
        self.title = classifiedByPartDic['title']
        result["title"] = classifiedByPartDic["title"]
        # 填充内容
        # TODO 7.22内容节点是否需要再做个类 DONE
        self.pptDic["children"] = []
        result["children"] = []
        for partName, nodes in classifiedByPartDic.items():
            if partName == "title":
                continue
            pptNode = PPTNode(partName, [])
            for node in nodes:
                self.dfs(pptNode, node)
                #  不为空添加到结果集
            if len(pptNode.getChildren()) > 0:
                self.pptDic["children"].append(pptNode)
                result["children"].append(pptNode.getDic())
        utils.dict_to_json(result, outputPath + "/pptDic.json")
        var = self.pptDic

    def dfs(self, pptNode, node):
        if node.getChosen():
            if node.getType() == 2:
                pptNode.addNode(node.getType(), node.getTextContent())
            elif node.getType() == 3:
                pptNode.addNode(node.getType(), node.getTableData())
            elif node.getType() == 4:
                pptNode.addNode(node.getType(), node.getrid())
            elif node.getType() == 5:
                pptNode.addNode(node.getType(), node.getXmlContent())
            return
        if node.getChildren() is not None:
            for c in node.getChildren():
                self.dfs(pptNode, c)

    # 封面页
    def getTitleData(self):
        pptTreeDic = utils.json_to_dict(self.__file_path)
        data = {
            "type": 0,
            "content": pptTreeDic["title"]
        }
        return data

    def getIndexPage(self):
        for pptNode in self.pptDic["children"]:
            self.index.append(pptNode.getContent())
        return self.index

    # 目录页
    def getDirectoryData(self):
        pptTreeDic = utils.json_to_dict(self.__file_path)
        data = {
            "type": 1,
            "content": []
        }
        for child in pptTreeDic["children"]:
            data["content"].append(child["content"])
        return data

    # 章节过度页和纯文字内容页
    def getTextDatas(self):
        pptTreeDic = utils.json_to_dict(self.__file_path)
        dataList = []
        for child in pptTreeDic["children"]:
            # 章节过度页
            data = {
                "type": 2,
                "content": []
            }
            index = pptTreeDic["children"].index(child)
            data["content"].append("0" + str(index + 1))
            data["content"].append(child["content"])
            dataList.append(data)

            # data = {
            #     "type": 3,  # type=3 表示数据类型为纯文本,
            #     "content": {
            #         "heading": "研究背景与研究问题",
            #         "children": [
            #             {
            #                 "keyword": "研究背景",
            #                 "sentences": [
            #                     "作为实现资金融通的中介机构，商业银行的经营状况与盈利水平对国家的资本市场有着重要影响。",
            #                     "利率是衡量国家经济的重要指标之一，其对国家经济实现均衡发展以及资源资金的合理配置具有重要导向意义。",
            #                 ]
            #             },
            #             {
            #                 "keyword": "研究问题",
            #                 "sentences": [
            #                     "利率市场化进程对于商业银行盈利水平产生的影响",
            #                     "互联网金融发展对于商业银行盈利水平产生的影响",
            #                     "互联网金融发展对于利率市场化产生的影响"
            #                 ]
            #             }
            #         ]
            #     }
            # }
            # 纯文字内容页
            for text_data in child["children"]:
                data = {
                    "type": 3,
                    "content": {
                        "heading": text_data["content"],
                        "children": []
                    }
                }
                data["content"]["children"] = text_data["children"]
                dataList.append(data)
        return dataList
