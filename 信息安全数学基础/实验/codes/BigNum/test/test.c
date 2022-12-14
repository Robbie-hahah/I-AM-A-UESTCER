#include<stdio.h>
#include<string.h>

#define MAX 100000000000    // 大数的最大位数 


/*
  大数加法
  参数：
  num1为第一个大数，用字符数组保存
  num2为第二个大数
  sum数组保存相加的结果  即：num1+num2=sum
  返回值：返回数组sum的有效长度，即计算结果的位数
 */
int Addition(char num1[], char num2[], int sum[])
{
	int i, j, len;
	int n2[MAX] = { 0 };
	int len1 = strlen(num1); // 计算数组num1的长度，即大数的位数 
	int len2 = strlen(num2); // 计算数组num2的长度，即大数的位数 

	len = len1 > len2 ? len1 : len2; // 获取较大的位数
	//将num1字符数组的数字字符转换为整型数字，且逆向保存在整型数组sum中，即低位在前，高位在后
	for (i = len1 - 1, j = 0; i >= 0; i--, j++)
		sum[j] = num1[i] - '0';
	// 转换第二个数 
	for (i = len2 - 1, j = 0; i >= 0; i--, j++)
		n2[j] = num2[i] - '0';
	// 将两个大数相加 
	for (i = 0; i <= len; i++)
	{
		sum[i] += n2[i];  // 两个数从低位开始相加 
		if (sum[i] > 9)   // 判断是否有进位 
		{   // 进位 
			sum[i] -= 10;
			sum[i + 1]++;
		}
	}
	if (sum[len] != 0)  // 判断最高位是否有进位 
		len++;
	return len;   // 返回和的位数 
}

int main()
{
	int i, len;
	int sum[MAX] = { 0 }; // 存放计算的结果，低位在前，高位在后，即sum[0]是低位 
	char num1[] = "1234567891234567891234"; // 第一个大数 
	char num2[] = "2345678912345678913345"; // 第二个大数 
	len = Addition(num1, num2, sum);    // 两数相加 
	printf("%s\n  +\n%s\n  =\n", num1, num2);
	// 反向输出求和结果
	for (i = len - 1; i >= 0; i--)
		printf("%d", sum[i]);
	printf("\n");
	system("pause");
	return 0;
}