import math


class PPTNode:
    content = ''
    children = []
    titles = []  # 多级标题： 1-xx 1.1-xx 1.1.1-xx
    top_title = ''
    origin_content = []

    class InnerNode:
        Type = -1
        content = ''

        def __init__(self, Type, content):
            self.Type = Type
            self.content = content

        def getDic(self):
            return {"type": self.Type, "content": self.content}

    def __init__(self, content, children, titles):
        self.content = content
        self.children = children
        self.titles = titles

    def getDic(self):
        return {"content": self.content, "children": self.children, "titles": self.titles, "top_title": self.top_title, "orgin_content": self.origin_content}

    def setTitles(self, titles):
        self.titles.append(titles)

    def getTitles(self):
        return self.titles

    def setOriginContent(self,origin_content):
        self.origin_content = origin_content

    def getOriginContent(self):
        return self.origin_content

    def setTopTitle(self, title):
        self.top_title = title

    def getTopTitle(self):
        return self.top_title

    def getContent(self):
        return self.content

    def getChildren(self):
        return self.children

    def getSlideCountByIndex(self, index):
        cnt_sentence = 0
        cnt_other = 0
        nodes = self.children[index]
        for node in nodes:
            if node["type"] == 2:
                cnt_sentence += 1
            else:
                cnt_other += 1

        return math.ceil(cnt_sentence / 4), cnt_other

    def addNode(self, nodetype, content):
        innerNode = PPTNode.InnerNode(nodetype, content)
        self.children.append(innerNode.getDic())
