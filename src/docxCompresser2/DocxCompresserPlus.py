import os
import re
import json
from collections import namedtuple

from src.docxCompresser2.ScoringModel import ScoringModel
from src.docxCompresser2.ILPModel import ILPModel
from src.docxCompresser2.DocxGenerator import DocxGenerator
from src.docxParser import Node
from src.docxParser import DocxTree
from common.Utils import Utils

utils = Utils()
'''
    第一遍压缩将段落匹配上part
    第二遍开始打分
'''


# 输入节点和特征词列表进行匹配，返回匹配结果
def check(node, strlist):
    matched = False
    if (node == None or strlist == None):
        return False
    if isinstance(node, Node.Node) == False:
        return False
    for str in strlist:
        if node.getType() != 1:
            if str in node.getTextContent().replace(" ", ""):
                matched = True
                break
    return matched


def isHeadNode(node):
    matched = False
    if node.getType() == 0 and node.getOutLvl() != "":
        matched = True
    return matched


def isTextMatch(node, strlist):
    matched = False
    if node.getType() == 1:
        for text_child in node.getChildren():
            if check(text_child, strlist):
                matched = True
    return matched


def isNode(node):
    if isinstance(node, Node.Node):
        return True
    else:
        return False


def isHeadContentMatch(node, heading_kw):
    for kw in heading_kw:
        content = node.getTextContent().replace(" ", "")
        if kw in content or kw == content:
            return True
    return False


'''
    递归将题目中有kw的节点标记为true
'''


def markSelected(node, heading_kw, partName):
    # 没有children节点说明递归到叶子节点（段落、图片……），返回
    if node.getChildren() is None:
        return False
    # 当前节点匹配上或者子节点有匹配上则匹配然后return true
    if isHeadNode(node) and isHeadContentMatch(node, heading_kw):
        node.setSelected(True)
        node.setPartName(partName)
        return True
    for c in node.getChildren():
        if markSelected(c, heading_kw, partName):
            node.setSelected(True)
            node.setPartName(partName)
            return True
    return False


def matchScript(classifyResult):
    for script in utils.get_file_paths(utils.getScriptPath()):
        script_name = os.path.basename(script).replace('v2.json', '')
        if classifyResult == script_name:
            script_json = utils.json_to_dict(script)
            return script_json
    return "There is no script matches: " + classifyResult
