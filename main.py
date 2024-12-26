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
    docxCompresserPlus = DocxCompresserPlus()
    result = docxCompresserPlus.set_result(classifyResult)
    docxCompresserPlus.set_main_word_freq(main_word_freq)
    if result == -1: return
    classifiedByPartDic = docxCompresserPlus.firstCompress(docxTree, output_file_path)
    scoreDic = docxCompresserPlus.score(classifiedByPartDic, output_file_path)
    #生成版
    # chosenDic = docxCompresserPlus.choose(scoreDic, output_file_path)
    # # 构建PPTTree
    # pptTree = PPTTree(output_file_path)
    # pptTree.buildPPTDic(chosenDic, output_file_path)

    # 幻灯片生成
    #parseDicToSlide(pptTree)
    #评估版
    # rouge_lst = []
    res = docxCompresserPlus.evaluate_choose(scoreDic, output_file_path)
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
    # 批量
    evaluate_lst = []
    output_path = utils.getOutputPath()
    for file in utils.get_file_paths(utils.getInputPath()):
        if file.endswith(".docx") and file.split(".docx")[0].split("\\")[-1] not in os.listdir(output_path):
            title = file.split(".docx")[0].split("\\")[-1]
            print(title + " starts")
            res = run(input_file_path=file, output_file_path=output_path + "\\" + title)
            print(title + " is done!")
            evaluate_lst.append(res)
    print(evaluate_lst)
    if os.path.exists(output_path + 'evaluate1.json'):
        pass
    else:
        os.makedirs(output_path + 'evaluate1.json')
    with open(output_path + 'evaluate1.json', 'w', encoding='UTF-8') as f:
        f.write(json.dumps(evaluate_lst, ensure_ascii=False, indent=2))
        f.close()
    # 过滤无效数据
    filted_evaluate_lst = [data for data in evaluate_lst if data != 0]
    filted_evaluate_lst = [data for data in filted_evaluate_lst if data['rouge1'] > 0.1]
    filted_evaluate_lst = [data for data in filted_evaluate_lst if data['rouge2'] > 0.1]
    # 计算平均值
    rouge1_values = [data['rouge1'] for data in filted_evaluate_lst if 'rouge1' in data]
    rouge2_values = [data['rouge2'] for data in filted_evaluate_lst if 'rouge2' in data]
    rougesl_values = [data['rouge-sl'] for data in filted_evaluate_lst if 'rouge-sl' in data]
    rougesu_values = [data['rouge-su'] for data in filted_evaluate_lst if 'rouge-su' in data]
    avg1 = sum(rouge1_values) / len(rouge1_values) if len(rouge1_values) > 0 else 0
    avg2 = sum(rouge2_values) / len(rouge2_values) if len(rouge2_values) > 0 else 0
    avgsl = sum(rougesl_values) / len(rougesl_values) if len(rougesl_values) > 0 else 0
    avgsu = sum(rougesu_values) / len(rougesu_values) if len(rougesu_values) > 0 else 0
    print(avg1)

    # 单独
    # file_path = utils.getUserPath() + "\input" + "/U201816007-李佳妮-1.《面部情绪表达对亲社会众筹成功的影响》.docx"
    # output_dir_path = utils.getUserPath() + "\output" + "/U201816007-李佳妮-1.《面部情绪表达对亲社会众筹成功的影响》"
    # run(file_path, output_dir_path)
# classifier.compareF1()
# classifier.trainModel()

# 接口计时

# classifier.compareF1()
