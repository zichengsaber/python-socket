import argparse
import socket
import json
import os
import sys 
import time
import threading 

STATUS_CODE = {
    250: "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251: "Invalid cmd ",
    252: "Invalid auth data",
    253: "Wrong username or password",
    254: "Passed authentication",
    255: "Filename doesn't provided",
    256: "File doesn't exist on server",
    257: "ready to send file",
    # 258: "md5 verification",

    800: "the file exist,but not enough ,is continue? ",
    801: "the file exist !",
    802: " ready to receive datas",
    900: "md5 valdate success"
}

DEFAULT_IP='127.0.0.1'
DEFAULT_PORT=6666

class ClientHandler():
    def __init__(self,args):
        self.sock=None
        self.args = args
        # 对端口范围验证
        self.verify_args(self.args)
        # 建立连接
        self.make_connection(args.ip,args.port)
        # 文件所在目录的绝对路径
        self.rootPath=os.path.dirname(os.path.abspath(__file__))
        # 标志
        self.last=False
        self.flag=True
    
    def interactive(self):
        print("begin to interactive.......")
        if self.authentication():
            while True:
                cmd_input=input("[{}]# ".format(self.current_dir)).strip()
                cmd_list=cmd_input.split()
                if hasattr(self,cmd_list[0]):
                    func=getattr(self,cmd_list[0])
                    func(*cmd_list)
                else:
                    print("Invalid command")
        else:
            # 认证失败关闭连接
            self.sock.close()
            exit(0)
        
            
    def verify_args(self,args): # 验证参数
        port=args.port 
        if port>0 and port< 65535:
            return 
        else:
            exit("The port is in 0~65535")
    def make_connection(self,ip,port): # 建立连接
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM) # IP,TCP 
        self.sock.connect((ip,port))
    
    def authentication(self): # 登录验证
        if self.args.user is None or self.args.password is None:
            username=input("username: ")
            password=input("password: ") 
        else:
            username=self.args.user
            password=self.args.password
        
        return self.get_auth_response(username,password)
    # 接受服务器的回应
    def get_auth_response(self,user,pwd):
        # 封装成字典
        data={
            "action":"auth",
            "username":user,
            "password":pwd
        }
        # 发送验证信息
        self.sock.send(json.dumps(data).encode("utf8"))
        # 接收验证信息
        response=self.sock.recv(1024).decode("utf8")
        response=json.loads(response) # 还原为dict
        
        if response["status_code"] == 254:      # 登录成功
            self.username = user
            self.current_dir = user
            print(STATUS_CODE[254])
            print("input help to see how to use")
            print("input quit to leave")
            return True
        else:     # 登录失败
            print(STATUS_CODE[response["status_code"]]) # "Wrong username or password"
    # 多人聊天的方式
    # 主要要解决的问题是
    def chat(self,*cmd_list): # 聊天
        data={
            "action":"chat",
        }
        self.sock.send(json.dumps(data).encode("utf8"))
        print("welcome to chat room!")
        print("input q to quit the chatroom")
        
        t1=threading.Thread(target=self.recvmsg)
        t1.start()
        while True:
            # 输出有一点小问题主要是抢占
            msg = input().strip()
            # msg=input("{}:".format(self.username)).strip()
            if len(msg) == 0:
                continue
            if msg=="q":
                self.sock.sendall(msg.encode("utf8"))
                time.sleep(1)
                return
            self.sock.sendall(msg.encode("utf8"))

    # 接收线程     
    def recvmsg(self):
        while True:
            info = self.sock.recv(1024).strip()
            info=json.loads(info.decode("utf8"))
            user_r=info.get("user")
            reply=info.get("msg")
            print(user_r+":"+reply)
            if reply=="quit the chatroom":
                break
    """
    文件处理部分     
    """
    def ls(self,*cmd_list):
        data={
            "action":"ls"
        }
        self.sock.sendall(json.dumps(data).encode("utf8"))

        data=self.sock.recv(1024).decode("utf8")
        print(data)
    
    def cd(self,*cmd_list):
        if len(cmd_list)==1:
            print("error format")
            return 
        data={
            "action":"cd",
            "dirname":cmd_list[1]
        }
        # 发送命令消息
        self.sock.sendall(json.dumps(data).encode("utf8"))
        # 接受
        data=self.sock.recv(1024).decode("utf8")



    """
    client 端退出
    """
    def quit(self,*cmd_list):
        data={
            "action":"quit",
        }
        self.sock.send(json.dumps(data).encode("utf8"))
        self.sock.close()
        exit(0)
    
        


if __name__=='__main__':
    # 可选参数
    parser = argparse.ArgumentParser(description='Client param')
    parser.add_argument("--ip",default=DEFAULT_IP,type=str,help="server IP")
    parser.add_argument("--port",default=DEFAULT_PORT,type=int,help="server port")
    parser.add_argument("--user",type=str,help="username")
    parser.add_argument("--password",type=str,help="username")
    args=parser.parse_args()
    ch=ClientHandler(args)
    ch.interactive()
    