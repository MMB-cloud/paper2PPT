def test1():
    n = int(input())
    s = list(map(int, input().split()))
    t = list(map(int, input().split()))
    st = list(s + t)
    st.sort()
    min = st[0]
    max = st[-1]
    diff = [0] * (max - min + 1)
    for i in range(n):
        diff[s[i] - min] += 1
        if t[i] + 1 - min < len(diff):
            diff[t[i] + 1 - min] -= 1

    cnt = 0
    max_cnt = 0
    cur_cnt = 0
    for i in range(len(diff)):
        cur_cnt += diff[i]
        if cur_cnt > max_cnt:
            max_cnt = cur_cnt
            cnt = 1
        elif cur_cnt == max_cnt:
            cnt += 1
    print(max_cnt)
    print(cnt)


if __name__ == '__main__':
    test1()
