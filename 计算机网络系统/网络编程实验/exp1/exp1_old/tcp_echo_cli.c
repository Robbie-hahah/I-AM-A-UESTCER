/*
    单进程客户端参考模版
    @2020 电子科技大学 信息与软件工程学院 《计算机网络系统》课程组
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <errno.h>
#include <signal.h>

#define MAX_CMD_STR 100

typedef struct sockaddr* pSA;

// 业务逻辑处理函数
int echo_rqt(int sockfd)
{
    char buf[MAX_CMD_STR+1];
    // 从stdin读取1行
    while (fgets(buf, MAX_CMD_STR, stdin)) {
        // TODO 收到exit，退出循环返回
        if(strncmp(buf, "exit", 4) == 0)
            return 0;

        // TODO 查询所读取1行字符的长度，并将行末'\n'更换为'\0'
        int len = strnlen(buf, MAX_CMD_STR);
        buf[len] = '\0';

        // TODO 根据读写边界定义，先发数据长度，再发缓存数据
        if(write(sockfd, &len, sizeof(int)) == -1)
        {
            printf("[cli] fail to write len!\n");
            exit(1);
        }
        if(write(sockfd, buf, sizeof(char)*len) == -1)
        {
            printf("[cli] fail to write buf!\n");
            exit(1);
        }

        // TODO 读取服务器echo回显数据，并打印输出到stdout，依然是先读长度，再根据长度读取数据
        if(read(sockfd, &len, sizeof(int)) == -1)
        {
            printf("[cli] fail to read len!\n");
            exit(1);
        }
        if(read(sockfd, buf, sizeof(char)*len) == -1)
        {
            printf("[cli] fail to read buf!\n");
            exit(1);
        }
        printf("[echo_rep] %s", buf);
/*注意：实际应用时，int型长度在读写时请注意字节序转换；为降低难度，测试平台标准服务器与客户端程序未在此进行字节序转换*/    
    }
    return 0;
}

int main(int argc,char *argv[])
{
    // TODO 定义服务器Socket地址srv_addr；
    struct sockaddr_in srv_addr;
    // TODO 定义Socket连接描述符connfd；
    int connfd;
    // 基于argc简单判断命令行指令输入是否正确；
    if(argc != 3){
        printf("Usage:%s <IP> <PORT>\n", argv[0]);
        return 0;
    }

    // TODO 初始化服务器Socket地址srv_addr，其中会用到argv[1]、argv[2]
        /* IP地址转换推荐使用inet_pton()；端口地址转换推荐使用atoi(); */
    bzero(&srv_addr, sizeof(srv_addr));
    srv_addr.sin_family = AF_INET;
    srv_addr.sin_port = htons(atoi(argv[2]));
    inet_pton(AF_INET, argv[1], &srv_addr.sin_addr);

    // TODO 获取Socket连接描述符: connfd = socket(x,x,x);
    connfd = socket(AF_INET, SOCK_STREAM, 0);
    if(connfd == -1)
    {
        printf("[cli] fail to get socket connfd!\n");
        exit(1);
    }
    do{
        // TODO 连接服务器，结果存于res: int res = connect(x,x,x);
        int res = connect(connfd, (pSA)&srv_addr, sizeof(srv_addr));
        // 以下代码紧跟connnect()；
        if(res == 0){
            // TODO 连接成功，按题设要求打印服务器端地址server[ip:port]
            printf("[cli] server[%s:%s] is connected!\n", argv[1], argv[2]);
            // TODO 执行业务处理函数echo_rqt();若echo_rqt()返回0，跳出循环准备释放资源，终结程序；
            if(echo_rqt(connfd) == 0)
                break;
        }
        else if(res == -1 && errno == EINTR)
            continue;// 若connect因系统信号中断而失败，则再次执行connect；
    } while(1);

    // TODO 关闭connfd
    close(connfd);
    printf("[cli] connfd is closed!\n");
    printf("[cli] client is exiting!\n");
    return 0;
}
