import socketserver
import json
import os 
import sys 
import shutil
import threading
import time 
import argparse
from conf.config import cfg
STATUS_CODE  = {

    250 : "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251 : "Invalid cmd ",
    252 : "Invalid auth data",
    253 : "Wrong username or password",
    254 : "Passed authentication",
    255 : "Filename doesn't provided",
    256 : "File doesn't exist on server",
    257 : "ready to send file",

    800 : "the file exist,but not enough ,is continue? ",
    801 : "the file exist !",
    802 : " ready to receive datas",

}



socket_to_user={} 

"""
A concrete request handler subclass must define a new handle() method, 
and can override any of the other methods. 
A new instance of the subclass is created for each request.
"""

class ServerHandler(socketserver.BaseRequestHandler):
    """
    This function must do all the work required to service a request
    """
    def handle(self):
        while True:
            data=self.request.recv(1024).strip()
            if data:
                data=json.loads(data.decode('utf8'))
                """
                {"action":"auth",
                "usename":"zzc"
                "pwd":123456
                }
                """
                if data.get("action"):
                    if hasattr(self,data.get("action")):
                        func=getattr(self,data.get("action"))
                        func(**data)
                    else:
                        print("Invalid command")
                else:
                    print("Invalid command")
    
    def send_response(self,state_code):
        # 状态码
        response={"status_code":state_code}
        self.request.sendall(json.dumps(response).encode())

    def auth(self,**data):
        username=data["username"]
        password=data["password"]

        user=self.authenticate(username,password)

        if user:
            self.send_response(254)
        else:
            self.send_response(253)

    # 从数据库中读入
    # 目前设计上来说是利用的零时的
    def authenticate(self,user,pwd):
        user_to_password=cfg.user_password
        if user_to_password.get(user):
            if user_to_password[user]==pwd:
                self.user=user
                socket_to_user[self.user]=self.request
                print(socket_to_user[self.user])
                self.rootPath=os.path.join(cfg.BASE_DIR,"home",self.user) # server/home/zzc
                print(self.user+" passed authentication")
                return user
    # chat
    # 需要设置退出
    # 要记录在线人数
    def chat(self,**data):
        print(self.user+" enter the chatroom!")
        
        while True:
            data_recv = self.request.recv(1024).decode("utf8")  # 接收数据
            if(data_recv=="q"):
                info={
                    "user":self.user,
                    "msg":"quit the chatroom"
                }
                # 广播消息
                for u,sock in socket_to_user.items():
                    if u==self.user:
                        info["msg"]="quit the chatroom"
                        sock.send(json.dumps(info).encode("utf8"))
                    else:
                        info["msg"]="quit the chat"
                        sock.send(json.dumps(info).encode("utf8"))
                print(self.user+" quit the chatroom!")
                return
            else: # 正常的消息发送
                print(self.user+" 发来消息：",data_recv)
                info={
                    "user":self.user,
                    "msg":data_recv
                }
                # 广播消息
                for u,sock in socket_to_user.items():
                    if u!=self.user:
                        sock.send(json.dumps(info).encode("utf8"))
    ### 文件处理部分
    def ls(self,**data):
        file_list = os.listdir(self.rootPath)
        file_str="\n".join(file_list)
        if not len(file_list):
            file_str="<empty dir>"
        self.request.sendall(file_str.encode("utf8"))

    def cd(self,**data):
        dirname=data.get('dirname')
        topdirname=os.path.join(cfg.BASE_DIR,"home") 

        if dirname=='~':
            self.rootPath=topdirname
        elif dirname=="..": # 上一级目录
            if self.rootPath!=topdirname:
                self.rootPath=os.path.dirname(self.rootPath)
            else:
                self.request.sendall("this is the top dir!".encode("utf8"))
                return 
        elif dirname==".": # 当前目录
            self.request.sendall(self.rootPath.encode("utf8"))
            return
        else:
            back=self.rootPath
            self.rootPath=os.path.join(self.rootPath,dirname)
            if not os.path.isdir(self.rootPath):
                self.rootPath=back
        
        self.request.sendall(self.rootPath.encode("utf8"))
        return 

    def pwd(self,**data):
        self.request.sendall(self.rootPath.encode("utf8"))

    def mkdir(self,**data):
        dirname=data["dirname"]
        path=os.path.join(self.rootPath,dirname)
        if not os.path.exists(path): # 创建
            if "/" in dirname:
                os.makedirs(path)
            else:
                os.mkdir(path)
            self.request.sendall("create directory successfully!".encode("utf8"))
        else:
            self.request.sendall("dirname exist".encode("utf8"))
        
    def rm(self,**data):
        file_name=data["file_name"]
        path=os.path.join(self.rootPath,file_name)
        if not os.path.exists(path):
            print("no such file")
            self.request.sendall("no such file".encode("utf8"))
        else:
            try:
                shutil.rmtree(path) # 递归删除
            except:
                os.remove(path) 
            print("delete over!!")
            str_info="remove "+file_name+" success!!!"
            self.request.sendall(str_info.encode('utf8'))


    def push(self,**data):
        print("data",data)
        file_name=data.get("file_name")       # 获取客户上传文件的名称，大小和目标地址
        file_size=data.get("file_size")
        target_path=data.get("target_path")

        if file_name=="no such file":
            print("no such file!")
            return

        if len(target_path)==0:
            abs_path=os.path.join(self.rootPath,file_name)
        else:
            abs_path=os.path.join(self.rootPath,target_path,file_name)  # 连接路径，获取绝对路径
        
        target_path=os.path.join(self.rootPath,target_path)
        if not os.path.exists(target_path):
            self.request.sendall('no such dir'.encode("utf8"))
            print("no such dir!")
            return
        else:
            self.request.sendall('ok'.encode("utf8"))

        ##########################################
        has_received=0

        if os.path.exists(abs_path):      # 判断要上传的文件是否已经存在于FTP
            file_has_size=os.stat(abs_path).st_size
            if file_has_size<file_size:
                # 断点续传
                self.request.sendall("800".encode("utf8")) # 接收客户端是否需要继续传输
                choice=self.request.recv(1024).decode("utf8")
                if choice=="Y":
                    self.request.sendall(str(file_has_size).encode("utf8"))
                    has_received+=file_has_size
                    f=open(abs_path,"ab")  # 打开当前文件，定位在尾端
                else:
                    f=open(abs_path,"wb")  # 不续传则，打开文件从文件头开始写，原内容删除

            else:
                self.request.sendall("801".encode("utf8"))         # 文件完全存在
                return

        else:
            self.request.sendall("802".encode("utf8"))
            f = open(abs_path, "wb")          # 创建新的文件，从头开始写

        while has_received<file_size:    # 文件写入过程
            try:
                data=self.request.recv(1024)
            except Exception:
                break
            f.write(data)
            has_received+=len(data)

        f.close()   
    
    def pull(self,**data):
        print("data",data)
        local_path=data.get("local_path")       # 获取下载文件的服务器的源地址
        target_path=data.get("target_path")

        local_path = os.path.join(self.rootPath, local_path)     # 得到源文件的绝对路径
        if not os.path.exists(local_path):
            self.request.send('no such file'.encode("utf8"))
            print("no such file!")
            return
        else:
            self.request.send('ok'.encode("utf8"))
        
        if target_path=="no such dir":
            print("no such dir!")
            return

        file_name = os.path.basename(local_path)  # 获取文件名称及大小
        file_size = os.stat(local_path).st_size

        file_info={    #发送文件完整路径和大小给客户端
            "file_name":file_name,
            "file_size":file_size
        }

        self.request.send(json.dumps(file_info).encode("utf8"))
        is_exist = self.request.recv(1024).decode("utf8")

        ############################################
        has_sent = 0
        if is_exist == "800":        # 文件存在，但不完整
            choice=self.request.recv(1024).decode("utf8")
            if choice== "Y":    # 续传，则更新文件位置到已经发送的末尾
                continue_position = self.request.recv(1024).decode("utf8")
                has_sent += int(continue_position)
            else:   # 不续传
                return

        elif is_exist == "801":              # 文件完全存在
            return

        f = open(local_path, "rb")    # 打开文件，只读状态
        f.seek(has_sent)
        while has_sent < file_size:
            data_new = f.read(1024)
            self.request.sendall(data_new)
            has_sent += len(data_new)

        f.close()


    def quit(self,**data): # 客户端对出ftp服务器
        info=self.user+" is quit!"
        del socket_to_user[self.user] 
        print(info)
        print("welcome next time!")
        exit()


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Client param')
    parser.add_argument("--ip",default=cfg.default_ip,type=str,help="server IP")
    parser.add_argument("--port",default=cfg.default_port,type=int,help="server port")
    args=parser.parse_args()
    s=socketserver.ThreadingTCPServer((args.ip,args.port),ServerHandler)
    print("Server started")
    s.serve_forever()