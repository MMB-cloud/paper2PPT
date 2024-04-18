import os
import math
import zipfile
import re

from src.classifier2.TFCounter import TFCounter
from Utils import Utils

utils = Utils()

class Category:
    def __init__(self, category_name, input_dir_path, output_dir_path):
        self.__category_name = category_name
        self.__input_dir_path = input_dir_path
        self.__output_dir_path = output_dir_path

        self.__file_paths = utils.get_file_paths(input_dir_path)
        if os.path.exists(output_dir_path):
            pass
        else:
            os.makedirs(output_dir_path)

        self.__wordDic = {}
        self.__tfidfWordDic = {}
        self.__keywordDic = {}

    def getWordDic(self):
        if len(self.__wordDic) != 0:
            return self.__wordDic
        if os.path.exists(self.__output_dir_path + "\categoryWordDic.json"):
            self.__wordDic = utils.json_to_dict(self.__output_dir_path + "\categoryWordDic.json")
            return self.__wordDic

        print("论文类别: " + self.__category_name + " 词频统计开始")

        # 1. 对论文类别下的每个word文档进行词频统计
        wordDicList = []
        tfCounter = TFCounter()
        for file_path in self.__file_paths:
            if file_path != "":
                wordDicList.append(tfCounter.tfcount(file_path))
        # 2. 词频统计汇总
        #for part in ['title', 'abstract', 'key_word', 'heading1', 'heading2', 'heading3', 'main_text']:
        for part in ['heading1', 'heading2', 'heading3']:
            self.__wordDic[part] = {}
            for wordDic in wordDicList:
                for word, num in wordDic[part].items():
                    if word not in self.__wordDic[part]:
                        self.__wordDic[part][word] = {"num": num, "df": 1}
                    else:
                        self.__wordDic[part][word]["num"] += num
                        self.__wordDic[part][word]["df"] += 1
        # 3. 结果保存
        utils.dict_to_json(self.__wordDic, self.__output_dir_path + "\categoryWordDic.json")

    def getTfidfWordDic(self, wordDic, num):    # wordDic: 论文集总词频统计 num: 论文总数
        if len(self.__tfidfWordDic) != 0:
            return self.__tfidfWordDic
        if os.path.exists(self.__output_dir_path + "\\tfidfWordDic.json"):
            self.__tfidfWordDic = utils.json_to_dict(self.__output_dir_path + "\\tfidfWordDic.json")
            return self.__tfidfWordDic
        print("论文类别: " + self.__category_name + " tfidf统计开始")

        # 权重系数设置: heading2=heading3>heading1>title>abstract>key_word>main_text
        weight = [3.0, 3.0, 2.5, 2.0, 1.5, 1.0, 0.5]
        parts = ['title', 'abstract', 'key_word', 'heading1', 'heading2', 'heading3', 'main_text']
        for part in parts:
            self.__tfidfWordDic[part] = {}
            totalNum = 0
            for word, wordCount in self.__wordDic[part].items():
                totalNum += wordCount["num"]
            for word, wordCount in self.__wordDic[part].items():
                tf = float(wordCount["num"]) / float(totalNum)
                idf = math.log(float(num * wordCount["df"]) / float(wordDic[part][word]["df"]))
                tfidf = tf * idf * math.log(len(word)) * weight[parts.index(part)] * math.sqrt(float(wordCount["df"]) / float(len(self.__file_paths)))
                if tfidf > 0.0001:
                    self.__tfidfWordDic[part][word] = tfidf
        utils.dict_to_json(self.__tfidfWordDic, self.__output_dir_path + "\\tfidfWordDic.json")


    def getKeywordDic(self):
        if len(self.__keywordDic) != 0:
            return self.__keywordDic
        if os.path.exists(self.__output_dir_path + "\keywordDic.json"):
            self.__keywordDic = utils.json_to_dict(self.__output_dir_path + "\keywordDic.json")
            return self.__keywordDic
        print("论文类别: " + self.__category_name + " 特征词统计开始")
        
        # 阈值比例设置: heading2=heading3>heading1=abstract>title=key_word>main_text
        threshold = [0.025, 0.025, 0.025, 0.05, 0.10, 0.10, 0.025]
        parts = ['title', 'abstract', 'key_word', 'heading1', 'heading2', 'heading3', 'main_text']
        for part in parts:
            self.__keywordDic[part] = {}
            length = int(len(self.__tfidfWordDic[part]) * threshold[parts.index(part)])
            alist = sorted(self.__tfidfWordDic[part].items(), key=lambda d: d[1], reverse=True)[: length]
            for i in alist:
                self.__keywordDic[part][i[0]] = i[1]
        utils.dict_to_json(self.__keywordDic, self.__output_dir_path + "\keywordDic.json")

    def getFilePaths(self):
        return self.__file_paths




