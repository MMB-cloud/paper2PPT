

class CompressNode:
    '''
    压缩后的节点
        引言：【Node】
        实验：【Node】
    '''
    def __init__(self, script_name, part_name, node):
        self.script_name = script_name
        self.part_name = part_name
        self.nodeTree = [] #压缩后的节点
        #递归建立一棵新的节点树，只包括选取的节点
