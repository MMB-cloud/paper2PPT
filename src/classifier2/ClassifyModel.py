import math
import os.path

from src.classifier2.TFCounter import TFCounter
from common.Utils import Utils

utils = Utils()

class ClassifyModel:
    def __init__(self):
        pass

    def classify(self, file_path):
        tfCounter = TFCounter()
        keywordDic = {}
        for script_path in utils.get_file_paths(utils.getScriptPath()):
            script_name = os.path.basename(script_path).replace(".json", "")
            keywordDic[script_name] = utils.json_to_dict(script_path)["keyword"]
        wordDic = tfCounter.tfcount(file_path)
        maxScore = 0.0
        classifyResult = ''
        for script_name, keyword in keywordDic.items():
            score = 0.0
            for part in ["title", "abstract", "key_word", "heading1", "heading2", "heading3", "main_text"]:
                for word, num in wordDic[part].items():
                    if word in keyword[part]:
                        score += math.sqrt(num) * keyword[part][word]
            print(script_name + " 剧本得分为: " + str(score))
            if score > maxScore:
                maxScore = score
                classifyResult = script_name
        file_name = os.path.basename(file_path)
        print(file_name + " 分类结果为: " + classifyResult + ", 得分为: " + str(maxScore))
        return classifyResult

