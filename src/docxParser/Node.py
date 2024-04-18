import re

from Utils import Utils

utils = Utils()

class Node:
    """
    :param type: 节点类型
    :param outLvl: 节点的层级，除章节节点外，其它节点的值均为''
    :param xml_content: 节点在document.xml中的字符串内容，句子节点的xml_content为''
    :param text_content: 句子节点独有，代表句子的文本内容
    :wt_start: 句子节点独有，对应<w:t>列表的起始索引
    :wt_end: 句子节点独有，对应<w:t>列表的结束索引
    """
    def __init__(self, type, outLvl, xml_content='', text_content='', wt_start=-1, wt_end=-1) -> None:
        # type=0: 章节
        # type=1: 段落
        # type=2: 句子
        # type=3: 表格
        # type=4: 图像
        # type=5: 公式
        self.__type = type  # 节点的类别
        self.__outLvl = outLvl  # 节点的大纲级别
        self.__xml_content = xml_content    # 节点对应的xml内容
        self.__score = 0.0      # 节点内容的权重评分
        self.__selected = False     # 节点内容是否被保留
        self.__parent = None    # 节点的父节点
        self.__ancestors = []   # 节点的祖先节点列表
        # self.__position = []    # 节点的位置向量

        
        if type == 3:   # 如果是表格节点，需要获取表格数据
            list1 = re.split("<w:tr>|</w:tr>", xml_content)
            table_rows_xml = []
            table_rows_text = []
            for list1_xml_content in list1[1:]:
                if "<w:tc>" in list1_xml_content or "</w:tc>" in list1_xml_content:
                    table_rows_xml.append("<w:tr>" + list1_xml_content + "</w:tr>")
            for table_row_xml in table_rows_xml:
                list2 = re.split("<w:tc>|</w:tc>", table_row_xml)
                table_cells_xml = []
                table_cells_text = []
                for i in range(len(list2)):
                    if i % 2 != 0:
                        table_cells_xml.append("<w:tc>" + list2[i] + "</w:tc>")
                for table_cell_xml in table_cells_xml:
                    spanVal = 1
                    if "<w:tcPr>" in table_cell_xml:
                        tcPr = "<w:tcPr>" + re.split("<w:tcPr>|</w:tcPr>", table_cell_xml)[1] + "</w:tcPr>"
                        if "<w:gridSpan w:val=" in tcPr:
                            spanVal = int(tcPr.split("<w:gridSpan w:val=\"")[1].split("\"")[0])
                    table_cell_text = ''
                    if table_cell_xml.find("<w:t>") or table_cell_xml.find("</w:t>"):
                        list3 = re.split("<w:t>|<w:t xml:space=\"preserve\":</w:t>", table_cell_xml)
                        for i in range(len(list3)):
                            if i % 2 != 0:
                                table_cell_text = table_cell_text + list3[i]
                    for i in range(0, spanVal):
                        if i == 0:
                            table_cells_text.append(table_cell_text)
                        else:
                            table_cells_text.append("")
                if len(table_cells_text) != 0:
                    table_rows_text.append(table_cells_text)
            self.__tableData = table_rows_text
        elif type == 4:     # 图像节点，不需要做处理
            pass
        elif type == 5:     # 公式节点，区分下标，m:sub是下标
            pass
        elif type == 1:     # 如果是段落节点，需要实现 1.分句   2. 获取run文字列表
            self.__wtlist = []      # <w:t></w:t>标签中的文本内容
            self.__children = []    # 子节点都是句子节点
            self.__length = 0       # 句子总字符长度
            # 提取wtlist
            list4 = re.split("<w:t>|<w:t xml:space=\"preserve\">|</w:t>", xml_content)
            for i in range(len(list4)):
                if i % 2 != 0:
                    self.__wtlist.append(list4[i])
            # 判断段落里面是否存在句号
            indexs = []
            for i in range(len(self.__wtlist)):
                if "。" in self.__wtlist[i]:
                    num = self.__wtlist[i].count("。")
                    for j in range(num):
                        indexs.append(i)
            if len(indexs) <= 1:
                wt_start = 0
                wt_end = len(self.__wtlist) - 1
                text_content = "".join(self.__wtlist)
                node = Node(type=2, outLvl='', xml_content='', text_content=text_content, wt_start=wt_start, wt_end=wt_end)
                node.setParent(self)
                self.__children.append(node)
            else:
                # 根据句号进行句子划分
                text_content = ""
                wt_start = -1
                wt_end = -1
                for i in range(len(self.__wtlist)):
                    wt = self.__wtlist[i]
                    if "。" in wt:  # 特殊处理
                        num = wt.count("。")    # 一个wt可能包含多个句子的部分文本内容
                        """
                        一个句号划分为两段文本
                        两个句号换分为三段文本
                        三个句号换分为四段文本
                        ....
                        """
                        text_list = wt.split("。")
                        for j in range(0, num+1):
                            if j == 0:  # 最前的文本内容是一个句子的末尾部分
                                text_content = text_content + text_list[j] + "。"
                                wt_end = i
                                # 生成node节点
                                node = Node(type=2, outLvl='', xml_content='', text_content=text_content, wt_start=wt_start, wt_end=wt_end)
                                node.setParent(self)
                                self.__children.append(node)
                                # 重置
                                text_content = ""
                                wt_start = i
                                wt_end = -1
                            elif j == num:  # 最后的内容是后一个的开始，如果内容为空，则不作处理
                                if text_list[j] == "":
                                    pass
                                else:
                                    text_content = text_list[j]
                                    wt_start = i
                            else:   # 存在句子的所有文本内容都在这个wt里面
                                text_content = text_content + text_list[j] + "。"
                                wt_start = i
                                wt_end = i
                                node = Node(type=2, outLvl='', xml_content='', text_content=text_content, wt_start=wt_start, wt_end=wt_end)
                                node.setParent(self)
                                self.__children.append(node)
                                # 重置
                                text_content = ""
                                wt_start = i
                                wt_end = -1
                    else:
                        if text_content == "":
                            wt_start = i
                        text_content = text_content + wt
        elif type == 0:     # 章节节点
            list5 = re.split("<w:t>|<w:t xml:space=\"preserve\">|</w:t>", xml_content)
            textList = []
            for i in range(len(list5)):
                if i % 2 != 0:
                    textList.append(list5[i])
            textContent = ''.join(textList)
            self.__text_content = textContent
            self.__children = []
            self.__leafnodes = []
            self.__length = 0
        elif type == 2:     # 句子节点
            self.__text_content = text_content
            self.__length = 0
            self.__wt_start = wt_start
            self.__wt_end = wt_end

    def setChildren(self, nodeList):
        if self.getType() == 0:
            outLvl_next = ''
            for node in nodeList:
                if node.getOutLvl() == str(int(self.__outLvl) + 1):
                    outLvl_next = str(int(self.__outLvl) + 1)
            if outLvl_next == "":   # 段落节点、表格节点或图像节点
                for node in nodeList:
                    self.__children.append(node)
                    node.setParent(self)
            else:
                indexs = []
                for node in nodeList:
                    if node.getOutLvl() == outLvl_next:
                        indexs.append(nodeList.index(node))
                if indexs[0] != 0:
                    for node in nodeList[: indexs[0]]:
                        self.__children.append(node)
                        node.setParent(self)
                for i in range(len(indexs)):
                    if i == len(indexs) - 1:
                        nodeList[indexs[i]].setChildren(nodeList[indexs[i]+1: ])
                    else:
                        nodeList[indexs[i]].setChildren(nodeList[indexs[i]+1: indexs[i+1]])
                    nodeList[indexs[i]].setParent(self)
                    self.__children.append(nodeList[indexs[i]])


    def getChildren(self):
        if self.__type not in [0, 1]:
            return
        return self.__children


    def getTreeDic(self):
        treeDic = {}
        treeDic["type"] = self.__type
        treeDic["outLvl"] = self.__outLvl
        treeDic["score"] = self.__score
        treeDic["selected"] = self.__selected
        if self.__type == 0:
            treeDic["text_content"] = self.__text_content
            treeDic["children"] = []
            for child in self.__children:
                treeDic["children"].append(child.getTreeDic())
        elif self.__type == 1:
            treeDic["children"] = []
            for child in self.__children:
                treeDic["children"].append(child.getTreeDic())
        elif self.__type == 2:
            treeDic["text_content"] = self.__text_content
        elif self.__type == 3:
            treeDic["table_data"] = str(self.__tableData)
        elif self.__type == 4:
            pass
        return treeDic

    def getCompressedTreeDic(self):
        compressedTreeDic = {}
        if self.__selected:
            compressedTreeDic["type"] = self.__type
            compressedTreeDic["outLvl"] = self.__outLvl
            compressedTreeDic["score"] = self.__score
            compressedTreeDic["selected"] = self.__selected
            if self.__type == 0:    # 章节节点
                compressedTreeDic["text_content"] = self.__text_content
                compressedTreeDic["children"] = []
                for child in self.__children:
                    if len(child.getCompressedTreeDic()) != 0:
                        compressedTreeDic["children"].append(child.getCompressedTreeDic())
            elif self.__type == 1:      # 段落节点
                compressedTreeDic["children"] = []
                for child in self.__children:
                    if len(child.getCompressedTreeDic()) != 0:
                        compressedTreeDic["children"].append(child.getCompressedTreeDic())
            elif self.__type == 2:
                compressedTreeDic["text_content"] = self.__text_content
            elif self.__type == 3:
                compressedTreeDic["table_data"] = str(self.__tableData)
            elif self.__type == 4:
                pass
        return compressedTreeDic


    def getNodeList(self):
        nodeList = []
        #如果是章节节点
        if self.__type == 0:
            nodeList.append(self)
            for child in self.__children:
                #次级章节
                if child.getType() == 0:
                    nodeList.extend(child.getNodeList())
                #段落节点
                else:
                    nodeList.append(child)
        return nodeList

    def getNodeListByType(self,type):
        nodeList = []
        if self.__type == type:
            nodeList.append(self)
            for child in self.__children:
                if child.getType() == type:
                    nodeList.extend(child.getNodeListByType())
                else:
                    nodeList.append(child)
        return nodeList

    def getFirstSentInNode(self):
        firSentLst = []
        #如果type = 1则是段落节点，返回子节点的第一个
        if self.__type == 1:
            if self.__children and self.__children[0].getSelected() == False:
                #for child in self.__children:
                firSentLst.append(self.__children[0].getTextContent())
                self.__children[0].setSelected(True)
                return firSentLst
        #如果type = 2则是句子节点，返回self
        if self.__type == 2:
            firSentLst.append(self.__children[1].getTextContent())
            self.__children[1].setSelected(True)
            return firSentLst
        #type = 0,段落节点，递归
        if self.__type == 0:
            for node in self.__children:
                firSentLst.append(node.getFirstSentInNode())
            return firSentLst







    def getSelectedNodeList(self):
        selectedNodeList = []
        if self.__type == 0:
            if self.__selected:
                selectedNodeList.append(self)
                for child in self.__children:
                    selectedNodeList.extend(child.getSelectedNodeList())
        elif self.__type == 1:  # 段落节点
            if self.__selected:
                # 句子节点没有被选中的，其对应的<w:t>里面的内容需要替换为空
                replaceList = {}    # 替换字典 {oldStr: newStr}
                for child in self.__children:
                    if child.getSelected():
                        pass
                    else:
                        # 获取该child对应的wt_list
                        wt_start = child.getwtstart()
                        wt_end = child.getwtend()
                        oldStr = ""     # 即将被替换的文本内容
                        newStr = ""     # 替换的新内容
                        # 根据start和end替换xml内容
                        if wt_start == wt_end:  # 句子的所有内容都在一个<w:t>下面
                            oldStr = self.__wtlist[wt_start]
                            newStr = "".join(self.__wtlist[wt_start].split(child.getTextContent()))
                            replaceList["<w:t>" + oldStr + "</w:t>"] = "<w:t>" + newStr + "</w:t>"
                            replaceList['<w:t xml:space=\"preserve\">' + oldStr + "</w:t>"] = '<w:t xml:space=\"preserve\">' + newStr + "</w:t>"
                            self.__wtlist[wt_start] = newStr
                        else:
                            for i in range(wt_start, wt_end + 1):
                                wt = self.__wtlist[i]
                                if wt == "。":
                                    replaceList["<w:t>。</w:t>"] = "<w:t></w:t>"
                                    replaceList['<w:t xml:space=\"preserve\">。</w:t>'] = '<w:t xml:space=\"preserve\"></w:t>'
                                else:
                                    if i == wt_start:
                                        if "。" in wt:
                                            # newStr为去掉。后剩余的内容
                                            oldStr = wt
                                            if wt.count("。") == 1:
                                                newStr = wt.split("。")[0] + "。"
                                            else:
                                                newStr = "。".join(wt.split("。"))[: -1]
                                        else:
                                            # newStr继续保持为空
                                            oldStr = wt
                                            newStr = ""
                                    elif i == wt_end:
                                        if "。" in wt:
                                            # newStr为去掉。的前面后剩余的内容
                                            oldStr = wt
                                            if wt.count("。") == 1:
                                                newStr = wt.split("。")[1]
                                            else:
                                                newStr = "。".join(wt.split("。")[1: ])
                                        else:
                                            # newStr继续保持为空
                                            oldStr = wt
                                            newStr = ""
                                    else:
                                        # newStr继续保持为空
                                        oldStr = wt
                                        newStr = ""
                                self.__wtlist[i] = newStr
                                replaceList["<w:t>" + oldStr + "</w:t>"] = "<w:t>" + newStr + "</w:t>"
                                replaceList['<w:t xml:space=\"preserve\">' + oldStr + "</w:t>"] = '<w:t xml:space=\"preserve\">' + newStr + "</w:t>"
                # xml内容替换
                for oldXml in replaceList:
                    self.__xml_content = self.__xml_content.replace(oldXml, replaceList[oldXml])
                selectedNodeList.append(self)
        elif self.__type == 3:
            if self.__selected:
                selectedNodeList.append(self)
        elif self.__type == 4:
            if self.__selected:
                selectedNodeList.append(self)
        return selectedNodeList

    
    def getwtstart(self):
        if self.__type == 2:
            return self.__wt_start
        return

    
    def getwtend(self):
        if self.__type == 2:
            return self.__wt_end
        return


    def getleafnodes(self):
        if self.__type == 0:
            if len(self.__leafnodes) != 0:
                return self.__leafnodes
            else:
                for child in self.__children:
                    if child.getType() == 0:
                        self.__leafnodes.extend(child.getleafnodes())
                    elif child.getType() == 1:  # 段落节点的子节点即为句子节点
                        self.__leafnodes.extend(child.getChildren())
        return self.__leafnodes


    
    # 获取当前文档数下指定层级的章节节点
    def gettreenodes(self, outLvl):
        treenodes = []
        if self.__type != 0 or int(self.__outLvl) >= int(outLvl):
            return []
        else:
            for child in self.__children:
                if child.getType() == 0:

                    if child.getOutLvl() == str(outLvl):
                        treenodes.append(child)
                    else:
                        treenodes.append(child.gettreenodes(outLvl))
        return treenodes

        # 获取当前文档数下指定层级的章节节点

    def getTreenodes(self, outLvl):
        treenodes = []
        if self.__type != 0 or int(self.__outLvl) >= int(outLvl):
            return []
        else:
            for child in self.__children:
                if child.getType() == 0:
                    if child.getOutLvl() == str(outLvl):
                        treenodes.append(child)
                    else:
                        treenodes.extend(child.getTreenodes(outLvl))
        return treenodes


    def setSelected(self, selected):
        self.__selected = selected

    
    def getSelected(self):
        return self.__selected

    
    def setScore(self, score):
        self.__score = score


    def getScore(self):
        return self.__score


    def setParent(self, node):
        self.__parent = node


    def getParent(self):
        return self.__parent


    def getTableData(self):
        if self.__type != 3:
            return
        else:
            return self.__tableData


    def getOutLvl(self):
        return self.__outLvl


    def getType(self):
        return self.__type


    def getTextContent(self):
        if self.__type not in [0, 2]:
            return
        else:
            return self.__text_content


    def getXmlContent(self):
        return self.__xml_content


    def getAncestors(self):
        if self.__outLvl == '0':    # 最顶级的一级章节
            return self.__ancestors
        else:
            if len(self.__ancestors) != 0:
                return self.__ancestors
            else:
                self.__ancestors.append(self.__parent)
                self.__ancestors.extend(self.__parent.getAncestors())
                return self.__ancestors

        
    """获取当前节点下的所有句子的字符串总长度"""
    def getLength(self):
        if self.__type not in [0, 1, 2]:
            return 0
        if self.__length != 0:
            return self.__length
        else:
            if self.__type == 0:
                for child in self.getChildren():
                    self.__length += child.getLength()
                self.__length += len(self.__text_content)
            elif self.__type == 1:
                for child in self.getChildren():
                    self.__length += child.getLength()
            elif self.__type == 2:
                self.__length = len(self.__text_content)

            return self.__length

    
    """专门针对摘要章节，清除所有的权重"""
    def clearScore(self):
        self.__score = 0.0
        self.__final_score = 0.0
        if self.__type in [0, 1]:
            for child in self.__children:
                child.clearScore()


    """直接找到最底层的章节节点集合"""
    def getLowerTreeNodes(self):
        if self.__type != 0:
            return
        treenodes = []
        notFound = True     # 判断子节点中是否存在章节节点
        for child in self.__children:
            if child.getType() == 0:
                treenodes.extend(child.getLowerTreeNodes())
                notFound = False
        if notFound:    # 当前章节节点下没有章节节点，即当前章节节点为最底层的章节节点
            treenodes.append(self)
        return treenodes



    """
    找到图表、图表标题以及对它们进行解释说明的句子，确定一个句子是对图表进行解释说明的规则有如下:
        1. 对图表编号的引用
        2. 对表格中文本和数据进行引用
        3. 提示词
        4. 与图表标题的词语重叠度
    """
    # def getImages(self):
    #     if self.getOutLvl() != "0":
    #         return
    #     imageMatrix = []        # 图像二维矩阵 [[图节点, 图标题节点, [描述性句子节点集合], [位置向量]]]
        
    #     # 图像，图标题节点和描述性句子节点集合都在最底层的章节下，因此，先找到最底层的章节节点集合
    #     for treenode in self.getLowerTreeNodes():
    #         children = treenode.getChildren()
    #         for i in range(len(children)):      # 遍历子节点
    #             if children[i].getType() == 4:      # 找到图像节点
    #                 if children[i+1].getType() == 1 and children[i+1].getChildren()[0].getTextContent().startswith("图"):   # 找到图标题段落节点
    #                     heading_text = children[i+1].getChildren()[0].getTextContent()  # 图标题的文本内容
    #                     image_index = "图"      # 图编号, 如"图3-1"
    #                     str_list = list(heading_text)   # 先将图标题转为字符列表 ["图", "3", "-", "1"]
    #                     for str in str_list[1: ]:
    #                         # 判断str是否为中文
    #                         if utils.check_chinese(str):    # 如果是中文就停止
    #                             break
    #                         else:
    #                             image_index = image_index + str
    #                     image_index = image_index.replace(" ", "")
    #                     leafnodes = []  # 图像的描述性句子的集合
    #                     for j in range(len(children)):
    #                         if children[j].getType() == 1:  # 找到段落节点
    #                             if len(children[j].getChildren()) == 1 and children[j].getChildren()[0].getTextContent().startswith("图"):  # 与图标题进行区分
    #                                 pass
    #                             else:
    #                                 for child in children[j].getChildren():  # 遍历段落节点中的子节点
    #                                     # 判断是否有对图编号的引用
    #                                     if image_index in child.getTextContent():
    #                                         leafnodes.append(child)
    #                                     else:
    #                                         # 单词重叠度
    #                                         leafnode_seg_list = utils.seg_depart(child.getTextContent())
    #                                         heading_seg_list = utils.seg_depart(heading_text)
    #                                         overlap_wordlist = list(set(heading_seg_list).intersection(set(leafnode_seg_list)))
    #                                         overlap = float(len(overlap_wordlist))/float(len(heading_seg_list))
    #                                         if overlap >= 0.5:
    #                                             leafnodes.append(child)
    #                                         else:
    #                                             # 判断是否存在提示词
    #                                             if "如图所示" in children.getTextContent() or "如上图" in children.getTextContent() or "如下图" in children.getTextContent():
    #                                                 leafnodes.append(child)
    #                     # 图像二维矩阵添加
    #                     imageMatrix.append([children[i], children[i+1], leafnodes, children[i].getPosition()])
    #                 else:   # 找不到图标题
    #                     imageMatrix.append([children[i], None, [], children[i].getPosition()])
    #     return imageMatrix


    """
    找到章节下的图像内容，以及对它们进行解释说明的句子，确定一个句子是对图表进行解释说明的规则有如下:
        1. 对图表编号的引用
        2. 对表格中文本和数据进行引用
        3. 提示词
        4. 与图表标题的词语重叠度
    """
    def getImages(self):
        imageMatrix = []        # 图像二维矩阵 [[图节点, 图标题节点, [描述性句子节点集合], [位置向量]]]

        for i in range(len(self.__children)):   # 遍历子节点
            if self.__children[i].getType() == 4:   # 找到图像节点
                if self.__children[i+1].getType() == 1 and self.__children[i+1].getChildren()[0].getTextContent().startswith("图"): # 找到图标题段落节点
                    heading_text = self.__children[i+1].getChildren()[0].getTextContent()   # 图标题的文本内容
                    image_index = "图"  # 图编号    如 "图3-1"
                    str_list = list(heading_text)   # 先将图标题转为字符列表 ["图", "3", "-", "1"]
                    for str in str_list[1: ]:
                        # 判断str是否为中文
                        if utils.check_chinese(str):    # 如果是中文就停止
                            break
                        else:
                            image_index = image_index + str
                    image_index = image_index.replace(" ", "")
                    leafnodes = []  # 图像的描述性句子的集合
                    for j in range(len(self.__children)):
                        if self.__children[j].getType() == 1:   # 找到段落节点
                            if len(self.__children[j].getChildren()) == 1 and self.__children[j].getChildren()[0].getTextContent().startswith("图"):    # 与图标题进行区分
                                pass
                            else:
                                for child in self.__children[j].getChildren():  # 遍历段落节点中的子节点
                                    # 判断是否有对图编号的引用
                                    if image_index in child.getTextContent():
                                        leafnodes.append(child)
                                    else:
                                        # 单词重叠度
                                        leafnodes_seg_list = utils.seg_depart(child.getTextContent())
                                        heading_seg_list = utils.seg_depart(heading_text)
                                        overlap_wordlist = list(set(heading_seg_list).intersection(set(leafnodes_seg_list)))
                                        overlap = float(len(overlap_wordlist))/float(len(heading_seg_list))
                                        if overlap >= 0.5:
                                            leafnodes.append(child)
                                        else:
                                            # 判断是否存在提示词
                                            if "如图所示" in child.getTextContent() or "如上图" in child.getTextContent() or "如下图" in child.getTextContent():
                                                leafnodes.append(child)
                    # 图像二维矩阵添加
                    imageMatrix.append([self.__children[i], self.__children[i+1], leafnodes])
                else:   # 找不到图标题
                    imageMatrix.append([self.__children[i], None, []])
        return imageMatrix



    
    """找到表标题、以及描述它们的句子"""
    # def getTables(self):     
    #     tableMatrix = []    # 表格二维矩阵 [[表格节点, 表标题节点, [描述性句子]]]

        
    #     # 表格，表标题节点和描述性句子节点集合都在最底层的章节下，因此，找到最底层的章节节点集合
    #     for treenode in self.getLowerTreeNodes():
    #         children = treenode.getChildren()
    #         for i in range(len(children)):      # 遍历子节点
    #             if children[i].getType() == 3:  # 找到表格节点
    #                 if children[i-1].getType() == 1 and children[i-1].getChildren()[0].getTextContent().startswith("表"):
    #                     heading_text = children[i+1].getChildren()[0].getTextContent()
    #                     table_index = "表"  # 表编号，如“表3-1”
    #                     str_list = list(heading_text)   # 先将表标题转为字符列表 ["表", "3", "-", "1"]
    #                     for str in str_list[1: ]:
    #                         # 判断str是否为中文
    #                         if utils.check_chinese(str):    # 如果是中文就停止
    #                             break
    #                         else:
    #                             table_index = table_index + str
    #                     table_index = table_index.replace(" ", "")
    #                     leafnodes = []  # 表格的描述性句子的集合
    #                     for j in range(len(children)):
    #                         if children[j].getType() == 1:  # 找到段落节点
    #                             if len(children[j].getChildren()) == 1 and children[j].getChildren()[0].getTextContent().startswith("表"):
    #                                 pass
    #                             else:
    #                                 for child in children[j].getChildren():     # 遍历段落节点
    #                                     # 判断是否有对表编号的引用
    #                                     if table_index in child.getTextContent():
    #                                         leafnodes.append(child)
    #                                     else:
    #                                         # 对表格中的文本内容和数据的引用
    #                                         matched = False # 引用了
    #                                         for row_data in children[i].getTableData():
    #                                             for cell_data in row_data:
    #                                                 if cell_data != "" and cell_data in child.getTextContent():
    #                                                     matched = True
    #                                                     break
    #                                         if matched:
    #                                             leafnodes.append(child)
    #                                         else:
    #                                             # 判断是否存在提示词
    #                                             if "如下表" in child.getTextContent() or "如上表" in child.getTextContent():
    #                                                 leafnodes.append(child)
    #                     # 表格二维矩阵添加
    #                     tableMatrix.append([children[i], children[i-1], leafnodes, children[i].getPosition()])
    #                 else:   # 找不到表标题
    #                     tableMatrix.append([children[i], None, [], children.getPosition()])
    #     return tableMatrix


    """找到表标题、以及描述它们的句子"""
    def getTables(self):
        tableMatrix = []    # 表格二维矩阵 [[表格节点, 表标题节点, [描述性句子]]]

        for i in range(len(self.__children)):   # 遍历子节点
            if self.__children[i].getType() == 3:  # 找到表格节点
                if self.__children[i-1].getType() == 1 and self.__children[i-1].getChildren()[0].getTextContent().startswith("表"):
                    heading_text = self.__children[i-1].getChildren()[0].getTextContent()
                    table_index = "表"  # 表编号 如"表3-1"
                    str_list = list(heading_text)   # 先将表标题转为字符列表 ["表", "3", "-", "1"]
                    for str in str_list[1: ]:
                        # 判断str是否为中文
                        if utils.check_chinese(str):    # 如果是中文就停止
                            break
                        else:
                            table_index = table_index + str
                    table_index = table_index.replace(" ", "")
                    leafnodes = []  # 表格的描述性句子的集合
                    for j in range(len(self.__children)):
                        if self.__children[j].getType() == 1:   # 找到段落节点
                            if len(self.__children[j].getChildren()) == 1 and self.__children[j].getChildren()[0].getTextContent().startswith("表"):
                                pass
                            else:
                                for child in self.__children[j].getChildren():      # 遍历段落节点
                                    # 判断是否有对表编号的引用
                                    if table_index in child.getTextContent():
                                        leafnodes.append(child)
                                    else:
                                        # 对表格中的文本内容和数据的引用
                                        matched = False # 引用了
                                        for row_data in self.__children[i].getTableData():
                                            for cell_data in row_data:
                                                if cell_data != "" and cell_data in child.getTextContent():
                                                    matched = True
                                                    break
                                        if matched:
                                            leafnodes.append(child)
                                        else:
                                            # 判断是否存在提示词
                                            if "如下表" in child.getTextContent() or "如上表" in child.getTextContent():
                                                leafnodes.append(child)
                    # 表格二维矩阵添加
                    tableMatrix.append([self.__children[i], self.__children[i-1], leafnodes])
                else:   # 找不到表标题
                    tableMatrix.append([self.__children[i], None, []])
        return tableMatrix






    """构建用于整数线性规划的单元列表"""
    # def getUnitMatrix(self):    # 只能用于一级标题
    #     if self.__outLvl != "0":
    #         return
    #     # [[文本块句子集合, 图表块集合]]
    #     # 文本块句子集合 = [句子1, 句子2, 句子3, ..., 句子n]
    #     # 图标快集合 = [图表节点, 图表标题节点, 描述性句子集合]
    #     unitMatrix = []     # 单元列表
    #     tableMatrix = self.getTables()  # 表格矩阵
    #     imageMatrix = self.getImages()  # 图像矩阵
    #     table_image_leafnodes = []
    #     for tableArray in tableMatrix:
    #         if len(tableArray[2]) != 0:
    #             table_image_leafnodes = list(set(table_image_leafnodes).union(set(tableArray[2])))
    #     for imageArray in imageMatrix:
    #         if len(imageArray[2]) != 0:
    #             table_image_leafnodes = list(set(table_image_leafnodes).union(set(imageArray[2])))
    #     para_leafnodes = list(set(self.__leafnodes).difference(set(table_image_leafnodes)))
    #     unitMatrix = [para_leafnodes, tableMatrix, imageMatrix]
    #     return unitMatrix

    """构建用于整数线性规划的单元列表"""
    def getUnitMatrix(self):
        # [[文本块句子集合, 图表块集合]]
        # 文本块句子集合 = [句子1, 句子2, 句子3, ..., 句子n]
        # 图表块集合 = [图表节点, 图表标题节点, 描述性句子集合]
        unitMatrix = []     # 单元列表
        exist = False   # 章节下是否存在图表
        tableMatrix = self.getTables()  # 表格矩阵
        imageMatrix = self.getImages()  # 图像矩阵
        table_image_leafnodes = []
        if len(tableMatrix) != 0:
            exist = True
            for tableArray in tableMatrix:
                if len(tableArray[2]) != 0:
                    table_image_leafnodes = list(set(table_image_leafnodes).union(set(tableArray[2])))
        if len(imageMatrix) != 0:
            exist = True
            for imageArray in imageMatrix:
                if len(imageArray[2]) != 0:
                    table_image_leafnodes = list(set(table_image_leafnodes).union(set(imageArray[2])))
        para_leafnodes = list(set(self.__leafnodes).difference(set(table_image_leafnodes)))
        unitMatrix = [para_leafnodes, tableMatrix, imageMatrix]
        return unitMatrix, exist





                                


                                



    
                

                                

