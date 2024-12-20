import os

from src.classifier2.Category import Category
from src.classifier2.ClassifyModel import ClassifyModel
from src.classifier2.NormalModel import NormalModel
from common.Utils import Utils
import time

utils = Utils()
normalModel = NormalModel()


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
            print(file_name + " 正确分类结果为: " + wrongFile[file_path][0],
                  " 分类器分类结果为: " + wrongFile[file_path][1])

    def compareF1(self):
        start_time = time.time()
        advancedModel = self.loadModel()
        testSetPath = utils.getTestSetPath()
        # FP
        advFpDic = {}
        norFpDic = {}
        # TP
        advCorrectNum = {}
        norCorrectNum = {}
        # FN
        advWrongFile = {}
        norWrongFile = {}
        # len
        categoryLenDic = {}
        for category_name in os.listdir(testSetPath):
            # 初始化FpDic 不初始化会keyerror
            advFpDic[category_name] = []
            norFpDic[category_name] = []
        for category_name in os.listdir(testSetPath):
            input_dir_path = testSetPath + "\\" + category_name
            file_paths = utils.get_file_paths(input_dir_path)
            categoryLenDic[category_name] = len(file_paths)

            for file_path in file_paths:
                advResult = advancedModel.classify(file_path)[0]
                norResult = normalModel.classify(file_path)[0]
                if advResult == category_name:
                    # TP
                    advCorrectNum.setdefault(category_name, 0)
                    advCorrectNum[category_name] += 1
                elif advResult != '':
                    # FN
                    advWrongFile[file_path.split('\\')[-1]] = advResult
                if norResult == category_name:
                    # TP
                    norCorrectNum.setdefault(category_name, 0)
                    norCorrectNum[category_name] += 1
                elif norResult != '':
                    # FN
                    norWrongFile[file_path.split('\\')[-1]] = norResult
        for fileEntry in advWrongFile.items():
            advFpDic[fileEntry[1]].append(fileEntry[0])
        for fileEntry in norWrongFile.items():
            norFpDic[fileEntry[1]].append(fileEntry[0])

        # 计算加权F1
        # advFp = [len(values) for values in advFpDic.values()]
        # norFp = [len(values) for values in norFpDic.values()]
        advPrecise = {}
        norPrecise = {}
        advRecall = {}
        norRecall = {}
        sumLen = sum(values for values in categoryLenDic.values())
        for tp in advCorrectNum.items():
            wei = categoryLenDic[tp[0]] / sumLen
            advPrecise[tp[0]] = (float(tp[1]) / (float(tp[1]) + float(len(advFpDic[tp[0]])))) * wei
            advRecall[tp[0]] = (float(tp[1]) / (float(tp[1]) + float(categoryLenDic[tp[0]] - tp[1]))) * wei
        for tp in norCorrectNum.items():
            wei = categoryLenDic[tp[0]] / sumLen
            norPrecise[tp[0]] = (float(tp[1]) / (float(tp[1]) + float(len(norFpDic[tp[0]])))) * wei
            norRecall[tp[0]] = (float(tp[1]) / (float(tp[1]) + float(categoryLenDic[tp[0]] - tp[1]))) * wei

        advF1 = 0
        norF1 = 0
        for category in advPrecise.keys():
            advF1 += 2 * advPrecise[category] * advRecall[category] / (advPrecise[category] + advRecall[category])
            norF1 += 2 * norPrecise[category] * norRecall[category] / (norPrecise[category] + norRecall[category])

        print("优化TF-IDF的加权F1得分为：" + str(advF1))
        print("普通TF-IDF的加权F1得分为：" + str(norF1))
        end_time = time.time()
        print(f"调用耗时：{(end_time - start_time) / 60} 分钟")
        print(" ")
    # norPrecise = float(norCorrectNum) / (float(norCorrectNum) + norFp)

    # advRecall = float(advCorrectNum) / (float(advCorrectNum) + len(advWrongFile))
    # norRecall = float(norCorrectNum) / (float(norCorrectNum) + len(norWrongFile))
# if __name__ == '__main__':
#    classifier = Classifier()
#    classifier.trainModel()
