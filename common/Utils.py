import os
import json
from common.MyEncoder import MyEncoder
# 1. 文件路径部分
# 1.1 项目根路径
import jieba

root_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(root_path)
# 1.2 论文分类模块的训练集文件夹
trainSetPath = root_path + "\\public\\dataSet\\train"
# 1.3 论文分类模块的测试集文件夹
testSetPath = root_path + "\\public\\dataSet\\test"
# 1.5 用户测试文件夹
userPath = root_path + "\\public\\user"
# 1.6 剧本文件夹
scriptPath = root_path + "\\public\\script"
# 1.7 Jieba文件夹
jiebaPath = root_path + "\\public\\jieba2"
#用户测试文件夹
inputPath = root_path + "\\public\\user\\input\\"
#测试输出文件
outputPath = root_path + "\\public\\user\\output\\"

# 2. Jieba中文分词部分
# 2.1   哈工大停用词表
stopwords_path = jiebaPath + "\stopwords.txt"
stopwords = [line.strip() for line in open(stopwords_path, encoding='UTF-8')]
# 2.2   论文专业术语词表
# prowords_path = jiebaPath + "\profwords2.txt"
# prowords = [line.strip() for line in open(prowords_path, encoding='UTF-8')]
# 2.3   特征词提取过程中论文噪音词表
# noisewords_path = jiebaPath + "\\noisewords.txt"
# noisewords = [line.strip() for line in open(noisewords_path, encoding='UTF-8')]
# 2.4   同义词词表
synonymwords_path = jiebaPath + "\synonymwords.txt"
synonymwords = [line.strip() for line in open(synonymwords_path, encoding='UTF-8')]
# 2.5   用户自定义词表
userdict_path = jiebaPath + "\\userdict.txt"
jieba.load_userdict(userdict_path)

#2.6 log
log_path = root_path + "\\public\\user\\log\\"

# 幻灯片模板路径
template_path = root_path + "\\public\\templates"

class Utils:
    def __init__(self):
        pass

    # 1. 文件路径部分
    # 1.1 获取项目跟路径
    def getRootPath(self):
        return root_path

    # 1.2 获取论文分类模块的训练集文件夹
    def getTrainSetPath(self):
        return trainSetPath

    # 1.3 获取论文分类模块的测试集文件夹1
    def getTestSetPath(self):
        return testSetPath

    # 1.5 获取用户测试文件夹
    def getUserPath(self):
        return userPath

    # 1.6 获取剧本文件夹
    def getScriptPath(self):
        return scriptPath

    # 获取幻灯片模板文件夹
    def getTemplatePath(self):
        return template_path

    def getInputPath(self):
        return inputPath

    def getOutputPath(self):
        return outputPath
    # 1.7 获取某文件夹下的所有word文件、json文件和图片文件的绝对路径

    def getLogPath(self):
        return log_path

    def get_file_paths(self, dir_path):
        files = os.listdir(dir_path)
        file_paths = []
        for file_name in files:
            file_path = dir_path + "\\" + file_name
            if os.path.splitext(file_path)[1] not in ['.docx', '.txt', '.png', 'jpeg', '.jpg', '.json', '.pptx']:
                pass
            else:
                file_paths.append(file_path)

        return file_paths

    # 2. Jieba中文分词部分
    # 2.1. 中文分词
    def seg_depart(self, sentence, delete_stopwords=True):
        if sentence == None:
            return []
        # 替换同义词
        sentence = self.replaceSynonymWords(sentence)
        sentence_depart = jieba.cut(sentence.strip(), cut_all=False)
        seg_list = []
        for word in sentence_depart:
            if self.check_chinese(word):
                if delete_stopwords:
                    if word not in stopwords and len(word) > 1:
                        seg_list.append(word)
        return seg_list

    # def getProfwords(self):
    #     return prowords

    # def getNoisewords(self):
    #     return noisewords

    # 2.2. 检查是否是中文词汇
    def check_chinese(self, check_str):
        for ch in check_str:
            if ch < '\u4e00' or ch > u'\u9fff':
                return False
        return True

    # 2.3 检查是否为数字
    def is_number(self, str):
        try:
            float(str)
            return True
        except ValueError:
            pass

        try:
            import unicodedata
            unicodedata.numeric(str)
            return True
        except (TypeError, ValueError):
            pass

        return False

    # 2.4 替换同义词
    def replaceSynonymWords(self, sentence):
        # 读取同义词表，并生成一个字典
        combine_dict = {}
        # synonym_words.txt是同义词表，每行是一系列同义词，用" "分割
        for line in open(synonymwords_path, "r", encoding="UTF-8"):
            seperate_word = line.strip().split(" ")
            # print(seperate_word)
            num = len(seperate_word)
            for i in range(1, num):
                combine_dict[seperate_word[i]] = seperate_word[0]

        # 将语句切分成单词
        seg_list = jieba.cut(sentence, cut_all=False)
        f = "/".join(seg_list).encode("utf-8")
        f = f.decode("utf-8")

        # 返回同义词替换后的句子
        final_sentence = ""
        for word in f.split("/"):
            if word in combine_dict:
                word = combine_dict[word]
                final_sentence += word
            else:
                final_sentence += word
        return final_sentence


    # 3. 字典与json文件的转换
    # 3.1 字典转json文件
    def dict_to_json(self, src_dict, file_path):
        dir = os.path.dirname(file_path)
        if os.path.exists(dir):
            pass
        else:
            os.makedirs(dir)
        with open(file_path, 'w', encoding='UTF-8') as f:
            f.write(json.dumps(src_dict, ensure_ascii=False, indent=2))
            f.close()

    # 3.2 json文件转字典
    def json_to_dict(self, file_path):
        with open(file_path, "r", encoding="UTF-8") as f:
            load_dict = json.load(f)
            #print(type(load_dict))
            f.close()
        return load_dict

