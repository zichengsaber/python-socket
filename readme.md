# XJTU 计算机网络实验8(Socket programing)

> zichengsaber

## 实现一个简单的聊天/文件传输程序(C/S)

### 框架
![](./img/arch.png)
### 功能展示

**登录**
在云服务器上启动`server.py`,此时的IP应该为你的服务器的内网的IP
![](./img/login(1).png)

在本地启动`client.py`,此时的IP应该是你的服务器的公网的IP
![](./img/login(2).png)

**聊天**
为了展示聊天功能我们需要在本地开启另一个`client.py`进程
![](./img/login(3).png)
聊天界面
![](./img/chat(1).png)
![](./img/chat(2).png)

**shell 命令**
客户端可以在服务器的个人文件夹下建立目录，删除文件
<img src="./img/cmd(1).png" style="zoom:67%">
<img src="./img/cmd(2).png" style="zoom:67%">

**上传文件**
<img src="./img/push.png" style="zoom:60%">
<img src="./img/push(1).png" style="zoom:67%">

**下载文件**
<img src="./img/pull.png" style="zoom:60%">

**断点续传**
传输过程中人为断开网络连接
<img src="./img/breakpoint.png" style="zoom:70%">

原文件大小

<img src="./img/remote.png" style="zoom:70%">

本地已经下载的大小

<img src="./img/local.png" style="zoom:70%">

断点续传

<img src="./img/break(2).png" style="zoom:67%">






