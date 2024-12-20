import math
import os.path

from src.classifier2.TFCounter import TFCounter
from common.Utils import Utils
import time
utils = Utils()


def matchModel(modelName):
    for model in utils.get_file_paths(utils.getModelPath()):
        fileName = os.path.basename(model).replace('v1.json', '')
        if modelName == fileName:
            modelJson = utils.json_to_dict(model)
            # self.modelScript = modelJson
            return modelJson
    return -1


class ClassifyModel:
    def __init__(self):
        pass

    # 加惩罚分，缺某一部分直接pass
    def classify(self, file_path):
        tfCounter = TFCounter()
        keywordDic = {}
        penalty_keywords = {}
        # award_keywords = {}
        # script_dic = {}
        for script_path in utils.get_file_paths(utils.getScriptPath()):
            file_name = os.path.basename(script_path)
            script_name = file_name.replace(".json", "")
            script_dic = utils.json_to_dict(script_path)
            keywordDic[script_name] = script_dic["keyword"]
            penalty_award = script_dic["penalty_award"]
            penalty_keywords[script_name] = penalty_award
            # award_keywords[script_name] = penalty_award[1]
        wordDic = tfCounter.tfcount(file_path)
        maxScore = -100
        classifyResult = ''
        for script_name, keyword in keywordDic.items():
            score = 0.0
            script_dic = utils.json_to_dict(utils.getScriptPath() + '\\' + script_name + '.json')
            penalty_weight = penalty_keywords[script_name]["penalty_weight"]
            # 计算奖励分和惩罚分
            for penalty_keyword in penalty_keywords[script_name]["penalty_keywords"]:
                for part in script_dic["parts"]:
                    if penalty_keyword in part["name"]:
                        # 如果关键部分是组件，加载对应组件进脚本
                        if 'model' in part:
                            model = matchModel(part["model"])
                            for theory in model["theory-type"]:
                                if theory["name"] == script_name:
                                    penalty_words = {}
                                    # theory_type = theory
                                    for word in theory["heading_keywords"]:
                                        penalty_words[word] = penalty_weight
                                    keyword["penalty_words"] = penalty_words
            # for part in ["title", "abstract", "key_word", "heading1", "heading2", "heading3", "main_text"]:
            for part in keyword.keys():
                if part == "penalty_words":
                    # 聚合所有title
                    title_words_in_word = set()
                    # 聚合所有的heading_words
                    heading_words_in_word = set()
                    # 聚合
                    for key in wordDic.keys():
                        if 'heading' in key:
                            for k in wordDic[key].keys():
                                heading_words_in_word.add(k)
                        if 'title' in key:
                            for k in wordDic[key].keys():
                                title_words_in_word.add(k)
                    # 奖惩分
                    for word in keyword[part].keys():
                        # if word in keyword[part]:
                        # 题目奖励分
                        if word in heading_words_in_word:
                            score += keyword[part][word] * 0.2
                        # 标题奖惩分
                        if word in heading_words_in_word:
                            score += keyword[part][word] * 0.2
                        else:
                            score -= keyword[part][word] * 0.1
                    # 不再执行下边的score
                    continue
                for word, cnt in wordDic[part].items():
                    if word in keyword[part]:
                        score += math.sqrt(cnt) * keyword[part][word]

            print(script_name + " 剧本得分为: " + str(score))
            if score > maxScore:
                maxScore = score
                classifyResult = script_name
        file_name = os.path.basename(file_path)
        print(file_name + " advanced分类结果为: " + classifyResult + ", 得分为: " + str(maxScore))
        res = [classifyResult, wordDic["main_text"]]
        return res