class DocxCompresserPlus:
    classifyResult = None
    classifyScript = {}
    scoringModel = ScoringModel()
    ilpModel = ILPModel()
    maxLength = 0
    def __init__(self) -> None:
        pass

    def set_result(self, result):
        self.classifyResult = result
        self.classifyScript = matchScript(result)
        self.scoringModel.setScirpt(result)

    # 存在问题：一级标题中可能有不同part的二/三级节点
    # TODO planA 按二级标题往part中放？ 体感上需要，因为不同part可能在同一个一级或二级标题下，会造成后边的把前面覆盖掉
    # TODO planB part作为一个list，所有可能的部分都放里边，然后到script中制定每一part的选取规则
    def firstCompress(self, docTree, outputPath):
        # script = self.matchScript(classifyResult)
        result = {}
        classifiedByPartDic = {}
        classifiedByPartDic["title"] = docTree.getTitle()
        parts = self.classifyScript["parts"]
        self.scoringModel.title = docTree.getTitle()
        # 逐part选取节点
        # 将选取的节点标记为true然后，只要子节点有被选取的节点，父节点也标记为true
        for part in parts:
            part_name = part["name"]
            heading_kw = part["heading_keywords"]
            position = part["position"]
            result.setdefault(part_name, [])
            classifiedByPartDic.setdefault(part_name, [])
            # 标题中包含headingkw的关键词则认为匹配上
            for i in position:
                # 回溯去搞
                if i < len(docTree.getChildren()) - 1:
                    markSelected(docTree.getChildren()[i], heading_kw, part_name)
                    if docTree.getChildren()[i].getSelected():
                        # 选取的节点归类放到对应的part
                        result[part_name].append(docTree.getChildren()[i].getTreeDic())
                        classifiedByPartDic[part_name].append(docTree.getChildren()[i])
        utils.dict_to_json(result, outputPath + "/ClassByPart.json")
        return classifiedByPartDic

    # docTree的“part”和key对应时代表选上
    # TODO 对part也加一个keylist 和script里的tfidf结合起来
    # TODO 7.17是不是可以在这里就以二级标题(type = 0, outLv = 1)作为part中的最小单元？ 明天试一下 DONE
    # TODO 7.18 检查为什么有的图片节点未选中 DONE
    # TODO 7.22 尝试解析公式,似乎可以直接将xml放到PPT，可以解析
    # TODO ClassBypart2解析为PPTtree
    def score(self, classifiedByPartDic, outputPath):
        result = {}
        scoredDic = {}
        scoredDic["title"] = classifiedByPartDic["title"]
        for partName, treeNodes in classifiedByPartDic.items():
            result.setdefault(partName, [])
            scoredDic.setdefault(partName, [])
            if partName == "title":
                continue
            for treeNode in treeNodes:  # 一级标题, type = 0, outLv = '0'
                if partName == "摘要":
                    self.scoringModel.abstractNode = treeNode
                    continue
                if partName in treeNode.getPartName():
                    for outLv2Node in treeNode.getChildren():
                        if partName in outLv2Node.getPartName():
                            # self.scoreByModel(treeNode)
                            # result[partName].append(treeNode.getTreeDic())
                            self.scoreByModel(outLv2Node)
                            result[partName].append(outLv2Node.getTreeDic())
                            scoredDic[partName].append(outLv2Node)
        utils.dict_to_json(result, outputPath + "/ClassByPart1.json")
        return scoredDic

    # TODO 7.14 把线性规划放到这里搞,以一级节点作为入参，dfs深搜 DONE
    def choose(self, scoredDic, outputPath):
        result = {}
        chosenDic = {}
        chosenDic["title"] = scoredDic["title"]
        for partName, treeNodes in scoredDic.items():
            result.setdefault(partName, [])
            chosenDic.setdefault(partName, [])
            if partName == "title":
                continue
            for treeNode in treeNodes:
                if partName == "摘要":
                    continue
                if partName in treeNode.getPartName():
                    max_length = 0.0
                    for part in self.classifyScript["parts"]:
                        if partName == part["name"]:
                            max_length = treeNode.getLength() * part["compress_ratio"]
                            break
                    self.markChosen(treeNode, max_length)
                    result[partName].append(treeNode.getTreeDic())
                    chosenDic[partName].append(treeNode)
        utils.dict_to_json(result, outputPath + "/ClassByPart2.json")
        return chosenDic

    # 二级节点入参，dfs求解
    # TODO 需要maxlenth，从当前的一级节点中获取total_length,然后*compress_ratio,最好每个part一个ratio DONE
    def markChosen(self, node, max_length):
        # 图片和公式节点保留
        if node.getType() == 3 or node.getType() == 4 or node.getType() == 5:
            print(1)
            node.setChosen(True)
            return

        # 遍历到叶节点，返回
        if node.getType() != 0:
            return
        # 找到标题节点的最末端，作为ILP求解的入参
        isEnd = True
        for n in node.getChildren():
            self.markChosen(n, max_length)
            # 可能存在标题节点+正文+次级标题，只有节点全是空outlvl才认为找到标题节点末端
            if n.getOutLvl() != '':
                isEnd = False
        if isEnd:
            self.ilpModel.build_and_solve(node, max_length, presentation_type="text_based")

    def scoreByModel(self, node):
        self.scoringModel.sentScoringByNodes(node)

    def compressDocx(self, docxTree):
        # 重要性评分
        scoringModel = ScoringModel()
        scoringModel.sent_scoring(docxTree, self.classifyResult)
        scoringModel.table_image_scoring(docxTree, self.classifyResult)
        scoringModel.sec_scoring(docxTree, self.classifyResult)
        docxTree.getTreeDic()

        # 内容选取
        for child in docxTree.getChildren():
            if check(child, ["摘要"]):
                pass
            else:
                self.compressChapter(node=child, classifyResult=self.classifyResult)

        for child in docxTree.getChildren():
            self.select_sec(child)

        docxTree.getTreeDic()
        docxTree.getCompressedTreeDic()

        # 压缩后内容生成
        docxGenerator = DocxGenerator()
        docxGenerator.generateDocx(docxTree)

    """一级章节内容压缩"""
    def compressChapter(self, node, classifyResult):
        # 读取剧本中的getdocparts
        getdocparts = {}
        for script_path in utils.get_file_paths(utils.getScriptPath()):
            script_name = os.path.basename(script_path).replace(".json", "")
            if script_name == classifyResult:
                getdocparts = utils.json_to_dict(script_path)["getdocparts"]

        # 将node与剧本中的章节进行匹配，如果匹配到了就读取该章节的相应规则参数
        for docpart in getdocparts:
            if check(node, docpart["name"]):  # 匹配到了，读取规则
                # 先读取necessary字段
                if docpart["necessary"]:
                    # 读取compress_mode字段，获取内容压缩模式
                    if docpart["compress_mode"] == "ILP_Model":
                        # 获取page_num字段
                        page_num = docpart["page_num"]
                        # 获取compress_ratio字段
                        compress_ratio = docpart["compress_ratio"]
                        # 获取presentation_type字段
                        presentation_type = docpart["presentation_type"]
                        # 获取children字段
                        children_docparts = docpart["children"]

                        # 根据compress_ratio确定一级章节最大文字量
                        maxLength = node.getLength() * compress_ratio
                        print(node.getTextContent() + " 最大文字量限制为: " + str(maxLength))

                        # 根据权重占比, 分配各二级章节的最大文字量
                        found = False  # 一级章节下是否有二级章节
                        for child in node.getChildren():
                            if child.getType() == 0 and child.getOutLvl() == "1":
                                found = True
                                break
                        if found:
                            totalScore = 0.0
                            for child in node.getChildren():
                                totalScore += child.getScore()
                            for child in node.getChildren():
                                if child.getType() == 0:
                                    print(child.getTextContent() + " 最大文字量限制为: " + str(
                                        maxLength * (child.getScore() / totalScore)))
                                    self.compressSubChapter(node=child,
                                                            maxLength=maxLength * (child.getScore() / totalScore),
                                                            docparts=children_docparts,
                                                            presentation_type=presentation_type)
                        else:  # 一级章节下就是正文，一般来说只有摘要章节和结论章节才会出现这样的情况，如果是摘要章节，就不作处理，如果是结论章节，那就针对一级章节构建整数线性规划模型，如果是其它章节，说明论文内容格式不规范
                            if "摘要" in node.getTextContent().replace(" ", ""):
                                pass
                            else:
                                # 构建整数线性规划模型，进行求解
                                ILP_Model = ILPModel()
                                ILP_Model.build_and_solve(node, maxLength=maxLength,
                                                          presentation_type=presentation_type, rules=[])
                        break
                    elif docpart["compress_mode"] == "sentence_cueword_matching":
                        # 获取matching_pattern字段
                        matching_pattern = docpart["matching_pattern"]
                        # 获取cuewords字段
                        cuewords = docpart["cuewords"]
                        # 直接找到其底层章节节点，进行句子匹配
                        for treenode in node.getLowerTreeNodes():
                            leafnodes = treenode.getleafnodes()
                            for leafnode in leafnodes:
                                # 进行matching_pattern正则匹配
                                matched = False
                                for pattern in matching_pattern:
                                    if len(re.findall(pattern, leafnode.getTextContent(), flags=0)) != 0:
                                        leafnode.setSelected(True)
                                        matched = True
                                        break
                                if matched:
                                    continue
                                else:
                                    # 进行cuewords字段匹配
                                    for cueword in cuewords:
                                        if cueword in leafnode.getTextContent():
                                            leafnode.setSelected(True)
                                            break
                else:
                    break
            else:  # 没有匹配到
                if getdocparts.index(docpart) == len(getdocparts) - 1:  # 直到最后一个也没有匹配到
                    # 执行默认路径  默认路径下使用整数线性规划模型进行内容选取，且模型选定为图表型
                    default_compress_ratio = 0.25  # 默认压缩比例为0.25
                    default_presentation_type = "chart_oriented"  # 默认生成图表型幻灯片

                    # 根据default_compress_ratio确定一级章节最大文字量
                    maxLength = node.getLength() * default_compress_ratio
                    print(node.getTextContent() + " 最大文字量约束为: " + str(maxLength))

                    # 根据权重占比，分配各二级章节的最大文字量
                    found = False  # 一级章节下是否有二级章节
                    for child in node.getChildren():
                        if child.getType() == 0 and child.getOutLvl() == "1":
                            found = True
                            break
                    if found:
                        totalScore = 0.0
                        for child in node.getChildren():
                            totalScore += child.getScore()
                        for child in node.getChildren():
                            if child.getType() == 0:
                                print(child.getTextContent() + " 最大文字量约束为: " + str(
                                    maxLength * (child.getScore() / totalScore)))
                                self.compressSubChapter(node=child,
                                                        maxLength=maxLength * (child.getScore() / totalScore),
                                                        docparts=[], presentation_type="chart_oriented")
                    else:  # 一级章节下就是正文，一般来说只有摘要章节和结论章节才会出现这样的情况, 如果是摘要章节, 如果是结论章节, 那就针对一级章节构建整数线性规划模型, 如果是其它章节, 说明论文内容格式不规范
                        if "摘要" in node.getTextContent().replace(" ", ""):
                            pass
                        else:
                            # 构建整数线性规划模型，进行求解
                            ILP_Model = ILPModel()
                            ILP_Model.build_and_solve(node, maxLength=maxLength, presentation_type="text_based",
                                                      rules=[])
                else:  # 继续进行匹配
                    continue


    """二、三级章节内容压缩"""
    def compressSubChapter(self, node, maxLength, docparts=[], presentation_type="chart_oriented"):
        # 判断自身是否是最底层章节或三级章节    整数线性规划模型是围绕二、三级章节构造的
        if node.getOutLvl() == "1":  # 二级章节
            found = False  # 是否存在三级章节
            for child in node.getChildren():
                if child.getType() == 0 and child.getOutLvl() == "2":  # 三级章节
                    found = True
                    break
            if found:  # 存在三级章节，就进行文字量再分配, 再进入一层
                totalScore = 0.0
                for child in node.getChildren():
                    totalScore += child.getScore()
                for child in node.getChildren():
                    if child.getType() == 0:
                        print(child.getTextContent() + " 最大文字量约束为: " + str(
                            maxLength * (child.getScore() / totalScore)))
                        self.compressSubChapter(node=child, maxLength=maxLength * (child.getScore() / totalScore),
                                                docparts=docparts)
            else:  # 二级章节即为最底层章节，构建整数线性规划模型，并进行求解
                ILP_Model = ILPModel()
                ILP_Model.build_and_solve(node=node, maxLength=maxLength, presentation_type=presentation_type,
                                          rules=docparts)
        elif node.getOutLvl() == "2":  # 三级章节
            # 构建整数线性规划模型，并进行求解
            ILP_Model = ILPModel()
            ILP_Model.build_and_solve(node=node, maxLength=maxLength, presentation_type=presentation_type,
                                      rules=docparts)

    def transferToSlideJson(self,classifiedByPartDic):
        pptDic = {}
        for partName, node in classifiedByPartDic:
            if node.getPartName() == partName:
                pptDic[partName] = []


