import os

from src.docxParser.DocxParser import DocxParser
from src.classifier2.Classifier import Classifier
from src.docxCompresser2.DocxCompresserPlus import DocxCompresserPlus
from common.Utils import Utils

utils = Utils()
if __name__ == "__main__":
    input_folder_path = utils.getUserPath() + '/input'
    output_folder_path = utils.getUserPath() + '/output'
    for file in os.listdir(input_folder_path):
        #print(input_folder_path + os.sep + file)
        input_file = input_folder_path + os.sep + file
        output_dir = output_folder_path + os.sep + file.replace(".docx","")
        # 文档解析
        docxParser = DocxParser()
        docxTree = docxParser.parseDocx(input_file, output_dir)
        # 论文分类
        classifier = Classifier()
        classifyModel = classifier.loadModel()
        classifyResult = classifyModel.classify(input_file)
        # 文档第一遍压缩
        docxCompresserPlus = DocxCompresserPlus()
        selecetedDoctree = docxCompresserPlus.firstNodeSelect(docxTree, classifyResult, output_dir)
        selecetedNodeList = selecetedDoctree.getSelectedNodeList()
        selecetedDoctree.getTreeDic()
