def main():
    n, k = map(int, input().split(" "))
    nums = [int(c) for c in input().split(" ")]
    sorted(nums)

    ans = nums[-1] - nums[0]

    for i in range(k):
        max_value = max(nums[i - 1] * 2, nums[-1] // 2)
        min_value = min(nums[0] >> 1, nums[n - (k - i)] // 2)
        ans = min(ans, max_value - min_value)

    print(ans)


if __name__ == "__main__":
    main()
