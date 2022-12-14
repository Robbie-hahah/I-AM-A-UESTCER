#include<winsock2.h>
#include<stdio.h>
#pragma comment(lib,"ws2_32.lib")
void CheckIP(void) //定义 CheckIP()函数，用于获取本机 IP 地址
{
	WSADATA wsaData;
	char name[255];//定义用于存放获得的主机名的变量
	char* ip;//定义 IP 地址变量
	PHOSTENT hostinfo;
	//调用 MAKEWORD()获得 Winsock 版本的正确值，用于加载 Winsock 库
	if (WSAStartup(MAKEWORD(2, 0), &wsaData) == 0) {
		//现在是加载 Winsock 库，如果 WSAStartup()函数返回值为 0，说明加载成 功，程序可以继续
		if (gethostname(name, sizeof(name)) == 0) {
			//如果成功地将本地主机名存放入由 name 参数指定的缓冲区中
			if ((hostinfo = gethostbyname(name)) != NULL) { //这是获取主机名，如果获得主机名成功的话，将返回一个指针，指向 hostinfo， hostinfo
			//为 PHOSTENT 型的变量，下面即将用到这个结构体
				ip = inet_ntoa(*(struct in_addr*)*hostinfo->h_addr_list);
				//调用 inet_ntoa()函数，将 hostinfo 结构变量中的 h_addr_list 转化为标准的点分 表示的 IP
				//地址(如 192.168.0.1)
				printf("%s\n", ip);//输出 IP 地址
			}
		}
		WSACleanup();//卸载 Winsock 库，并释放所有资源
	}
}

int main(void)
{
	CheckIP(); 
	return 0;
}
