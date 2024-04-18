import os.path
import zipfile
import re

from src.docxParser.DocxParser import DocxParser
from Utils import Utils

utils = Utils()

def check(node, wordList):
    matched = False
    for word in wordList:
        if word in node.getTextContent().replace(" ", ""):
            matched = True
            break
    return matched


class TFCounter:
    def __init__(self):
        self.__docxParser = DocxParser()

    def tfcount(self, file_path):
        basename = os.path.basename(file_path)
        # output_path = file_path.replace("input", "output").replace(".docx", ".json")
        # if os.path.exists(output_path):
        #     tfCount = utils.json_to_dict(output_path)
        #     return tfCount

        print(basename + " 词频统计开始")
        docxTree = self.__docxParser.parseDocx(file_path)

        # 1.划分词频统计区域
        title = {}      # 标题
        abstract = {}   # 摘要
        key_word = {}   # 关键词
        heading1 = {}
        heading2 = {}
        heading3 = {}
        main_text = {}


        # 2.标题词频统计
        seg_list = utils.seg_depart(basename.replace(".docx", ""))
        for word in set(seg_list):
            if word not in title:
                title[word] = seg_list.count(word)
            else:
                title[word] += seg_list.count(word)
        
        
        for child in docxTree.getChildren():
            if check(child, ["摘要"]):
                leafnodes = child.getleafnodes()
                for leafnode in leafnodes:
                    if '关键词' in leafnode.getTextContent() or "关键字" in leafnode.getTextContent():  # 关键词词频统计
                        seg_list = utils.seg_depart(leafnode.getTextContent())
                        for word in set(seg_list):
                            if word not in key_word:
                                key_word[word] = seg_list.count(word)
                            else:
                                key_word[word] += seg_list.count(word)
                    else:   # 摘要词频统计
                        seg_list = utils.seg_depart(leafnode.getTextContent())
                        for word in set(seg_list):
                            if word not in abstract:
                                abstract[word] = seg_list.count(word)
                            else:
                                abstract[word] += seg_list.count(word)
            else:
                # heading1 词频统计
                seg_list = utils.seg_depart(child.getTextContent().replace(" ", ""))
                for word in set(seg_list):
                    if word not in heading1:
                        heading1[word] = seg_list.count(word)
                    else:
                        heading1[word] += seg_list.count(word)
                
                
                for grandchild in child.getChildren():
                    if grandchild.getOutLvl() == "1":   # heading2 词频统计
                        seg_list = utils.seg_depart(grandchild.getTextContent().replace(" ", ""))
                        for word in set(seg_list):
                            if word not in heading2:
                                heading2[word] = seg_list.count(word)
                            else:
                                heading2[word] += seg_list.count(word)
                        for grandgrandchild in grandchild.getChildren():
                            if grandgrandchild.getOutLvl() == "2":  # heading3 词频统计
                                seg_list = utils.seg_depart(grandgrandchild.getTextContent().replace(" ", ""))
                                for word in set(seg_list):
                                    if word not in heading3:
                                        heading3[word] = seg_list.count(word)
                                    else:
                                        heading3[word] = seg_list.count(word)
                

                # main_text
                for leafnode in child.getleafnodes():
                    seg_list = utils.seg_depart(leafnode.getTextContent())
                    for word in set(seg_list):
                        if word not in main_text:
                            main_text[word] = seg_list.count(word)
                        else:
                            main_text[word] += seg_list.count(word)
                        
            


        tfCount = {}
        tfCount["title"] = title
        tfCount["abstract"] = abstract
        tfCount["key_word"] = key_word
        tfCount["heading1"] = heading1
        tfCount["heading2"] = heading2
        tfCount["heading3"] = heading3
        tfCount["main_text"] = main_text

        
        # utils.dict_to_json(tfCount, output_path)
        return tfCount




