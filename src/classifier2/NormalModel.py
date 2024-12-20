import math
import os.path

from src.classifier2.TFCounter import TFCounter
from common.Utils import Utils

utils = Utils()


def matchModel(modelName):
    for model in utils.get_file_paths(utils.getModelPath()):
        fileName = os.path.basename(model).replace('v1.json', '')
        if modelName == fileName:
            modelJson = utils.json_to_dict(model)
            # self.modelScript = modelJson
            return modelJson
    return -1


class NormalModel:
    def __init__(self):
        pass

    # for part in ["title", "abstract", "key_word", "heading1", "heading2", "heading3", "main_text"]:
    # for part in keyword.keys():
    # script_dic = utils.json_to_dict(utils.getScriptPath() + '\\' + script_name + '.json')
    # 只计算TFIDF分数
    def classify(self, file_path):
        tfCounter = TFCounter()
        keywordDic = {}
        for script_path in utils.get_file_paths(utils.getScriptPath()):
            file_name = os.path.basename(script_path)
            script_name = file_name.replace(".json", "")
            script_dic = utils.json_to_dict(script_path)
            keywordDic[script_name] = script_dic["keyword"]
            #penalty_award = script_dic["penalty_award"]
            #penalty_keywords[script_name] = penalty_award
            # award_keywords[script_name] = penalty_award[1]
        wordDic = tfCounter.tfcount(file_path)
        maxScore = 0.0
        classifyResult = ''
        for script_name, keyword in keywordDic.items():
            score = 0.0
            for word, cnt in wordDic["main_text"].items():
                if word in keyword["main_text"]:
                    score += math.sqrt(cnt) * keyword["main_text"][word]
            print(script_name + " 剧本得分为: " + str(score))
            if score > maxScore:
                maxScore = score
                classifyResult = script_name
        file_name = os.path.basename(file_path)
        print(file_name + " Normal分类结果为: " + classifyResult + ", 得分为: " + str(maxScore))
        res = [classifyResult, wordDic["main_text"]]
        return res

    #normal版
    # def classify1(self, file_path):
    #     tfCounter = TFCounter()
    #     keywordDic = {}
    #     for script_path in utils.get_file_paths(utils.getScriptPath()):
    #         file_name = os.path.basename(script_path)
    #         script_name = file_name.replace(".json", "")
    #         script_dic = utils.json_to_dict(script_path)
    #         keywordDic[script_name] = script_dic["keyword"]
    #         #penalty_award = script_dic["penalty_award"]
    #         #penalty_keywords[script_name] = penalty_award
    #         # award_keywords[script_name] = penalty_award[1]
    #     wordDic = tfCounter.tfcount(file_path)
    #     maxScore = 0.0
    #     classifyResult = ''
    #     for script_name, keyword in keywordDic.items():
    #         score = 0.0
    #         script_dic = utils.json_to_dict(utils.getScriptPath() + '\\' + script_name + '.json')
    #         # for part in ["title", "abstract", "key_word", "heading1", "heading2", "heading3", "main_text"]:
    #         for part in keyword.keys():
    #             for word, cnt in wordDic[part].items():
    #                 if word in keyword[part]:
    #                     score += math.sqrt(cnt) * keyword[part][word]
    #         print(script_name + " 剧本得分为: " + str(score))
    #         if score > maxScore:
    #             maxScore = score
    #             classifyResult = script_name
    #     file_name = os.path.basename(file_path)
    #     print(file_name + " Normal分类结果为: " + classifyResult + ", 得分为: " + str(maxScore))
    #     res = [classifyResult, wordDic["main_text"]]
    #     return res
