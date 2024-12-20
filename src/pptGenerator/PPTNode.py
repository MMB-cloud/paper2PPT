import math


class PPTNode:
    content = ''
    children = []
    title = ''

    class InnerNode:
        Type = -1
        content = ''

        def __init__(self, Type, content):
            self.Type = Type
            self.content = content

        def getDic(self):
            return {"type": self.Type, "content": self.content}

    def __init__(self, content, children):
        self.content = content
        self.children = children

    def getDic(self):
        return {"content": self.content, "children": self.children}

    def setTitle(self, title):
        self.title = title

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
