from rouge import Rouge
from common.Utils import Utils
from collections import Counter

utils = Utils()


class EvaluateModel:
    @staticmethod
    def longest_common_subsequence(x, y):
        m = len(x)
        n = len(y)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if x[i - 1] == y[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        lcs = []
        i, j = m, n
        while i > 0 and j > 0:
            if x[i - 1] == y[j - 1]:
                lcs.append(x[i - 1])
                i -= 1
                j -= 1
            elif dp[i - 1][j] > dp[i][j - 1]:
                i -= 1
            else:
                j -= 1
        lcs.reverse()
        return "".join(lcs), dp[m][n]

    @staticmethod
    def calculate_rouge_l(reference, candidate, beta):
        lcs_str, lcs_len = EvaluateModel.longest_common_subsequence(reference, candidate)
        m = len(reference)
        n = len(candidate)
        res = []
        recall = lcs_len / m if m > 0 else 0
        precision = lcs_len / n if n > 0 else 0
        if recall + precision > 0:
            f_score = ((1 + beta * beta) * recall * precision) / (recall + (beta * beta) * precision)
        else:
            f_score = 0
        res.append(precision)
        res.append(recall)
        res.append(f_score)
        return res

    @staticmethod
    def get_ngrams(text, n):
        """
        获取文本的n-gram列表
        """
        words = list(utils.seg_depart(text))
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = "".join(words[i:i + n])
            ngrams.append(ngram)
        return ngrams

    @staticmethod
    def rouge_n(reference, candidate, n):
        """
        计算ROUGE-n指标（n为1或2）
        """
        reference_ngrams = EvaluateModel.get_ngrams(reference, n)
        candidate_ngrams = EvaluateModel.get_ngrams(candidate, n)
        common_ngrams = set(reference_ngrams) & set(candidate_ngrams)
        if len(reference_ngrams) == 0 or len(candidate_ngrams) == 0:
            return 0
        # Precise
        precise = len(common_ngrams) / len(set(candidate_ngrams))
        # Recall
        recall = len(common_ngrams) / len(set(reference_ngrams))
        # F1
        F1 = 5 * precise * recall / (4 * precise + recall) if precise != 0 and recall != 0 else 0
        res = [precise, recall, F1]
        return res

    @staticmethod
    def get_skip_bigrams(text, max_skip=4):
        """
        获取文本中的skip-bigrams（间隔二元组）
        :param text: 输入的中文文本
        :param max_skip: 允许的最大间隔词数，默认为4
        :return: skip-bigrams列表
        """
        words = list(utils.seg_depart(text))
        skip_bigrams = []
        for i in range(len(words)):
            for j in range(i + 1, min(i + max_skip + 1, len(words))):
                skip_bigram = words[i] + words[j]
                skip_bigrams.append(skip_bigram)
        return skip_bigrams

    @staticmethod
    def get_unigrams(text):
        """
        获取文本中的unigrams（一元组，即单个词语）
        :param text: 输入的中文文本
        :param: 无
        :return: unigrams列表
        """
        words = list(utils.seg_depart(text))
        return words

    @staticmethod
    def rouge_su(reference, candidate, beta=1.0):
        """
        计算ROUGE-SU指标
        :param reference: 参考中文文本（如参考摘要）
        :param candidate: 生成的中文文本（如生成摘要）
        :param beta: 权重参数，用于平衡skip-bigram和unigram的重要性，默认为1.0
        :return: ROUGE-SU得分
        """
        ref_skip_bigrams = EvaluateModel.get_skip_bigrams(reference)
        ref_unigrams = EvaluateModel.get_unigrams(reference)
        cand_skip_bigrams = EvaluateModel.get_skip_bigrams(candidate)
        cand_unigrams = EvaluateModel.get_unigrams(candidate)

        # 统计参考文本中skip-bigram和unigram的出现次数
        ref_skip_bigram_counts = Counter(ref_skip_bigrams)
        ref_unigram_counts = Counter(ref_unigrams)

        common_skip_bigrams = set(ref_skip_bigrams) & set(cand_skip_bigrams)
        common_unigrams = set(ref_unigrams) & set(cand_unigrams)

        skip_bigram_recall = sum([ref_skip_bigram_counts[sb] for sb in common_skip_bigrams]) / sum(
            ref_skip_bigram_counts.values())
        unigram_recall = sum([ref_unigram_counts[ug] for ug in common_unigrams]) / sum(ref_unigram_counts.values())

        # 根据beta值计算加权调和平均
        rouge_su_score = ((1 + beta ** 2) * skip_bigram_recall * unigram_recall) / (
                    beta ** 2 * skip_bigram_recall + unigram_recall) if (beta ** 2 * skip_bigram_recall + unigram_recall) > 0 else 0
        return rouge_su_score

# if __name__ == '__main__':
#     reference = "这是一个参考摘要，用于测试ROUGE-L指标的计算。"
#     candidate = "这是一个生成摘要，用于与参考摘要进行比较。"
#
#     rouge_l_score, lcs_str = calculate_rouge_l(reference, candidate)
#     print("ROUGE-L F-score:", rouge_l_score)
#     print("最长公共子序列：", lcs_str)
