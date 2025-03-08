from src.docxParser.DocxParser import DocxParser
from src.classifier2.Classifier import Classifier
from src.docxCompresser2.DocxCompresserPlus import DocxCompresserPlus
from src.docxCompresser2.EvaluateModel import EvaluateModel
from common.Utils import Utils
from src.pptGenerator.PPTGenerator import parseDicToSlide
from src.pptGenerator.PPTTree import PPTTree
from src.classifier2.TFCounter import TFCounter
import os
import docx
from src.picExtractor.picExtractor import PicExtractor
import time
import json

utils = Utils()
classifier = Classifier()


def run(input_file_path, output_file_path):
    # 文档解析
    docxParser = DocxParser()
    result = docxParser.extractPic(input_file_path, output_file_path)
    if result == -1: return
    docxTree = docxParser.parseDocx(input_file_path, output_file_path)
    # docxTree = docxParser.compressDocTree(docxTree) # 替换复合节点 待优化

    # 论文分类
    classifier = Classifier()
    classifyModel = classifier.loadModel()
    res = classifyModel.classify(input_file_path)
    classifyResult = res[0]
    main_word_freq = res[1]

    # 文档第一遍压缩
    # docxCompresserPlus = DocxCompresserPlus()
    # result = docxCompresserPlus.set_result(classifyResult)
    # docxCompresserPlus.set_main_word_freq(main_word_freq)
    # if result == -1: return
    # classifiedByPartDic = docxCompresserPlus.firstCompress(docxTree, output_file_path)
    # scoreDic = docxCompresserPlus.score(classifiedByPartDic, output_file_path)
    #生成版
    # chosenDic = docxCompresserPlus.choose(scoreDic, output_file_path)
    # # 构建PPTTree
    # pptTree = PPTTree(output_file_path)
    # pptTree.buildPPTDic(chosenDic, output_file_path)

    # 幻灯片生成
    #parseDicToSlide(pptTree)
    #评估版
    # rouge_lst = []
    #res = docxCompresserPlus.evaluate_choose(scoreDic, output_file_path)
    # rouge_lst.append(res)
    return res

    # 计算正文词频
    # 11.17 用tfcounter的数据
    # leafs = docxTree.getleafnodes()
    # main_word_freq = {}
    # for sent_node in leafs:
    #     seg_words = utils.seg_depart(sent_node.getTextContent())
    #     for seg_word in seg_words:
    #         main_word_freq.setdefault(seg_word, 0)
    #         main_word_freq[seg_word] += 1


if __name__ == '__main__':
    classifier.compareF1()
    #classifier.trainModel()

# 接口计时

# classifier.compareF1()
