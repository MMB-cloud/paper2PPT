from src.docxParser.DocxParser import DocxParser
from src.classifier2.Classifier import Classifier
from src.classifier2.Category import Category
from src.docxCompresser2.DocxCompresser import DocxCompresser
from src.docxCompresser2.DocxCompresserPlus import DocxCompresserPlus
from src.pptGenerator.PPTGenerator import PPTGenerator
from Utils import Utils

# from src.classifier2.TFCounter import TFCounter

# from DocxCompresser import DocxCompresser


utils = Utils()

if __name__ == "__main__":
    #     classifier = Classifier()
    #     classifier.trainModel()
    #     classifier.testModel()

    file_path = utils.getUserPath() + "\input" + "/U201816007-李佳妮-1.《面部情绪表达对亲社会众筹成功的影响》.docx"
    output_dir_path = utils.getUserPath() + "\output" + "/U201816007-李佳妮-1.《面部情绪表达对亲社会众筹成功的影响》"
    # file_path = utils.getTestSetPath() + "\实证研究类"
    # output_dir_path = utils.getUserPath()

    # 文档解析
    docxParser = DocxParser()
    docxTree = docxParser.parseDocx(file_path, output_dir_path)
    leafnodes = docxTree.getleafnodes()  # leafnodes直接获取到末级节点
    # for leafnode in leafnodes:
    #    print(leafnode.getTextContent())
    children = docxTree.getChildren()
    # 一层child是一级标题
    #for child in children:  # child = type0 child[1] = 绪论 child[2] = 引言
        #print(child.getTextContent())
        #for ch in child.getChildren():  # ch = type1 ch[1]
        #    print(ch.getTextContent())

    # wordDic = TFCounter().tfcount(file_path)
    # print(wordDic)
    # 论文分类
    classifier = Classifier()
    classifyModel = classifier.loadModel()
    classifyResult = classifyModel.classify(file_path)

    # 文档第一遍压缩
    docxCompresserPlus = DocxCompresserPlus()
    docxCompresser = DocxCompresser()
    selecetedDoctree = docxCompresserPlus.firstNodeSelect(docxTree, classifyResult, output_dir_path)
    selecetedNodeList = selecetedDoctree.getSelectedNodeList()
    selecetedDoctree.getTreeDic()
    #print(selecetedNodeList)
    # docxCompresser.compressDocx(docxTree, classifyResult)

    # # 幻灯片生成
    # pptGenerator = PPTGenerator()
    # pptGenerator.generatePPT2(json_path=utils.getUserPath() + "\pptTree.json", output_dir_path=output_dir_path)

    # avgScore = docxTree.getAvgScore()
    # print("平均值为: ", avgScore)

    # treenodes = []
    # for child in docxTree.getChildren():
    #     if '摘要' in child.getTextContent().replace(" ", ""):
    #         pass
    #     else:
    #         treenodes.extend(child.getLowerTreeNodes())
    # for treenode in treenodes:
    #     print(treenode.getTextContent())

    # for child in docxTree.getChildren():
    #     if "摘要" in child.getTextContent().replace(" ", ""):
    #         pass
    #     else:
    #         imageMatrix = child.getImages()
    #         if len(imageMatrix) != 0:
    #             for imageArray in imageMatrix:
    #                 if imageArray[1] != None:
    #                     print(imageArray[1].getChildren()[0].getTextContent())
    #                     for leafnode in imageArray[2]:
    #                         print(leafnode.getTextContent())
    #                 else:
    #                     print("没有图标题")

    # for child in docxTree.getChildren():
    #     if "摘要" in child.getTextContent().replace(" ", ""):
    #         pass
    #     else:
    #         tableMatrix = child.getTables()
    #         if len(tableMatrix) != 0:
    #             for tableArray in tableMatrix:
    #                 if tableArray[1] != None:
    #                     print(tableArray[1].getChildren()[0].getTextContent())
    #                     for leafnode in tableArray[2]:
    #                         print(leafnode.getTextContent())
    #                 else:
    #                     print("没有表标题")

    # for child in docxTree.getChildren():
    #     if "摘要" in child.getTextContent().replace(" ", ""):
    #         pass
    #     else:
    #         unitMatrix = child.getUnitMatrix()
    #         para_leafnodes = unitMatrix[0]  # 段落文本块，句子集合
    #         tableMatrix = unitMatrix[1]     # 表格块 [[表格节点, 表标题节点, 描述性句子集合, 位置向量]]
    #         imageMatrix = unitMatrix[2]     # 图像块 [[图像节点, 图标题节点, 描述性句子集合, 位置向量]]
    # for leafnode in para_leafnodes:
    #     print(leafnode.getTextContent())
    #     print(leafnode.getPosition())
    # for tableArray in tableMatrix:
    #     if tableArray[1] != None:   # 存在表标题节点
    #         print(tableArray[1].getChildren()[0].getTextContent())
    # for imageArray in imageMatrix:
    #     if imageArray[1] != None:
    #         print(imageArray[1].getChildren()[0].getTextContent())
