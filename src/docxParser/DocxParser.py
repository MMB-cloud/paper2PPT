import zipfile
import re

from src.docxParser.DocxTree import DocxTree
from src.docxParser.Node import Node
from common.Utils import Utils

utils = Utils()

class DocxParser:
    def __init__(self):
        pass

    def parseDocx(self, file_path, output_dir_path=''):
        # 1. 文件解压缩
        z = zipfile.ZipFile(file_path)

        # 2. 提取样式信息
        styleInf = z.read("word/styles.xml").decode().split("<w:style w:type=\"paragraph\" ")
        styleIds = [""]
        styleBaseon = [""]
        styleOutLvl = [""]
        styleNum = len(styleInf)
        for i in range(1, styleNum):
            styleInf[i] = styleInf[i].split("</w:style>")[0]
            styleIds.append(styleInf[i].split("w:styleId=\"")[1].split("\"")[0])
            if styleInf[i].find("<w:basedOn w:val=\"") > 0:
                styleBaseon.append(
                    styleInf[i].split("<w:basedOn w:val=\"")[1].split("\"")[0])
            else:
                styleBaseon.append("")
            if styleInf[i].find("<w:outlineLvl w:val=\"") > 0:
                styleOutLvl.append(
                    styleInf[i].split("<w:outlineLvl w:val=\"")[1].split("\"")[0])
            else:
                styleOutLvl.append("")
        baseDic = dict(zip(styleIds, styleBaseon))
        outLvlDic = dict(zip(styleIds, styleOutLvl))
        for i in range(1, styleNum):
            if len(styleOutLvl[i]) == 0:
                while len(styleBaseon[i]) > 0:
                    styleBaseon[i] = baseDic[styleBaseon[i]]
                    styleOutLvl[i] = outLvlDic[styleBaseon[i]]
                    if len(styleOutLvl[i]) > 0:
                        break
        outLvlDic = dict(zip(styleIds, styleOutLvl))

        # styleOutLvl去重、排序
        styleOutLvl = list(set(styleOutLvl))
        lst = []
        for outLvl in styleOutLvl:
            if outLvl != '':
                lst.append(int(outLvl))
        lst = sorted(lst)
        newStyleOutLvl = []
        for outLvl in lst:
            newStyleOutLvl.append(str(outLvl))
        newStyleOutLvl.append('')
        styleOutLvl = newStyleOutLvl

        # 3.识别文本段落、表格和图像
        # 3.1 获取document.xml中的<w:body>部分
        document_content = z.read("word/document.xml").decode("utf-8")
        body_content = "<w:body>" + re.split("<w:body>|</w:body>", document_content)[1] + "</w:body>"
        # 3.2 <w:p>与<w:tbl>的分割
        list1 = re.split("<w:tbl>|</w:tbl>", body_content)
        list2 = []
        for i in range(len(list1)):
            if i % 2 == 0:
                list2.append(list1[i])
            else:
                list2.append("<w:tbl>" + list1[i] + "</w:tbl>")
        # 3.3 <w:p>内部的分割与过滤
        contentList = []
        for content in list2:
            if content.startswith("<w:tbl>"):
                contentList.append(content)
            else:
                list3 = re.split("<w:p |</w:p>", content)
                for paraContent in list3[: -1]:
                    if "</w:t>" in paraContent or "<w:pict" in paraContent or "<w:drawing" in paraContent:
                        contentList.append("<w:p " + paraContent + "</w:p>")
        # 3.4 将xml字符串转为nodeList
        nodeList = []
        for content in contentList:
            if content.startswith("<w:tbl>"):
                node = Node(type=3, outLvl='', xml_content=content)
                #print(content)
                nodeList.append(node)
                # print(node.getXmlContent())
                # for row in node.getTableData():
                #     print(str(row))
                # print()
            else:
                if "<w:pict" in content or "<w:drawing" in content:
                    node = Node(type=4, outLvl='', xml_content=content)
                    nodeList.append(node)
                #公式节点
                if "<m:oMath>" in content or "<o:OLEObject" in content:
                    node = Node(type=5, outLvl='', xml_content=content)
                    nodeList.append(node)
                else:
                    outLvl = ""
                    if "w:pStyle w:val=" in content:
                        styleStr = content[content.find("w:pStyle w:val="): ].split("/>")[0]
                        styleId = styleStr.split("\"")[1] if len(styleStr.split("\"")) > 1 else ""
                        outLvl = outLvlDic[styleId] if styleId in outLvlDic else ""
                    if outLvl != "":
                        node = Node(type=0, outLvl=outLvl, xml_content=content)
                        nodeList.append(node)
                    else:
                        # 创建段落节点
                        node = Node(type=1, outLvl='', xml_content=content)
                        nodeList.append(node)
        # 3.5 将nodeList转化为docxTree
        docxTree = DocxTree(file_path, output_dir_path)
        docxTree.setChildren(nodeList)
        docxTree.getTreeDic()
        # 3.6 将过滤后的文档内容输出到word文档中
        destz = zipfile.ZipFile(output_dir_path + "\\" + "未压缩.docx", "w", compression=zipfile.ZIP_DEFLATED)
        nodeList = docxTree.getNodeList()
        body_xml_content = "<w:body>"
        for node in nodeList:
            body_xml_content = body_xml_content + node.getXmlContent()
        body_xml_content = body_xml_content + "</w:body>"
        document_xml_content = ""
        list4 = re.split("<w:body>|</w:body>", document_content)
        document_xml_content = list4[0] + body_xml_content + list4[2]
        for filename in z.namelist():
            if filename == "word/document.xml":
                destz.writestr(filename, document_xml_content)
            else:
                # print(filename)
                if filename.endswith(".xml"):
                    destz.writestr(filename, z.read(filename).decode())
                else:
                    destz.writestr(filename, z.read(filename))
        destz.close()
        z.close()
        # 3.7 返回构建好的文档树
        return docxTree



# if __name__=="__main__":
#     file_path = utils.getUserPath() + "\input" + "\互联网金融、利率市场化与商业银行盈利能力的实证研究.docx"
#     output_dir_path = utils.getUserPath() + "\output" + "\互联网金融、利率市场化与商业银行盈利能力的实证研究"
#     docxParser = DocxParser()
#     docxParser.parseDocx(file_path, output_dir_path)
                    