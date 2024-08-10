from src.docxParser.DocxParser import DocxParser
from src.classifier2.Classifier import Classifier
from src.docxCompresser2.DocxCompresserPlus import DocxCompresserPlus
from common.Utils import Utils
from src.pptGenerator.PPTGenerator import parseDicToSlide
from src.pptGenerator.PPTTree import PPTTree
import os
import docx
from src.picExtractor.picExtractor import PicExtractor

utils = Utils()


def run(input_file_path, output_file_path):
    # 文档解析
    docxParser = DocxParser()
    result = docxParser.extractPic(input_file_path, output_file_path)
    if result == -1 : return
    docxTree = docxParser.parseDocx(input_file_path, output_file_path)

    # 论文分类
    classifier = Classifier()
    classifyModel = classifier.loadModel()
    classifyResult = classifyModel.classify(input_file_path)

    # 文档第一遍压缩
    docxCompresserPlus = DocxCompresserPlus()
    result = docxCompresserPlus.set_result(classifyResult)
    if result == -1: return
    classifiedByPartDic = docxCompresserPlus.firstCompress(docxTree, output_file_path)
    scoreDic = docxCompresserPlus.score(classifiedByPartDic, output_file_path)
    chosenDic = docxCompresserPlus.choose(scoreDic, output_file_path)

    # 构建PPTTree
    pptTree = PPTTree(output_file_path)
    pptTree.buildPPTDic(chosenDic, output_file_path)

    # 幻灯片生成
    parseDicToSlide(pptTree)


if __name__ == '__main__':
    # 批量
    output_path = utils.getOutputPath()
    for file in utils.get_file_paths(utils.getInputPath()):
        if file.endswith(".docx") and file.split(".docx")[0].split("\\")[-1] not in os.listdir(output_path):
            title = file.split(".docx")[0].split("\\")[-1]
            print(title + " starts")
            run(input_file_path=file, output_file_path=output_path + "\\" + title)
            print(title + " is done!")

    # 单独
    # file_path = utils.getUserPath() + "\input" + "/~$01815057-丁璇-1.《高管风险承担与企业ESG的实证研究》.docx"
    # output_dir_path = utils.getUserPath() + "\output" + "/~$01815057-丁璇-1.《高管风险承担与企业ESG的实证研究》.docx"
    # run(file_path, output_dir_path)
