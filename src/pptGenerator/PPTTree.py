from common.Utils import Utils
from src.pptGenerator.PPTNode import PPTNode
from openai import OpenAI
import re
utils = Utils()

"""幻灯片树"""


class PPTTree:
    title = ''
    index = []
    pptDic = {}
    #api_key = 'sk-6274a5c776bd4840a772af31dffc3afb' #ds
    api_key = '819d1190-94d8-413f-a7f8-b6a5522e79f2' #ds
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
                pptNode_with_llm = self.doubao(pptNode)
                #self.pptDic["children"].append(pptNode)
                self.pptDic["children"].append(pptNode_with_llm)
                #result["children"].append(pptNode.getDic())
                result["children"].append(pptNode_with_llm.getDic())

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

    def deepseek(self, pptNode):
        children = pptNode.getChildren()
        sent_lst = [child['content'] for child in children if child['type'] == 2]
        pre_words = f"这是从一篇论文中{pptNode.getContent() }部分摘取的关键句子，' \
                    '将下面列表中内容替换为更适合幻灯片展示的语句，' \
                    '并进行概括总结，使其更有逻辑:"
        content = "\n".join(sent_lst)
        client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful research assistant"},
                {"role": "user", "content": f"{pre_words + content}"},
            ],
            stream=False
        )

        print(response)

    def doubao(self,pptNode):
        children = pptNode.getChildren()
        sent_lst = [child['content'] for child in children if child['type'] == 2]
        pre_words = f"这是从一篇论文中{pptNode.getContent()}部分摘取的关键句子，' \
                            '将下面内容替换为更适合幻灯片展示的简练语句，如果是综述部分则总条数小于等于5，字数小于等于200' \
                            '并进行分点概括总结，使其条理清晰，更有逻辑："
        content = "\n".join(sent_lst)
        aft_words = "\n" + "其他要求：字体不需要加粗，所有冒号用中文全角符号。输出结果为list，输出模板为：1.xx:- xxxx - yyyy 2.xx: - xxxx"
        client = OpenAI(api_key=self.api_key, base_url="https://ark.cn-beijing.volces.com/api/v3")
        response = client.chat.completions.create(
            model="ep-20250214205811-6bwfc",
            messages=[
                {"role": "system", "content": "你是用于辅助ppt制作的助手，语言风格简练"},
                {"role": "user", "content": f"{pre_words + content + aft_words}"},
            ],
            #stream=False
        )
        response_content = response.choices[0].message.content
        # 按行切割
        response_content_list = response_content.split('\n')
        # 返回节点
        n_pptnode = PPTNode(pptNode.getContent(), [])
        if len(response_content_list) > 0 and response_content_list[0].endswith("："):
            # 分割内容为不同的部分
            sections = re.split(r'\n(?=\d+\.\s*[\u4e00-\u9fa5]+：)', response_content.strip())

            # 初始化一个空列表来存储字典
            data_list = []
            #如果切割后的list只有一个，未按格式

            # 遍历每个部分
            for section in sections:
                if section.strip():
                    # 提取标题和内容
                    title_part, *content_lines = section.split('\n')
                    title = title_part.split('：')[0].strip()  # 提取标题
                    # 清理内容并转换为列表
                    content = [
                        line.strip().replace('    - ', '', 1)  # 替换首个子项目符号
                        for line in content_lines
                        if line.strip()
                    ]
                    if len(content) == 0 and len(title_part.split('：')) > 1:
                        content = [title_part.split('：')[1]]
                    data_list.append({"title": title, "content": content})
                    # 创建字典并添加到列表
                    n_pptnode.addNode(2, {'title': title, 'content': content})
        else:
            n_pptnode.addNode(2,{'title': pptNode.getContent(), 'content': response_content_list})
        # 添加图片节点
        for child in pptNode.getChildren():
            if child['type'] == 4:
                n_pptnode.addNode(4,child['content'])
            elif child['type'] == 3:
                n_pptnode.addNode(3,child['content'])

        return n_pptnode
        #print(response.choices[0].message.content)



