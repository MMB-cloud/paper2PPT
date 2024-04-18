from pptx import Presentation
from pptx.util import Cm, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_PARAGRAPH_ALIGNMENT
from Utils import Utils

utils = Utils()

"""实现对幻灯片模板内容的读取与写入"""
class Template:
    """
    :param template_dir_path: 幻灯片模板文件夹
    :param output_dir_path: 幻灯片输出文件夹
    :return: None
    """
    def __init__(self, template_dir_path) -> None:
        self.__template_dir_path = template_dir_path


    """
    :param data: 待输出的文本、图表和图像内容
    :param output_path: 替换后幻灯片的指定输出路径
    """
    def replace(self, data, output_path):
        # 1. 根据slide类型确定要替换的pptx_path
        slide_index = -1
        if data["type"] == 0:
            slide_index = 0
        elif data["type"] == 1:
            num = len(data["content"])
            slide_index = num -3
        elif data["type"] == 2:
            slide_index = 4
        elif data["type"] == 3:
            slide_index = 5
        pptx_path = self.__template_dir_path + "\index_0" + str(slide_index) + ".pptx"
        ppt = Presentation(pptx_path)
        slide = ppt.slides[0]

        # 2. 获取pptx的配置
        configure = utils.json_to_dict(self.__template_dir_path + "\configure.json")
        text_frames_configure = configure["slides"][slide_index]["text_frames"]

        # 3. 获取文本框，并进行内容替换
        text_frames = [] if slide_index not in [5] else {}
        if slide_index not in [5]:
            for text_frame_configure in text_frames_configure:
                for shape in slide.shapes:
                    if shape.has_text_frame and text_frame_configure["content"] in shape.text_frame.text:
                        text_frames.append(shape.text_frame)
            for i in range(len(text_frames)):
                text_frame = text_frames[i]
                text_frame_style = text_frames_configure[i]["style"]
                paragraph = text_frame.paragraphs[0]
                paragraph.text = data["content"][i] if type(data["content"]) == list else data["content"]
                if text_frame_style["paragraph_alignment"] == "center":
                    paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.CENTER
                font = paragraph.font
                font.name = text_frame_style["font_name"]
                font.color.rgb = RGBColor(text_frame_style["font_color_rgb"][0], text_frame_style["font_color_rgb"][1], text_frame_style["font_color_rgb"][2])
                font.size = Pt(text_frame_style["font_size"])
                font.bold = text_frame_style["font_bold"]
        else:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    if text_frames_configure["heading"]["content"] in shape.text_frame.text:
                        paragraph = shape.text_frame.paragraphs[0]
                        text_frame_style = text_frames_configure["heading"]["style"]
                        paragraph.text = data["content"]["heading"]
                        if text_frame_style["paragraph_alignment"] == "center":
                            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.CENTER
                        font = paragraph.font
                        font.name = text_frame_style["font_name"]
                        font.color.rgb = RGBColor(text_frame_style["font_color_rgb"][0], text_frame_style["font_color_rgb"][1], text_frame_style["font_color_rgb"][2])
                        font.size = Pt(text_frame_style["font_size"])
                        font.bold = text_frame_style["font_bold"]
                    else:
                        for i in range(len(text_frames_configure["children"])):
                            if text_frames_configure["children"][i]["keyword"]["content"] in shape.text_frame.text:
                                paragraph = shape.text_frame.paragraphs[0]
                                text_frame_style = text_frames_configure["children"][i]["keyword"]["style"]
                                paragraph.text = data["content"]["children"][i]["keyword"]
                                if text_frame_style["paragraph_alignment"] == "center":
                                    paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.CENTER
                                font = paragraph.font
                                font.name = text_frame_style["font_name"]
                                font.color.rgb = RGBColor(text_frame_style["font_color_rgb"][0], text_frame_style["font_color_rgb"][1], text_frame_style["font_color_rgb"][2])
                                font.size = Pt(text_frame_style["font_size"])
                                font.bold = text_frame_style["font_bold"]
                            else:
                                if text_frames_configure["children"][i]["sentences"]["content"] in shape.text_frame.text:
                                    for j in range(len(data["content"]["children"][i]["sentences"])):
                                        paragraph = shape.text_frame.paragraphs[j]
                                        text_frame_style = text_frames_configure["children"][i]["sentences"]["style"]
                                        paragraph.text = data["content"]["children"][i]["sentences"][j]
                                        if text_frame_style["paragraph_alignment"] == "center":
                                            paragraph.alignment = PP_PARAGRAPH_ALIGNMENT.CENTER
                                        font = paragraph.font
                                        font.name = text_frame_style["font_name"]
                                        font.color.rgb = RGBColor(text_frame_style["font_color_rgb"][0], text_frame_style["font_color_rgb"][1], text_frame_style["font_color_rgb"][2])
                                        font.size = Pt(text_frame_style["font_size"])
                                        font.bold = text_frame_style["font_bold"]
        ppt.save(output_path)






        

        