def select_sec(self, node):
    if node.getType() in [0, 1]:
        for child in node.getChildren():
            self.select_sec(child)
            if child.getSelected():
                node.setSelected(True)

    '''
            第一遍压缩：
                标题匹配+2
                内容匹配+1
                匹配到两分以上则该节点对应至剧本中对应部分
                input: 
                    docTree:文档的树结构
                    classifyResult:预测文档类别
                    outputPath:输出json路径，正式版应该没这个
            逻辑：
                先检索一级标题，匹配headingKey记录位置，匹配项则看是否有子章节，有子章节则继续向下匹配直到正文章节后开始匹配内容项，没有说明后边直接跟正文直接匹配内容项。
                一级标题没有selected的再过一遍二级标题。

                    向下匹配到末级标题，即正文对应的父节点作为保留的最小单位，selected标为True
                        4研究设计--4.1研究假设--4.1.1收费节点
                        4研究设计--4.2模型构建

        '''

    '''
    标题匹配+2
    段落内容匹配+1
    有图表+1
        先遍历二级标题
            标题匹配后遍历子节点，只匹配段落节点.
        再遍历三级标题
            标题匹配后遍历子节点加分
    '''

    '''
            # 读取剧本中各节点在二级标题中的对应部分
            selectNodesDic = {}
            for docpart in docparts:
                if not docpart["children"]:
                    for node in docTree.getChildren():
                        # 获取二级标题列表
                        sec_nodelist = node.gettreenodes(1)
                        for sec_node in sec_nodelist:
                            if check(sec_node, docpart["key_words"]):
                               #position = docpart["position"]
                                selectNodesDic[docpart["name"]+sec_node.getTextContent()] = sec_node.getTreeDic()
                else: #一级标题符合，整个保留（例如文献综述和实证研究部分内容）
                    #for child in docpart["children"]:
                        for node in docTree.getChildren():
                            if check(node,docpart["key_words"]):
                                selectNodesDic[docpart["name"]+node.getTextContent()] = node.getTreeDic()

            utils.dict_to_json(selectNodesDic, outputPath+"/firstCompress.json")

            return selectNodesDic
    '''
    """论文内容压缩"""
