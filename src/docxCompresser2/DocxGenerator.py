import zipfile
import re

class DocxGenerator:
    def __init__(self) -> None:
        pass


    def generateDocx(self, docxTree):
        file_path = docxTree.getFilePath()
        z = zipfile.ZipFile(file_path)
        document_content = z.read("word/document.xml").decode("utf-8")
        output_dir_path = docxTree.getOutputDirPath()
        destz = zipfile.ZipFile(output_dir_path + "\\" + "压缩后.docx", "w", compression=zipfile.ZIP_DEFLATED)
        selectedNodeList = docxTree.getSelectedNodeList()
        body_xml_content = "<w:body>"
        for node in selectedNodeList:
            body_xml_content = body_xml_content + node.getXmlContent()
        body_xml_content = body_xml_content + "</w:body>"
        document_xml_content = ""
        list4 = re.split("<w:body>|</w:body>", document_content)
        document_xml_content = list4[0] + body_xml_content + list4[2]
        for filename in z.namelist():
            if filename == "word/document.xml":
                destz.writestr(filename, document_xml_content)
            else:
                if filename.endswith(".xml"):
                    destz.writestr(filename, z.read(filename).decode())
                else:
                    destz.writestr(filename, z.read(filename))
        destz.close()
        z.close()
