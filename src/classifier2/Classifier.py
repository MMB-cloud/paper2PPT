import os

from src.classifier2.Category import Category
from src.classifier2.ClassifyModel import ClassifyModel
from src.classifier2.NormalModel import NormalModel
from common.Utils import Utils
from sklearn.metrics import confusion_matrix
from seaborn import heatmap
import matplotlib.pyplot as plt
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
        # 混淆矩阵数据
        index_dic = {"调查研究类":0,"实证研究类v3":1,"优化算法类":2,"软件研发类":3}
        adv_y_true = []
        adv_y_pred = []
        nor_y_true = []
        nor_y_pred = []
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
                if advResult in index_dic.keys():
                    adv_y_true.append(index_dic[category_name])
                    adv_y_pred.append(index_dic[advResult])
                norResult = normalModel.classify(file_path)[0]
                if norResult in index_dic.keys():
                    nor_y_true.append(index_dic[category_name])
                    nor_y_pred.append(index_dic[norResult])
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
        advPrecise_origin = {}
        norPrecise = {}
        norPrecise_origin = {}
        advRecall = {}
        advRecall_origin = {}
        norRecall = {}
        norRecall_origin = {}
        sumLen = sum(values for values in categoryLenDic.values())
        for tp in advCorrectNum.items():
            wei = categoryLenDic[tp[0]] / sumLen
            advPrecise[tp[0]] = (float(tp[1]) / (float(tp[1]) + float(len(advFpDic[tp[0]])))) * wei
            advPrecise_origin[tp[0]] = (float(tp[1]) / (float(tp[1]) + float(len(advFpDic[tp[0]]))))
            advRecall[tp[0]] = (float(tp[1]) / (float(tp[1]) + float(categoryLenDic[tp[0]] - tp[1]))) * wei
            advRecall_origin[tp[0]] = (float(tp[1]) / (float(tp[1]) + float(categoryLenDic[tp[0]] - tp[1])))

        for tp in norCorrectNum.items():
            wei = categoryLenDic[tp[0]] / sumLen
            norPrecise[tp[0]] = (float(tp[1]) / (float(tp[1]) + float(len(norFpDic[tp[0]])))) * wei
            norPrecise_origin[tp[0]] = (float(tp[1]) / (float(tp[1]) + float(len(norFpDic[tp[0]]))))
            norRecall[tp[0]] = (float(tp[1]) / (float(tp[1]) + float(categoryLenDic[tp[0]] - tp[1]))) * wei
            norRecall_origin[tp[0]] = (float(tp[1]) / (float(tp[1]) + float(categoryLenDic[tp[0]] - tp[1])))

        advF1 = 0
        advF1Dic = {}
        norF1 = 0
        norF1Dic = {}
        for category in advPrecise.keys():
            advF1 += 2 * advPrecise[category] * advRecall[category] / (advPrecise[category] + advRecall[category])
            advF1Dic[category] = 2 * advPrecise_origin[category] * advRecall_origin[category] / \
                                 (advPrecise_origin[category] + advRecall_origin[category])
            norF1 += 2 * norPrecise[category] * norRecall[category] / (norPrecise[category] + norRecall[category])
            norF1Dic[category] = 2 * norPrecise_origin[category] * norRecall_origin[category] / \
                                 (norPrecise_origin[category] + norRecall_origin[category])
        cm_adv = confusion_matrix(adv_y_true,adv_y_pred)
        cm_nor = confusion_matrix(nor_y_true,nor_y_pred)
        plt.figure(figsize=(8,6))
        heatmap(cm_adv, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Class 0', 'Class 1', 'Class 2', 'Class 3'],
                yticklabels=['Class 0', 'Class 1', 'Class 2', 'Class 3'])
        plt.title('Confusion Matrix Heatmap (TF-IDF)')
        plt.xlabel('Predicted Label')
        plt.ylabel('True Label')
        plt.show()

        plt.figure(figsize=(8, 6))
        heatmap(cm_nor, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Class 0', 'Class 1', 'Class 2', 'Class 3'],
                yticklabels=['Class 0', 'Class 1', 'Class 2', 'Class 3'])
        plt.title('Confusion Matrix Heatmap (Structured TF-IDF)')
        plt.xlabel('Predicted Label')
        plt.ylabel('True Label')
        plt.show()

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
