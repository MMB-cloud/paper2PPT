import os
import re

from src.docxCompresser2.ScoringModel import ScoringModel
from src.docxCompresser2.ILPModel import ILPModel
from src.docxCompresser2.DocxGenerator import DocxGenerator

from Utils import Utils

utils = Utils()

def check(node, strlist):
    matched = False
    for str in strlist:
        if str in node.getTextContent().replace(" ", ""):
            matched = True
            break
    return matched

class DocxCompresser:
    def __init__(self) -> None:
        pass

    #得到所有能匹配到剧本的节点
    def originCompress(self,docTree,classifyResult):
        #获取剧本中“getdocparts”部分
        docparts = {}
        for script_path in utils.get_file_paths(utils.getScriptPath()):
            script_name = os.path.basename(script_path).replace('plus.json','')
            if classifyResult == script_name:
                docparts = utils.json_to_dict(script_path)["getdocparts"]

        #读取剧本中各节点在文章中的对应部分
        selectNodesDic = {}
        for docpart in docparts:
           for node in docTree.getChildren():
               if check(node,docpart["name"]):
                   selectNodesDic[node.getTextContent()] = node.getChildren()
        print(selectNodesDic)
        return selectNodesDic




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
            if check(node, docpart["name"]):    # 匹配到了，读取规则
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
                        found = False   # 一级章节下是否有二级章节
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
                                    print(child.getTextContent() + " 最大文字量限制为: " + str(maxLength * (child.getScore()/totalScore)))
                                    self.compressSubChapter(node=child, maxLength=maxLength * (child.getScore()/totalScore), docparts=children_docparts, presentation_type=presentation_type)
                        else:   # 一级章节下就是正文，一般来说只有摘要章节和结论章节才会出现这样的情况，如果是摘要章节，就不作处理，如果是结论章节，那就针对一级章节构建整数线性规划模型，如果是其它章节，说明论文内容格式不规范
                            if "摘要" in node.getTextContent().replace(" ", ""):
                                pass
                            else:
                                # 构建整数线性规划模型，进行求解
                                ILP_Model = ILPModel()
                                ILP_Model.build_and_solve(node, maxLength=maxLength, presentation_type=presentation_type, rules=[])
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
            else:   # 没有匹配到
                if getdocparts.index(docpart) == len(getdocparts) - 1:  # 直到最后一个也没有匹配到
                    # 执行默认路径  默认路径下使用整数线性规划模型进行内容选取，且模型选定为图表型
                    default_compress_ratio = 0.25   # 默认压缩比例为0.25
                    default_presentation_type = "chart_oriented"    # 默认生成图表型幻灯片

                    # 根据default_compress_ratio确定一级章节最大文字量
                    maxLength = node.getLength() * default_compress_ratio
                    print(node.getTextContent() + " 最大文字量约束为: " + str(maxLength))

                    # 根据权重占比，分配各二级章节的最大文字量
                    found = False   # 一级章节下是否有二级章节
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
                                print(child.getTextContent() + " 最大文字量约束为: " + str(maxLength * (child.getScore()/totalScore)))
                                self.compressSubChapter(node=child, maxLength=maxLength * (child.getScore()/totalScore), docparts=[], presentation_type="chart_oriented")
                    else:   # 一级章节下就是正文，一般来说只有摘要章节和结论章节才会出现这样的情况, 如果是摘要章节, 如果是结论章节, 那就针对一级章节构建整数线性规划模型, 如果是其它章节, 说明论文内容格式不规范
                        if "摘要" in node.getTextContent().replace(" ", ""):
                                pass
                        else:
                            # 构建整数线性规划模型，进行求解
                            ILP_Model = ILPModel()
                            ILP_Model.build_and_solve(node, maxLength=maxLength, presentation_type="text_based", rules=[])
                else:   # 继续进行匹配
                    continue   





    """二、三级章节内容压缩"""
    def compressSubChapter(self, node, maxLength, docparts=[], presentation_type="chart_oriented"):
        # 判断自身是否是最底层章节或三级章节    整数线性规划模型是围绕二、三级章节构造的
        if node.getOutLvl() == "1": # 二级章节
            found = False   # 是否存在三级章节
            for child in node.getChildren():
                if child.getType() == 0 and child.getOutLvl() == "2":   # 三级章节
                    found = True
                    break
            if found:   # 存在三级章节，就进行文字量再分配, 再进入一层
                totalScore = 0.0
                for child in node.getChildren():
                    totalScore += child.getScore()
                for child in node.getChildren():
                    if child.getType() == 0:
                        print(child.getTextContent() + " 最大文字量约束为: " + str(maxLength * (child.getScore()/totalScore)))
                        self.compressSubChapter(node=child, maxLength=maxLength * (child.getScore()/totalScore), docparts=docparts)
            else:   # 二级章节即为最底层章节，构建整数线性规划模型，并进行求解
                ILP_Model = ILPModel()
                ILP_Model.build_and_solve(node=node, maxLength=maxLength, presentation_type=presentation_type, rules=docparts)
        elif node.getOutLvl() == "2":   # 三级章节
            # 构建整数线性规划模型，并进行求解
            ILP_Model = ILPModel()
            ILP_Model.build_and_solve(node=node, maxLength=maxLength, presentation_type=presentation_type, rules=docparts)

    
    """哪些章节保留"""
    def select_sec(self, node):
        if node.getType() in [0, 1]:
            for child in node.getChildren():
                self.select_sec(child)
                if child.getSelected():
                    node.setSelected(True)


        """
        getdocparts剧本结构设计说明如下:
            "getdocparts": [
                {
                    "name": ["绪论", "导论", "引言", "前言"],   // 一级章节匹配关键词
                    "necessary": true,      // 是否保留 值为true->对其内容进行压缩; 值为false->整个章节直接删除
                    "page_num": [3, 5],      // 限制的生成幻灯片的页数   [min_value, max_value] 注意: 左右都是闭; min_value和max_value可以不设值, 代表没有最大和最小限制, 注意: 要么都设, 要么都不设
                    "compress_mode": "ILP_Model",       // 内容压缩模式 值为"ILP_Model"->使用整数线性规划模型进行内容选取; 值为"sentence_cueword_matching"->使用句式+提示词进行匹配提取
                    "compress_ratio": 0.30,     // 内容压缩比率
                    "presentation_type": "text_based",  // 生成的幻灯片类型, 值为"text_based"->文字型幻灯片, 在进行内容选取时不考虑图表; 值为"chart_oriented"->图表型幻灯片,在进行内容选取时考虑图表, 默认为"chart_oriented"; 注意: 如果设置为图表型幻灯片, 那么内容压缩模式必须为ILP_Model
                    "children: [                // 一级章节下的二、三级章节的规则模板设置
                        {
                            "name": ["研究背景"],           // 二、三级章节匹配关键词
                            "necessary": true,
                            "page_id": 0,           // 生成的幻灯片的id编号, 如果没有其它章节与其共享此id编号, 代表该章节在生成幻灯片时独占一页
                            "sent_num": [3, 6],     // 提取的句子的数量限制 [min_value, max_value] 注意细节同"page_num"
                            "compress_mode": "ILP_Model",      // 在编写剧本时, 可以不设置此字段, 子章节会直接继承父章节的此字段的字段值
                            "display_form": "item_list",    // 提取的句子在生成幻灯片的内容组织形式, 值为"item-list"->项目列表; 值为"key-value"->关键词+项目列表; 值为"table_image_text"->图表+项目列表, 如果设置了这个值, 那么此章节中的图表必须保留下来
                        },
                        {
                            "name": ["研究问题"],
                            "necessary": true,
                            "page_id": 1,
                            "sent_num": [3,6],
                            "compress_mode": "ILP_Model",
                            "display_form": "item_list",
                        },
                        {
                            "name": ["研究目的"],
                            "necessary": true,
                            "page_id": 1,
                            "sent_num": [1, 3],
                            "compress_mode": "ILP_Model",
                            "display_form": "item_list",
                        },
                        {
                            "name": ["研究意义"],
                            "necessary": true,
                            "page_id": 1,       // 可以看到 研究问题、研究目的、研究意义的字段值都为1, 这表示在生成幻灯片时 它们生成在同一页幻灯片上
                            "sent_num": [1, 3],
                            "compress_mode": "ILP_Model",
                            "display_form": "item_list"
                        },
                        {
                            "name": ["研究内容"],
                            "necessary": true,
                            "page_id": 2,
                            "sent_num": [3, 5],
                            "compress_mode": "ILP_Model",
                            "display_form": "item_list",
                        },
                        {
                            "name": ["研究方法"],
                            "necessary": true,
                            "page_id": 2,           // 研究内容和研究方法的字段值都为2, 说明在生成幻灯片时  它们生成在同一页幻灯片上
                            "sent_num": [3, 5],     
                            "compress_mode": "ILP_Model",
                            "display_form": "item_list",
                        }
                    ]
                },
                {
                    "name": ["文献综述"],
                    "necessary": true,
                    "page_num": [3, 5],
                    "compress_mode": "sentence_cueword_matching",  // 使用句式+提示词进行匹配提取，需要设定 "matching_pattern"用于正则匹配句式, 同时设定"cuewords"用于匹配提示词; 此模式一旦设立，对子章节同样有效
                    "matching_pattern": [
                        '19[0-9][0-9]',
                        '20[0-2][0-9]'
                    ],
                    "cuewords": [
                        "介绍了",
                        "阐述了",
                        "提出了",
                        "认为",
                        "验证了",
                        "研究发现",
                        "研究表明",
                        "分析了",
                        "探究了",
                        "进行了",
                        "结果表明",
                        "研究了",
                        "探讨了",
                        "揭露了",
                        "运用了",
                        "构建了",
                        "总结了"
                    ]
                }
            ]
        """
        
