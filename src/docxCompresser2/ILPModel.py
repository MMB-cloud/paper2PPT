import cvxpy as cp
from numpy import array
import pandas as pd


def check(node, strlist):
    matched = False
    for str in strlist:
        if str in node.getTextContent().replace(" ", ""):
            matched = True
            break
    return matched


"""
用于内容选取的整数线性规划模型
    目标: 最大化生成的幻灯片的内容单元总权重
    约束:
        - 静态约束
            1. 总文字量约束
            2. 图表、图标题和对图表的描述性句子是绑定在一起的，要么都选，要么都不选
        - 动态约束(基于制作学术论文幻灯片的经验设定的内容选取的规则约束，存储在剧本当中，需要加载并转化为约束条件)
            1. 哪些子章节必须被选中
            2. 子章节内容选取的句子的数量的期望值
            3. 哪些章节中如果出现了图表，则图表必须被保留
"""


class ILPModel:
    def __init__(self) -> None:
        pass

    """模型构建与求解"""

    def build_and_solve(self, node, maxLength, presentation_type, rules=[]):
        # 先看presentation_type字段
        if presentation_type == "text_based":  # 文字型幻灯片, 不考虑图表
            weightList = []  # 句子权重列表
            lengthList = []  # 句子长度列表

            # 获取句子列表
            leafnodes = node.getleafnodes()
            # 获取句子权重列表和句子长度列表的值
            for leafnode in leafnodes:
                weightList.append(leafnode.getScore())
                lengthList.append(leafnode.getLength())

            # 获取rules里面的规则参数
            # 先看是否能匹配到当中的章节
            if len(rules) == 0:  # 没有规则, 走默认路径
                # 默认路径下只有文字量约束

                # 构建整数线性规划模型
                c_list = []
                a_matrix = [[]]
                for i in range(len(weightList)):
                    c_list.append(-weightList[i] * float(lengthList[i]) / float(maxLength))
                    a_matrix[0].append(lengthList[i])

                c = array(c_list)  # 目标向量
                a = array(a_matrix)  # 约束矩阵
                b = array(maxLength)
                lent = len(weightList) if len(weightList) > 0 else 1
                x = cp.Variable(lent, integer=True)  # 决策变量
                if len(c) == 0:
                    return 0
                objective = cp.Minimize(c * x)  # 目标函数
                constraints = [a @ x <= b, x >= 0, x <= 1]  # 约束条件
                problem = cp.Problem(objective, constraints)  # 问题模型

                # 问题模型求解
                problem.solve(solver='GLPK_MI', verbose=True)
                results = list(x.value)
                for i in range(len(results)):
                    selected = True if results[i] == 1 else False
                    leafnodes[i].setChosen(selected)
            else:  # 有规则，看是否能匹配到当中的章节
                for docpart in rules:
                    if check(node, docpart["name"]):  # 匹配到了，读取规则
                        # 先读取necessary字段
                        if docpart["necessary"]:
                            # 获取page_id
                            page_id = docpart["page_id"]
                            # 获取sent_num
                            sent_num = docpart["sent_num"]
                            # 获取compress_mode
                            compress_mode = docpart["compress_mode"]

                            if compress_mode == "ILP_Model":
                                # 看是否独占一个page_id，如果是的话，其maxLength的值取参数maxLenght和450里面的最大值
                                page_only = False
                                link_num = 0
                                for docpart in rules:
                                    if docpart["page_id"] == page_id:
                                        link_num += 1
                                if link_num == 1:
                                    page_only = True
                                if page_only:
                                    maxLength = maxLength if maxLength > 350 else 350
                                # 获取最小句子数量限制和最大句子数量限制
                                min_value = -1
                                max_value = -1
                                if len(sent_num) == 0:  # 没有最大和最小约束
                                    pass
                                else:
                                    min_value = sent_num[0]
                                    max_value = sent_num[1]

                                # 构建整数线性规划模型
                                c_list = []
                                a_matrix = [[], [], []] if min_value != -1 else [[]]
                                for i in range(len(weightList)):
                                    c_list.append(-weightList[i] * float(lengthList[i]) / float(maxLength))
                                    # c_list.append(-weightList[i])
                                    if min_value != -1:  # 存在最大和最小句子数量约束
                                        a_matrix[0].append(lengthList[i])
                                        a_matrix[1].append(-1.0)  # 最小约束
                                        a_matrix[2].append(1.0)  # 最大约束
                                    else:
                                        a_matrix[0].append(lengthList[i])

                                c = array(c_list)  # 目标向量
                                a = array(a_matrix)  # 约束矩阵
                                b = array([])
                                if min_value != -1:
                                    b = array([maxLength, -min_value, max_value])  # 约束条件
                                else:
                                    b = array(maxLength)
                                x = cp.Variable(len(weightList), integer=True)  # 决策变量
                                objective = cp.Minimize(c * x)  # 目标函数
                                constraints = [a @ x <= b, x >= 0, x <= 1]  # 约束条件
                                problem = cp.Problem(objective, constraints)  # 问题模型

                                # 问题模型求解
                                problem.solve(solver='GLPK_MI', verbose=True)
                                df = pd.DataFrame(x.value)
                                results = df.values.flatten().tolist()
                                # results = list(x.value)
                                print(results)
                                for i in range(len(results)):
                                    selected = True if results[i] == 1 else False
                                    leafnodes[i].setChosen(selected)
                            else:  # 句式+提示词匹配模式
                                pass
                            break
                        else:  # necessary字段值为False，就不作处理
                            break
                    else:  # 没有匹配到
                        if rules.index(docpart) == len(rules) - 1:  # 直到最后一个也没有匹配到
                            # 执行默认路径  默认路径下只有文字量约束

                            # 构建整数线性规划模型
                            c_list = []
                            a_matrix = [[]]
                            for i in range(len(weightList)):
                                c_list.append(-weightList[i] * float(lengthList[i]) / float(maxLength))
                                # c_list.append(-weightList[i])
                                a_matrix[0].append(lengthList[i])

                            c = array(c_list)  # 目标向量
                            a = array(a_matrix)  # 约束矩阵
                            b = array(maxLength)
                            x = cp.Variable(len(weightList), integer=True)  # 决策变量
                            objective = cp.Minimize(c * x)  # 目标函数
                            constraints = [a @ x <= b, x >= 0, x <= 1]  # 约束条件
                            problem = cp.Problem(objective, constraints)  # 问题模型

                            # 问题模型求解
                            problem.solve(solver='GLPK_MI', verbose=True)
                            results = list(x.value)
                            for i in range(len(results)):
                                selected = True if results[i] == 1 else False
                                leafnodes[i].setChosen(selected)
                        else:  # 继续进行匹配
                            continue
        elif presentation_type == "chart_oriented":  # 图表型幻灯片, 考虑图表
            weightList = []  # 权重列表
            lengthList = []  # 长度列表

            unitMatrix, exist = node.getUnitMatrix()
            if exist:
                # 获取文本块集合(句子集合)
                para_leafnodes = unitMatrix[0]
                # 表格块集合 [[表格节点, 表标题节点, 描述性句子集合, 位置向量]]
                tableMatrix = unitMatrix[1]
                # 图像块集合 [[图像节点, 图标题节点, 描述性句子集合, 位置向量]]
                imageMatrix = unitMatrix[2]

                # 获取权重列表和长度列表的值
                for leafnode in para_leafnodes:
                    weightList.append(leafnode.getScore())
                    lengthList.append(leafnode.getLength())
                for tableArray in tableMatrix:
                    # 计算权重, 表格块的权重为表格权重 + 表标题权重 + 描述性句子集合权重
                    weight = 0.0
                    weight += tableArray[0].getScore()
                    if tableArray[1] != None:
                        weight += tableArray[1].getChildren()[0].getScore()
                        for leafnode in tableArray[2]:
                            weight += leafnode.getScore()
                    # 计算长度, 表格块的长度设定为表标题长度 + 描述性句子总长度
                    length = 0
                    if tableArray[1] != None:
                        length += tableArray[1].getChildren()[0].getLength()
                        for leafnode in tableArray[2]:
                            length += leafnode.getLength()
                    weightList.append(weight)
                    lengthList.append(length)
                for imageArray in imageMatrix:
                    weight = 0.0
                    length = 0
                    weight += imageArray[0].getScore()
                    if imageArray[1] != None:
                        weight += imageArray[1].getChildren()[0].getScore()
                        for leafnode in imageArray[2]:
                            weight += leafnode.getScore()
                    if imageArray[1] != None:
                        length += imageArray[1].getChildren()[0].getScore()
                        for leafnode in imageArray[2]:
                            length += leafnode.getLength()
                    weightList.append(weight)
                    lengthList.append(length)

                # 构建整数线性规划模型
                c_list = []
                a_matrix = [[]]
                for i in range(len(weightList)):
                    c_list.append(-weightList[i] * float(lengthList[i]) / float(maxLength))
                    # c_list.append(-weightList[i])
                    a_matrix[0].append(lengthList[i])

                c = array(c_list)  # 目标向量
                a = array(a_matrix)  # 约束矩阵
                b = array(maxLength)  # 约束条件
                x = cp.Variable(len(weightList), integer=True)  # 决策变量
                objective = cp.Minimize(c * x)  # 目标函数
                constraints = [a @ x <= b, x >= 0, x <= 1]  # 约束条件
                problem = cp.Problem(objective, constraints)  # 问题模型

                # 问题求解
                selectedList = []
                problem.solve(solver='GLPK_MI', verbose=True)
                results = list(x.value)
                for i in range(len(results)):
                    selected = True if results[i] == 1 else False
                    selectedList.append(selected)

                # 确定哪些内容对象被选取
                # 文本块，句子集合
                for i in range(len(para_leafnodes)):
                    para_leafnodes[i].setSelected(selectedList[i])
                # 表格块 [[表格节点, 表标题节点, 描述性句子集合]]
                for i in range(len(tableMatrix)):
                    selected = selectedList[i + len(para_leafnodes)]
                    tableMatrix[i][0].getChosen(selected)  # 表格节点
                    if tableMatrix[i][1] != None:
                        tableMatrix[i][1].getChildren()[0].getChosen(selected)  # 表标题节点
                        for leafnode in tableMatrix[i][2]:
                            leafnode.getChosen(selected)  # 描述性句子节点
                # 图像块 [[图像节点, 图标题节点, 描述性句子集合]]
                for i in range(len(imageMatrix)):
                    selected = selectedList[i + len(para_leafnodes) + len(tableMatrix)]
                    imageMatrix[i][0].getChosen(selected)  # 图像节点
                    if imageMatrix[i][1] != None:
                        imageMatrix[i][1].getChildren()[0].getChosen(selected)  # 图标题节点
                        for leafnode in imageMatrix[i][2]:
                            leafnode.getChosen(selected)  # 描述性句子节点
            else:
                # 直接转向构建文字型整数线性规划模型
                self.build_and_solve(node=node, maxLength=maxLength, presentation_type="text_based", rules=rules)



    """模型构建与求解"""
    # def sent_select(self, node, maxLength, classifyResult):
    #     weightList = [] # 权重列表
    #     lengthList = [] # 长度列表

    #     unitMatrix = node.getUnitMatrix()
    #     # 获取文本块集合(句子集合)
    #     para_leafnodes = unitMatrix[0]
    #     # 表格块集合 [[表格节点, 表标题节点, 描述性句子集合, 位置向量]]
    #     tableMatrix = unitMatrix[1]
    #     # 图像块集合 [[图像节点, 图标题节点, 描述性句子集合, 位置向量]]
    #     imageMatrix = unitMatrix[2]

    #     # 获取权重列表和长度列表的值
    #     for leafnode in para_leafnodes:
    #         weightList.append(leafnode.getScore())
    #         lengthList.append(leafnode.getLength())
    #     for tableArray in tableMatrix:
    #         # 计算权重, 表格块的权重为表格权重 + 表标题权重 + 描述性句子集合权重
    #         weight = 0.0
    #         weight += tableArray[0].getScore()
    #         if tableArray[1] != None:
    #             weight += tableArray[1].getChildren()[0].getScore()
    #             for leafnode in tableArray[2]:
    #                 weight += leafnode.getScore()
    #         # 计算长度, 表格块的长度设定为表标题长度 + 描述性句子总长度
    #         length = 0
    #         if tableArray[1] != None:
    #             length += tableArray[1].getChildren()[0].getLength()
    #             for leafnode in tableArray[2]:
    #                 leafnode += leafnode.getLength()
    #         weightList.append(weight)
    #         lengthList.append(length)
    #     for imageArray in imageMatrix:
    #         weight = 0.0
    #         weight += imageArray[0].getScore()
    #         if imageArray[1] != None:
    #             weight += imageArray[1].getChildren()[0].getScore()
    #             for leafnode in imageArray[2]:
    #                 weight += leafnode.getScore()
    #         if imageArray[1] != None:
    #             length += imageArray[1].getChildren()[0].getLength()
    #             for leafnode in imageArray[2]:
    #                 length += leafnode.getLength()
    #         weightList.append(weight)
    #         lengthList.append(length)

    #     # 构建整数线性规划模型
    #     c_list = [[]]
    #     a_matrix = [[]]
    #     for i in range(len(weightList)):
    #         c_list.append(-weightList[i] * float(lengthList[i]) / float(maxLength))
    #         a_matrix[0].append(lengthList[i])

    #     c = array(c_list)       # 目标向量
    #     a = array(a_matrix)     # 约束矩阵
    #     b = array(maxLength)    # 约束条件
    #     x = cp.Variable(len(weightList), integer=True)      # 决策变量
    #     objective = cp.Minimize(c * x)      # 目标函数
    #     constraints = [a*x <= b, x >= 0, x <= 1]    # 约束条件
    #     problem = cp.Problem(objective, constraints)    # 问题模型

    #     # 问题求解
    #     selectedList = []
    #     problem.solve(solver='GLPK_MI', verbose=True)
    #     results = list(x.value)
    #     for i in range(len(results)):
    #         selected = True if results[i] == 1 else False
    #         selectedList.append(selected)

    #     # 确定哪些内容对象被选取
    #     # 文本块，句子集合
    #     for i in range(len(para_leafnodes)):
    #         para_leafnodes[i].setSelected(selectedList[i])
    #     # 表格块 [[表格节点, 表标题节点, 描述性句子集合]]
    #     for i in range(len(tableMatrix)):
    #         selected = selectedList[i + len(para_leafnodes)]
    #         tableMatrix[i][0].setSelected(selected)     # 表格节点
    #         if tableMatrix[i][1] != None:
    #             tableMatrix[i][1].getChildren()[0].setSelected(selected)    # 表标题节点
    #             for leafnode in tableMatrix[i][2]:
    #                 leafnode.setSelected(selected)      # 描述性句子节点
    #     # 图像块 [[图像节点, 图标题节点, 描述性句子集合]]
    #     for i in range(len(imageMatrix)):
    #         selected = selectedList[i+len(para_leafnodes)+len(tableMatrix)]
    #         imageMatrix[i][0].setSelected(selected)     # 图像节点
    #         if imageMatrix[i][1] != None:
    #             imageMatrix[i][1].getChildren()[0].setSelected(selected)    # 图标题节点
    #             for leafnode in imageMatrix[i][2]:
    #                 leafnode.setSelected(selected)      # 描述性句子节点
