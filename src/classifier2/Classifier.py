import os

from src.classifier2.Category import Category
from src.classifier2.ClassifyModel import ClassifyModel
from Utils import Utils

utils = Utils()

class Classifier:
    def __init__(self):
        pass

    def trainModel(self):
        categoryList = []

        # 1. 获取训练集文件夹路径
        trainSetPath = utils.getTrainSetPath()
        for dir in os.listdir(trainSetPath + "\\" + "input"):
            category_name = dir
            input_dir_path_ = trainSetPath + "\\" + "input" + "\\" + dir
            output_dir_path = trainSetPath + "\\" + "output" + "\\" + dir
            category = Category(category_name, input_dir_path_, output_dir_path)
            category.getWordDic()
            categoryList.append(category)
        # 2. 论文集总词频统计
        collectionWordDic = {}
        if os.path.exists(trainSetPath + "\\" + "output" + "\wordDic.json"):
            collectionWordDic = utils.json_to_dict(trainSetPath + "\\" + "output" + "\wordDic.json")
        else:
            for part in ['title', 'abstract', 'key_word', 'heading1', 'heading2', 'heading3', 'main_text']:
                collectionWordDic[part] = {}
                for category in categoryList:
                    categoryWordDic = category.getWordDic()
                    for word, wordCount in categoryWordDic[part].items():
                        if word not in collectionWordDic[part]:
                            collectionWordDic[part][word] = {"num": wordCount["num"], "df": wordCount["df"]}
                        else:
                            collectionWordDic[part][word]["num"] += wordCount["num"]
                            collectionWordDic[part][word]["df"] += wordCount["df"]
        utils.dict_to_json(collectionWordDic, trainSetPath + "\\" + "output" + "\wordDic.json")
        # 3. tfidf计算
        num = 0
        for category in categoryList:
            num += len(category.getFilePaths())
        for category in categoryList:
            category.getTfidfWordDic(collectionWordDic, num)
        # for category in categoryList:
        #     category.getDfidfWordDic(wordDic, num)
        # 4. 特征词选取
        for category in categoryList:
            category.getKeywordDic()

    def loadModel(self):
        classifyModel = ClassifyModel()
        return classifyModel

    def testModel(self):
        classifyModel = self.loadModel()
        adict = {}
        wrongFile = {}
        testSetPath = utils.getTestSetPath()
        for category_name in os.listdir(testSetPath):
            input_dir_path = testSetPath + "\\" + category_name
            file_paths = utils.get_file_paths(input_dir_path)
            correctNum = 0
            for file_path in file_paths:
                classifyResult = classifyModel.classify(file_path)
                if classifyResult == category_name:
                    correctNum += 1
                else:
                    wrongFile[file_path] = [category_name, classifyResult]
            correctRate = float(correctNum) / float(len(file_paths))
            adict[category_name] = correctRate
        for category_name, correctRate in adict.items():
            print(category_name + " 的分类正确率为: " + str(correctRate))
        print("以下这些文档分类错误: ")
        for file_path in wrongFile:
            file_name = os.path.basename(file_path)
            print(file_name + " 正确分类结果为: " + wrongFile[file_path][0], " 分类器分类结果为: " + wrongFile[file_path][1])


