from common.Utils import Utils

utils = Utils()

"""幻灯片树"""
class PPTTree:
    """
    :param file_path: pptTree.json的绝对路径
    """

    pptDic = {}

    def __init__(self, file_path) -> None:
        self.__file_path = file_path

    def buildPPTDic(self,classifiedByPartDic):
        for partName, nodes in classifiedByPartDic.items():
            self.pptDic[partName] = []
            for node in nodes:
                if partName == node.getPartName():
                    for leafnode in node.getleafnodes():
                        if leafnode.getChosen:
                            self.pptDic[partName].append(leafnode.getTextContent())
        var = self.pptDic

    # 封面页
    def getTitleData(self):
        pptTreeDic = utils.json_to_dict(self.__file_path)
        data = {
            "type": 0,
            "content": pptTreeDic["title"]
        }
        return data

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
            data["content"].append("0" + str(index+1))
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
