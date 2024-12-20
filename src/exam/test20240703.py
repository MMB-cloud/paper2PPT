import math


def main():
    n, x = map(int, input().split())
    price = list(map(int,input().split()))
    joy = list(map(int,input().split()))
    dp = [[[0 for _ in range(3)] for _ in range(n)] for _ in range(x+1)]
    #初始化
    for i in range(1, x + 1):
        if i >= price[0]:
            dp[i][0][0] = joy[0]
    #dp
    for i in range(1, x + 1):
        for j in range(1, n):
            if i >= price[j]:
                dp[i][j][0] = max(dp[i - price[j]][j - 1][0], dp[i - price[j]][j - 1][1], dp[i - price[j]][j - 1][2]) + joy[j]  # 原价买
            if dp[i][j - 1][0] > 0 and i >= price[j] / 2:
                dp[i][j][1] = dp[i - int(price[j] / 2)][j - 1][0] + joy[j] #半价买
            dp[i][j][2] = max(dp[i][j - 1][0], dp[i][j - 1][1], dp[i][j - 1][2]) #不买
    print(max(dp[x][n - 1][0],dp[x][n - 1][1],dp[x][n - 1][2]))




if __name__ == "__main__":
    main()
