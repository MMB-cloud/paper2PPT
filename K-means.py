import docx
import jieba
import string
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from common.Utils import Utils

utils = Utils()


def read_and_preprocess_word_doc(file_path):
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)

    text = " ".join(full_text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = utils.seg_depart(text)
    # stopwords_list = get_stopwords_list()
    # filtered_words = [word for word in words if word not in stopwords_list]

    return " ".join(words)


# def get_stopwords_list():
#    stopwords = ["的", "了", "是", "在", "我", "你", "他", "她", "它", "我们", "你们", "他们", "她们", "它们", "这",
#                 "那", "此", "个", "些", "和", "与", "及", "等", "就", "也", "又", "还", "再", "很", "非常", "十分",
#                 "太", "啊", "呀", "呢", "吧", "吗", "哦", "嗯"]
#    return stopwords


def extract_features(texts):
    vectorizer = CountVectorizer()
    count_matrix = vectorizer.fit_transform(texts)

    tfidf_transformer = TfidfTransformer()
    tfidf_matrix = tfidf_transformer.fit_transform(count_matrix)

    return tfidf_matrix


def cluster_documents(features, num_clusters):
    kmeans = KMeans(n_clusters=num_clusters)
    kmeans.fit(features)
    return kmeans.labels_


def plot_cluster_result(labels):
    unique_labels, label_counts = np.unique(labels, return_counts=True)
    plt.pie(label_counts, labels=unique_labels, autopct='%1.1f%%')
    plt.axis('equal')
    plt.title('Distribution of Clusters')
    plt.show()


def plot_silhouette_scores(features):
    k_values = range(2, 10)
    silhouette_scores = []

    for k in k_values:
        kmeans = KMeans(n_clusters=k)
        kmeans.fit(features)
        labels = kmeans.labels_
        silhouette_avg = silhouette_score(features, labels)
        silhouette_scores.append(silhouette_avg)

    plt.plot(k_values, silhouette_scores)
    plt.xlabel('Number of Clusters (k)')
    plt.ylabel('Silhouette Score')
    plt.title('Silhouette Score vs. Number of Clusters')
    plt.show()


if __name__ == '__main__':

    # 假设的中文论文Word文档路径列表
    word_document_paths = []
    for file in utils.get_file_paths(utils.getInputPath()):
        word_document_paths.append(file)
    num_clusters = 3

    texts = []
    for path in word_document_paths:
        preprocessed_text = read_and_preprocess_word_doc(path)
        texts.append(preprocessed_text)

    features = extract_features(texts)

    labels = cluster_documents(features, num_clusters)
    # plot_cluster_result(labels)
    plot_silhouette_scores(features)
    for i, label in enumerate(labels):
        print(f"Document {i}: Cluster {label}")
