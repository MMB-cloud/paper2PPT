import os

from common.Utils import Utils
import docx

class PicExtractor:

    def extractPic(self, input_file_path, output_file_path):
        utils = Utils()
        docx_document = docx.Document(input_file_path)
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
                save_dir = output_file_path # 获取当前py脚本路径
                index_str = str(index).rjust(2, '0')
                save_path = save_dir + docx_name.rsplit('.',1)[0] + '\\' + index_str + ' - ' +rId + ' - ' + str(part.partname).rsplit('/',1)[1] # 拼接路径
                print('导出路径：', save_path)

                # 写入文件
                if os.path.exists(output_file_path):
                    pass
                else:
                    os.makedirs(output_file_path)
                with open(save_path, 'wb') as f:
                    f.write(part.blob)
                    f.close()
                # 记录文件
                export_files.append(output_file_path)
            print('导出的所有文件：', export_files)

if __name__ == '__main__':
    utils = Utils()
    pe = PicExtractor()
    pe.extractPic(utils.getUserPath() + "\input" + "/B2C环境下消费者购买决策影响因素研究2023218_22845.docx",utils.getUserPath() + "\output" + "/B2C环境下消费者购买决策影响因素研究2023218_22845")
    # #文件路径
    # utils = Utils()
    # docx_name = '1997-2011年我国专利产出与经济增长效率的关系研究2023218_174316.docx'
    # docx_file = utils.getInputPath() + docx_name
    # docx_document = docx.Document(docx_file)
    # docx_related_parts = docx_document.part.related_parts
    # index = 0
    # export_files = []
    # for rId in docx_related_parts:
    # #for part in docx_related_parts:
    #     part = docx_related_parts[rId]
    #     partname = str(part.partname)
    #     if partname.startswith('/word/media/') or partname.startswith('/word/embeddings/'):
    #         # 构建导出路径
    #         index += 1
    #         save_dir = utils.getOutputPath()  # 获取当前py脚本路径
    #         index_str = str(index).rjust(2, '0')
    #         save_path = save_dir + docx_name.rsplit('.',1)[0] + '\\' + index_str + ' - ' +rId + ' - ' + str(part.partname).rsplit('/',1)[1] # 拼接路径
    #         print('导出路径：', save_path)
    #
    #         # 写入文件
    #         if os.path.exists(save_dir + docx_name.rsplit('.',1)[0]):
    #             pass
    #         else:
    #             os.makedirs(save_dir + docx_name.rsplit('.',1)[0])
    #         with open(save_path, 'wb') as f:
    #             f.write(part.blob)
    #             f.close()
    #         # 记录文件
    #         export_files.append(save_path)
    #     print('导出的所有文件：', export_files)
    #print(docx_related_parts) #para88 -> part -> part -> rels -> rid8 ->target_part
