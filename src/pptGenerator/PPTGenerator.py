from win32com.client import Dispatch
from src.pptGenerator.PPTTree import PPTTree
from src.pptGenerator.Template import Template
from common.Utils import Utils

utils = Utils()


def parseDicToSlide(pptTree):
    template = Template(utils.getTemplatePath(), utils.getOutputPath())
    title = pptTree.title  # 标题
    index_script = pptTree.getIndexScript()  # 剧本索引索引页
    index_title = pptTree.getIndexTitle()  # 标题索引索引页
    # 标题页
    # 优先一级标题 如果一级标题重复则按二级标题
    template.setTitle(title)
    # 索引页
    template.setIndex(index_title)
    for pptNode in pptTree.pptDic["children"]:
        # 章节标题
        template.setSlideNode(pptNode, index_script, index_title)
    # 合并
    file_paths = utils.get_file_paths(utils.getOutputPath() + "\\" + title)
    pptx_paths = []
    for file_path in file_paths:
        if file_path.endswith(".pptx"):
            pptx_paths.append(file_path)
    ppt = Dispatch("PowerPoint.Application")
    # ppt.Visible = 1
    ppt.DisplayAlerts = 0
    pptA = ppt.Presentations.Open(pptx_paths[0])
    for pptx_path in pptx_paths[1:]:
        pptB = ppt.Presentations.Open(pptx_path)
        pptB.Slides(1).Copy()
        pptA.Slides.Paste()
        pptB.Close()
    # 设置合并后的ppt保存路径
    pptA.SaveAs(utils.getOutputPath() + "\\" + title + "\\final.pptx")
    pptA.Close()
    ppt.Quit()


class PPTGenerator:
    def __init__(self) -> None:
        pass

    def generatePPT1(self, docxTree):
        # 1.生成pptTree.json
        docxTree.getPPTTreeDic()

        # 2.读取pptTree，获取要生成的slides列表
        file_path = docxTree.getOutputDirPath() + "\pptTree.json"
        pptTree = PPTTree(file_path)
        dataList = []
        dataList.append(pptTree.getTitleData())
        dataList.append(pptTree.getDirectoryData())
        dataList.extend(pptTree.getTextDatas())

        # 3.根据幻灯片模板进行内容替换
        template_dir_path = utils.getTemplatePath() + "\\template_01"
        template = Template(template_dir_path,docxTree.getOutputDirPath())
        for data in dataList:
            output_path = docxTree.getOutputDirPath() + "\output_" + str(dataList.index(data)) + ".pptx"
            template.replace(data, output_path)

        # 4.将生成的PPT列表进行合并
        file_paths = utils.get_file_paths(docxTree.getOutputDirPath())
        pptx_paths = []
        for file_path in file_paths:
            if file_path.endswith(".pptx"):
                pptx_paths.append(file_path)
        ppt = Dispatch("PowerPoint.Application")
        # ppt.Visible = 1
        ppt.DisplayAlerts = 0
        pptA = ppt.Presentations.Open(pptx_paths[0])
        for pptx_path in pptx_paths[1:]:
            pptB = ppt.Presentations.Open(pptx_path)
            pptB.Slides(1).Copy()
            pptA.Slides.Paste()
            pptB.Close()
        # 设置合并后的ppt保存路径
        pptA.SaveAs(docxTree.getOutputDirPath() + "\\final.pptx")
        pptA.Close()
        ppt.Quit()

    def generatePPT2(self, json_path, output_dir_path):
        pptTree = PPTTree(json_path)
        dataList = []
        dataList.append(pptTree.getTitleData())
        dataList.append(pptTree.getDirectoryData())
        dataList.extend(pptTree.getTextDatas())

        # 3.根据幻灯片模板进行内容替换
        template_dir_path = utils.getTemplatePath() + "\\template_01"
        template = Template(template_dir_path,output_dir_path)
        for data in dataList:
            output_path = output_dir_path + "\output_" + str(dataList.index(data)) + ".pptx"
            template.replace(data, output_path)

        # 4.将生成的PPT列表进行合并
        file_paths = utils.get_file_paths(output_dir_path)
        pptx_paths = []
        for file_path in file_paths:
            if file_path.endswith(".pptx"):
                pptx_paths.append(file_path)
        ppt = Dispatch("PowerPoint.Application")
        # ppt.Visible = 1
        ppt.DisplayAlerts = 0
        pptA = ppt.Presentations.Open(pptx_paths[0])
        for pptx_path in pptx_paths[1:]:
            pptB = ppt.Presentations.Open(pptx_path)
            pptB.Slides(1).Copy()
            pptA.Slides.Paste()
            pptB.Close()
        # 设置合并后的ppt保存路径
        pptA.SaveAs(output_dir_path + "\\final.pptx")
        pptA.Close()
        ppt.Quit()
