from src.docxParser.Node import Node


class CompositeNode(Node):
    def __init__(self, type, content, textContent, intro):
        self.type = type
        super().__init__(type, '', text_content='\n'.join(textContent))
        self.content = content
        self.textContent = textContent
        self.content_intro = intro
        self.chosen = False

    def setChosen(self, boolean):
        self.chosen = boolean

    def getTextContent(self):
        return self.textContent

    def getTreeDic(self):
        treeDic = {}
        treeDic["type"] = self.__type
        treeDic["outLvl"] = self.__outLvl
        treeDic["score"] = self.__score
        treeDic["selected"] = self.__selected
        treeDic["part"] = self.__part_name
        treeDic["chosen"] = self.__chosen
        treeDic["content"] = self.content
        treeDic["textContent"] = self.textContent
        treeDic["intro"] = self.intro
        return treeDic
