import os
import re
import json

from src.docxCompresser2.ScoringModel import ScoringModel
from src.docxCompresser2.ILPModel import ILPModel
from src.docxCompresser2.DocxGenerator import DocxGenerator
from src.docxParser import Node

from common.Utils import Utils

utils = Utils()


# 输入节点和特征词列表进行匹配，返回匹配结果
def check(node, strlist):
    matched = False
    if(node == None or strlist == None):
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

'''
    递归将题目中有kw的节点标记为true
'''


def isHeadContentMatch(node, heading_kw):
    for kw in heading_kw:
        if kw in node.getTextContent():
            return True
    return False


def markSlected(node, heading_kw, partName):
    #没有children节点说明递归到叶子节点（段落、图片……），返回
    if node.getChildren() is None:
        return False
    #当前节点匹配上或者子节点有匹配上则匹配然后return true
    if isHeadNode(node) and isHeadContentMatch(node,heading_kw):
        node.setSelected(True)
        node.setPartName(partName)
        return True
    for c in node.getChildren():
        if(markSlected(c,heading_kw,partName)):
            node.setSelected(True)
            node.setPartName(partName)
            return True
    return False
class DocxCompresserPlus:
    def __init__(self) -> None:
        pass


    def originCompress(self, docTree, classifyResult, outputPath):
        # 获取剧本中“getdocparts”部分
        docparts = {}  # 用于输出json文件，会丢失原本的Class结构
        nodeList = []
        for script_path in utils.get_file_paths(utils.getScriptPath()):
            script_name = os.path.basename(script_path).replace('plus.json', '')
            if classifyResult == script_name:
                docparts = utils.json_to_dict(script_path)["getdocparts"]
                # 读取剧本中各节点在二级标题中的对应部分
                selectNodesDic = {}
                for docpart in docparts:
                    if docpart["children"]:
                        # 一级标题需要整建制保留
                        selectNodesDic[docpart["name"]] = []
                        for node in docTree.getChildren():
                            if check(node, docpart["key_words"]):
                                selectNodesDic[docpart["name"]] = node.getTreeDic()
                                nodeList.append(node)
                        # 未检索出符合的一级标题，读取二级标题与子节点对应部分
                        if not selectNodesDic[docpart["name"]]:
                            for child_docpart in docpart["children"]:
                                for node in docTree.getChildren():
                                    sec_nodelist = node.gettreenodes(1)
                                    for sec_node in sec_nodelist:
                                        if check(sec_node, child_docpart["key_words"]):
                                            # position = docpart["position"]
                                            nodeList.append(sec_node)
                                            selectNodesDic[child_docpart[
                                                               "name"] + sec_node.getTextContent()] = sec_node.getTreeDic()
                    else:
                        for node in docTree.getChildren():
                            # 获取二级标题列表
                            sec_nodelist = node.gettreenodes(1)
                            for sec_node in sec_nodelist:
                                if check(sec_node, docpart["key_words"]):
                                    # position = docpart["position"]
                                    selectNodesDic[docpart["name"] + sec_node.getTextContent()] = sec_node.getTreeDic()
                                    nodeList.append(sec_node)
                # print(selectNodesDic)
                utils.dict_to_json(selectNodesDic, outputPath + "/firstCompress.json")
                return nodeList

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

    def firstNodeSelectv1(self, docTree, classifyResult, outputPath):
        # 匹配剧本

        for script_path in utils.get_file_paths(utils.getScriptPath()):
            script_name = os.path.basename(script_path).replace('v2.json', '')
            if classifyResult == script_name:
                docparts = utils.json_to_dict(script_path)["getdocparts"]
                # 对于剧本中的一个节点
                for docpart in docparts:
                    score = 0
                    # 一级标题匹配
                    for heading1_child in docTree.getChildren():  # 1 绪论
                        # print(heading1_child.getTextContent())
                        if check(heading1_child, docpart["heading_keywords"]):  # 一级标题存在关键词match得分+2
                            socre = score + 2
                            # 如果有子节点：可能是二级标题也可能是段落节点
                            if heading1_child.getChildren != None:
                                for heading2_child in heading1_child.getChildren():
                                    # 子节点是二级标题
                                    if heading2_child.getType() == 0:  # 1.1 研究背景与研究问题
                                        if check(heading2_child, docpart["heading_keywords"]):  # 二级标题存在关键词match得分+2
                                            score = score + 2
                                            # 匹配到的二级标题有子节点，可能是三级标题或段落节点
                                            if heading2_child.getChildren != None:
                                                for heading3_child in heading2_child.getChildren():
                                                    # 三级标题
                                                    if heading3_child.getType() == 0:  # 1.1.1 研究背景
                                                        if check(heading3_child,
                                                                 docpart["heading_keywords"]):  # 三级标题匹配，得分+2,整节点保留
                                                            score = score + 2
                                                            heading3_child.setSelected(True)
                                                        # for Content_child in heading3_child:
                                                        #    print(1)
                                                        #    if check(Content_child,docpart["content_keywords"]):
                                                        #        Content_child.setSelected(True)
                                                    # 段落节点
                                                    if heading3_child.getType() == 1:  # 二级标题下已经是段落节点
                                                        for Content_child in heading3_child.getChildren():
                                                            # print(Content_child.getTextContent())
                                                            if check(Content_child, docpart["content_keywords"]):
                                                                print(
                                                                    "二级标题下是段落节点并且内容匹配:" + Content_child.getTextContent())
                                                                heading3_child.setSelected(True)
                                        # 二级标题没有match到三级标题匹配
                                        else:
                                            for heading3_child in heading2_child.getChildren():
                                                if heading3_child.getType == 0:  # 1.1.1 研究背景
                                                    if check(heading3_child, docpart["heading_keywords"]):
                                                        print("三级标题下匹配:" + heading3_child.getTextContent())
                                                        heading3_child.setSelected(True)

                                    # 段落节点，即一级标题下已经是正文了（摘要）
                                    if heading2_child.getType == 1:
                                        for Content_child in heading2_child.getChildren():
                                            if check(Content_child, docpart["content_keywords"]):
                                                heading2_child.setSelected(True)
                        # 一级标题没检索到题目匹配项，检索二级标题
                        else:
                            for heading2_child in heading1_child.getChildren():
                                # print(heading2_child.getTextContent())
                                # 二级标题匹配
                                if check(heading2_child, docpart["heading_keywords"]):  # 2.2
                                    print(heading2_child.getTextContent())
                                    score = score + 2
                                    # 遍历二级标题节点
                                    for heading3_child in heading2_child.getChildren():
                                        # print(heading3_child.getTextContent())
                                        # 如果是三级标题节点
                                        if heading3_child.getType() == 0:
                                            if check(heading3_child, docpart["heading_keywords"]):
                                                print(heading3_child.getTextContent())
                                                for textcontent_child in heading3_child.getChildren():
                                                    if isTextMatch(textcontent_child, docpart["content_keywords"]):
                                                        textcontent_child.setSelected(True)

                                        # 如果是段落节点
                                        else:
                                            if isTextMatch(heading3_child, docpart["content_keywords"]):

                                                score = score + 1
                                                if score > 1:
                                                    heading3_child.setSelected(True)
                                                    # print("段落节点Type："+str(heading3_child.getTextContent())+"OutLvl:"+str(heading3_child.getOutLvl()))
                                        # heading3中有超过两个段落被选中则整节点选择
                                        if score > 3:
                                            heading3_child.setSelected(True)
                                            # print("段落节点Type："+str(heading3_child.getType())+"OutLvl:"+str(heading3_child.getOutLvl()))
                                    # 二级标题未找到匹配项
        return docTree

    '''
    标题匹配+2
    段落内容匹配+1
    有图表+1
        先遍历二级标题
            标题匹配后遍历子节点，只匹配段落节点.
        再遍历三级标题
            标题匹配后遍历子节点加分
    '''

    def firstNodeSelect(self, docTree, classifyResult, outputPath):
        # 试一下在第一遍压缩中提句子节点
        #selectedSentLst = []
        selectedSentDic = {}
        for script_path in utils.get_file_paths(utils.getScriptPath()):
            script_name = os.path.basename(script_path).replace('v2.json', '')
            if classifyResult == script_name:
                docparts = utils.json_to_dict(script_path)["getdocparts"]
                common_keywords = list(utils.json_to_dict(script_path)["common_keywords"])
                before_chart_cuewords = list(utils.json_to_dict(script_path)["before_chart_cuewords"])
                after_chart_cuewords = list(utils.json_to_dict(script_path)["after_chart_cuewords"])
                # 对于剧本中的一个节点
                for docpart in docparts:
                    selectedSentLst = []
                    selectMode = docpart["selectMode"]
                    # 选取段落第一句的话
                    if selectMode == 1:
                        for heading1_child in docTree.getChildren():
                            heading2_nodeList = heading1_child.getTreenodes(2)
                            for heading2_node in heading2_nodeList:
                                if check(heading2_node,docpart["heading_keywords"]) or check(heading2_node.getParent(),docpart["heading_keywords"]):

                                    selectedSentLst.extend(heading2_node.getFirstSentInNode())
                    #关键词匹配
                    if selectMode == 2:
                        content_keywords = list(docpart["content_keywords"]) + common_keywords
                        for heading1_child in docTree.getChildren():
                            # 遍历二级标题
                            heading2_nodeList = heading1_child.getTreenodes(1)
                            for heading2_node in heading2_nodeList:
                                score = 0
                                if check(heading2_node, docpart["heading_keywords"]) or check(heading2_node.getParent(),
                                                                                              docpart["heading_keywords"]):  # 标题匹配+2
                                    score = score + 2
                                    # 寻找二级标题下段落节点
                                    pos = 0
                                    para_nodeLsts = heading2_node.getChildren()
                                    for para_nodeLst in para_nodeLsts:
                                        # 段落节点
                                        if para_nodeLst.getSelected() == False and para_nodeLst.getType() == 1:
                                            # 匹配内容关键词
                                            for para_node in para_nodeLst.getChildren():
                                                if check(para_node, content_keywords):
                                                    score = score + 1
                                                    selectedSentLst.append(para_node.getTextContent() + '\n')
                                                    para_nodeLst.setSelected(True)
                                                    para_node.setSelected(True)
                                        # 图表节点
                                        if para_nodeLst.getType() == 3 or para_nodeLst.getType() == 4:
                                            #找上下文一段内的关键词
                                            if para_nodeLst.getSelected() == False:
                                                para_nodeLst.setSelected(True)
                                                for para_node in para_nodeLsts[pos - 1].getChildren():
                                                    #print(para_node.getTextContent())
                                                    if check(para_node,before_chart_cuewords) and para_node.getSelected() == False:
                                                        para_node.setSelected(True)
                                                        selectedSentLst.append(para_node.getTextContent() + '\n')
                                                for para_node in para_nodeLsts[pos + 1].getChildren():
                                                    if check(para_node,after_chart_cuewords) and para_node.getSelected() == False:
                                                        #print(para_node.getTextContent())
                                                        para_node.setSelected(True)
                                                        selectedSentLst.append(para_node.getTextContent() + '\n')
                                                if para_nodeLst.getType() == 3:
                                                    #selectedSentLst.extend(str(para_nodeLst.getTableData()))
                                                    selectedSentLst.append(str(para_nodeLst.getType()))
                                                if para_nodeLst.getType() == 4:
                                                    selectedSentLst.append(str(para_nodeLst.getrid()))
                                                    '''
                                                    image:
                                                        <v:shape id="_x0000_i1025" type="#_x0000_t75" style="width:208.5pt;height:50.25pt" o:ole="" filled="t">
                                                         <v:imagedata r:id="rId8" o:title=""/>
                                                        </v:shape>
                                                    id="_x0000_i1025" ————image1
                                                    id="_x0000_i1026" ————image2
                                                    '''
                                            score = score + 1

                                        pos = pos + 1
                                    # 选中得分大于1的二级节点
                                if score > 1:
                                    heading1_child.setSelected(True)
                                    heading2_node.setSelected(True)
                            # 遍历三级标题节点
                            heading3_nodeList = heading1_child.getTreenodes(2)
                            # print(heading3_nodeList)
                            for heading3_node in heading3_nodeList:
                                score = 0
                                # print(heading3_node)
                                # 三级标题匹配
                                if check(heading3_node, docpart["heading_keywords"]) or (
                                        isNode(heading3_node) and check(heading3_node.getParent(),
                                                                        docpart["heading_keywords"])):
                                    #if selectMode == 1:
                                    #    selectedSentLst.extend(heading3_node.getFirstSentInNode())
                                    score = score + 2
                                    pos = 0
                                    para_nodeLsts = heading3_node.getChildren()
                                    for para_nodeLst in para_nodeLsts:
                                        # 段落节点
                                        if para_nodeLst.getSelected() == False and para_nodeLst.getType() == 1:
                                            for para_node in para_nodeLst.getChildren():
                                                if check(para_node, content_keywords):
                                                    score = score + 1
                                                    selectedSentLst.append(para_node.getTextContent() + '\n')
                                                    para_nodeLst.setSelected(True)
                                                    para_node.setSelected(True)
                                        # 图表节点
                                        if para_nodeLst.getType() == 3 or para_nodeLst.getType() == 4 or para_nodeLst.getType() == 5:
                                            if para_nodeLst.getSelected() == False:
                                                para_nodeLst.setSelected(True)
                                                #获取图题和图注解
                                                if pos > 0:
                                                    for para_node in para_nodeLsts[pos - 1].getChildren():
                                                        print(para_node.getTextContent())
                                                        if check(para_node,before_chart_cuewords) and para_node.getSelected() == False:
                                                            para_node.setSelected(True)
                                                            selectedSentLst.append(para_node.getTextContent() + '\n')
                                                if pos + 1< len(para_nodeLsts):
                                                    for para_node in para_nodeLsts[pos + 1].getChildren():
                                                        if check(para_node,after_chart_cuewords) and para_node.getSelected() == False:
                                                            print(para_node.getTextContent())
                                                            para_node.setSelected(True)
                                                            selectedSentLst.append(para_node.getTextContent() + '\n')
                                                selectedSentLst.extend(str(para_nodeLst.getType()))
                                            score = score + 1

                                if score > 1:
                                    heading3_node.getParent().setSelected(True)
                                    heading3_node.setSelected(True)
                                    heading1_child.setSelected(True)
                    selectedSentDic[docpart["name"]] = selectedSentLst
        #print(selectedSentLst)
        #with open(outputPath + '/selectedSentLst.txt', 'w', encoding='UTF-8') as f:
        #    f.writelines(selectedSentLst)
        #    f.close()
        utils.dict_to_json(selectedSentDic,outputPath + '/selectedSentDic.json')

        return docTree


    def firstCompress(self,docTree, classifyResult, outputPath):
        script = self.matchScript(classifyResult)
        result = {}
        parts = script["parts"]
        #逐part选取节点
        #将选取的节点标记为true然后，只要子节点有被选取的节点，父节点也标记为true
        for part in parts:
            part_name = part["name"]
            heading_kw = part["heading_keywords"]
            position = part["position"]
            result.setdefault(part_name,[])
            #标题中包含headingkw的关键词则认为匹配上
            for i in position:
                #回溯去搞
                markSlected(docTree.getChildren()[i],heading_kw,part_name)
                if docTree.getChildren()[i].getSelected():
                    # 选取的节点归类放到对应的part
                    result[part_name].append(docTree.getChildren()[i].getTreeDic())

        utils.dict_to_json(result,outputPath + "/ClassByPart.json")





    def matchScript(self,classifyResult):
        for script in utils.get_file_paths(utils.getScriptPath()):
            script_name = os.path.basename(script).replace('v2.json','')
            if classifyResult == script_name:
                script_json = utils.json_to_dict(script)
                return script_json
        return "There is no script matches: " + classifyResult
    # 第二遍压缩
    def secondNodeSelect(self, selectedDocTree):
        selectedNodeDic = {}
        # 获取每段话的第一句
        for node in nodeList:
            selectedNodeDic[node.getTextContent()] = node.getFirstSentInNode()
        return selectedNodeDic
        # 获取包含父节点（即对应标题）名称的句子


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


def compressDocx(self, docxTree, classifyResult):
    # 重要性评分
    scoringModel = ScoringModel()
    scoringModel.sent_scoring(docxTree, classifyResult)
    scoringModel.table_image_scoring(docxTree, classifyResult)
    scoringModel.sec_scoring(docxTree, classifyResult)
    docxTree.getTreeDic()

    # 内容选取
    for child in docxTree.getChildren():
        if check(child, ["摘要"]):
            pass
        else:
            self.compressChapter(node=child, classifyResult=classifyResult)

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
                    print(child.getTextContent() + " 最大文字量约束为: " + str(maxLength * (child.getScore() / totalScore)))
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


def select_sec(self, node):
    if node.getType() in [0, 1]:
        for child in node.getChildren():
            self.select_sec(child)
            if child.getSelected():
                node.setSelected(True)
