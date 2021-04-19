import os

class Config(object):
    default_ip='127.0.0.1'
    default_port=6666
    user_password={
        "zzc":"123456",
        "lmg":"123456"
        
    }
    BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cfg=Config()


