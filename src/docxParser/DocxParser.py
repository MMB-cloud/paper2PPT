import zipfile
import re
import docx
import os

from src.docxParser.DocxTree import DocxTree
from src.docxParser.Node import Node
from common.Utils import Utils
from datetime import datetime

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
                # print(content)
                nodeList.append(node)
                # print(node.getXmlContent())
                # for row in node.getTableData():
                #     print(str(row))
                # print()
            else:
                if ("<w:pict" in content or "<w:drawing" in content) and "r:embed" in content:
                    node = Node(type=4, outLvl='', xml_content=content)
                    nodeList.append(node)
                # 公式节点
                # TODO 公式节点前还有文字说明，需要进一步细化，标志词前的算作node节点，分隔符中间的内容作为type5的node
                if "<m:oMath>" in content or "<o:OLEObject" in content:
                    # 收集公式节点
                    list4 = re.split(r'<m:oMath>(.*?)</m:oMath>', content)
                    if len(list4) > 1:
                        node = Node(type=5, outLvl='', xml_content=list4[1])
                        nodeList.append(node)
                    # 收集段落节点
                    content_except_oMath = re.sub(r'<m:oMath>.*?</m:oMath>', '', content)
                    node = Node(type=1, outLvl='', xml_content=content_except_oMath)
                    nodeList.append(node)
                else:
                    outLvl = ""
                    if "w:pStyle w:val=" in content:
                        styleStr = content[content.find("w:pStyle w:val="):].split("/>")[0]
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

    # 提取图片
    def extractPic(self, input_file_path, output_file_path):
        if not zipfile.is_zipfile(input_file_path):
            with open(utils.getLogPath() + "error_log.txt", 'a',encoding='utf-8') as f:
                f.write(f"{datetime.now()} --- badFile with File: {input_file_path} + \n")
                f.close()
            return -1 # 不是docx文件
        #文件损坏
        try:
            docx_document = docx.Document(input_file_path)
        except Exception as e:
            print(f"{e} with File: {input_file_path}")
            with open(utils.getLogPath() + "error_log.txt", 'a') as f:
                f.write(f"{datetime.now()} --- {e} with File: {input_file_path}")
                f.close()
            return
        else:
            docx_related_parts = docx_document.part.related_parts
            index = 0
            export_files = []
            for rId in docx_related_parts:
                # for part in docx_related_parts:
                part = docx_related_parts[rId]
                partname = str(part.partname)
                if partname.startswith('/word/media/') or partname.startswith('/word/embeddings/'):
                    # 构建导出路径
                    index += 1
                    docx_name = output_file_path.split("/")[-1]
                    save_dir = output_file_path  # 获取当前py脚本路径
                    index_str = str(index).rjust(2, '0')
                    save_path = save_dir + '\\' + index_str + '-' + rId + '-' + \
                                str(part.partname).rsplit('/', 1)[1]  # 拼接路径
                    # print('导出路径：', save_path)

                    # 写入文件
                    if os.path.exists(output_file_path):
                        pass
                    else:
                        os.makedirs(output_file_path)
                    with open(save_path, 'wb') as f:
                        f.write(part.blob)
                        f.close()
                    # 记录文件
                    export_files.append(part.partname)
            print('导出的所有文件：', export_files)

# if __name__=="__main__":
#     file_path = utils.getUserPath() + "\input" + "\互联网金融、利率市场化与商业银行盈利能力的实证研究.docx"
#     output_dir_path = utils.getUserPath() + "\output" + "\互联网金融、利率市场化与商业银行盈利能力的实证研究"
#     docxParser = DocxParser()
#     docxParser.parseDocx(file_path, output_dir_path)
