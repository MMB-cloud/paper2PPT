def minFlips(A, B):
    n = len(A)

    # 判断两个矩阵是否可以通过翻转行或列变得相等
    def canTransform(A, B):
        for i in range(n):
            for j in range(n):
                if (A[0][0] ^ A[i][0] ^ A[0][j] ^ A[i][j]) != B[i][j]:
                    return False
        return True

    # 计算最少的翻转次数
    def countFlips(A, B):
        rowFlips = [0] * n
        colFlips = [0] * n
        for i in range(n):
            if A[i][0] != B[i][0]:
                rowFlips[i] = 1
        for j in range(n):
            if A[0][j] != B[0][j]:
                colFlips[j] = 1

        return sum(rowFlips) + sum(colFlips)

    # 先判断是否可以通过翻转使 A 变为 B
    if not canTransform(A, B):
        return -1

    # 计算最少的翻转次数
    return countFlips(A, B)






if __name__ == "__main__":
    # 测试用例
    A = [
        [0, 1, 0],
        [1, 0, 1],
        [0, 1, 0]
    ]

    B = [
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1]
    ]
    print(minFlips(A, B))  # 输出应该是3