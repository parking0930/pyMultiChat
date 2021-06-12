import threading
import os
import socket
from prettytable import PrettyTable # pip install prettytable 로 설치 후 사용 가능
from time import sleep

port = 2500
address = ("localhost", port)
BUFSIZE = 1024

roomList = {} # {방 제목:[닉네임1, 닉네임2, ...]} 형태로 사용
my_nickname = ""

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(address)
mode = 1 # 1은 채팅방 입장 전 2는 입장 후

def receive_msg():
    while True:
        r_msg = s.recv(BUFSIZE)
        if not r_msg:
            break
        if mode==1:
            if r_msg.decode()=="refresh":
                global roomList
                roomList = {}
                while True: # 방 목록을 로딩하기 위한 반복문
                    r_msg = s.recv(BUFSIZE).decode()
                    if r_msg=="LoadComplete":
                        break
                    tmp = r_msg.split("|")
                    roomList[tmp[0]] = tmp[1][1:len(tmp[1])-1].replace("'", "").replace(" ", "").split(",")
                print_room()
                print(my_nickname+"님 환영합니다.")
                print("원하시는 작업을 선택해주세요.")
                print("1: 방 선택")
                print("2: 방 만들기")
                print("3: 종료하기\n선택: ", end="")
        elif mode==2:
            if r_msg.decode().find(':')==-1 and r_msg.decode().find('[SYSTEM]')==-1:
                continue
            print("", end="\r", flush=True)
            print(" "*(len(my_nickname)*2+2), end="")
            print("", end="\r", flush=True)
            print("%s\n%s:" %(r_msg.decode(), my_nickname), end="")
def send_msg():
    state = 0
    while 1:
        sleep(0.01)
        if state == 0:
            state = 1
            print("", end="\r", flush=True)
        data = input(my_nickname+":")
        if data == "/나가기":
            s.close()
            return
        data = my_nickname+":"+data
        s.send(data.encode())
    s.close()

def isRoomExist(roomName):
    for key, value in roomList.items():
        if key == roomName:
            return True
    return False

def create_room():
    msg = "create"
    s.send(msg.encode())
    while True:
        roomName = input("방 제목: ")
        if not isRoomExist(roomName) and roomName != "":
            break
        else:
            print("올바른 제목을 입력해주세요.")
    msg = roomName+"|"+my_nickname # 제목|닉네임
    s.send(msg.encode())
    os.system('cls')
    print("방 제목: "+ roomName)
    print("나의 닉네임: "+my_nickname)
    print("명령어: /나가기")
    print("-"*100)
    print("[SYSTEM] "+my_nickname+"님이 방을 생성하셨습니다.")

def select_room():
    while True:
        inp = input("입장할 방 번호를 선택하세요:")
        if int(inp)<=len(roomList) and int(inp)>0: # 제대로 된 번호인지 검증
            break
        print("존재하지 않는 방입니다.")
        print(roomList)
    msg = "enter"
    s.send(msg.encode())
    os.system('cls')
    print("방 제목: "+list(roomList.keys())[int(inp)-1])
    print("나의 닉네임: "+my_nickname)
    print("명령어: /나가기")
    print("-"*100)
    msg = inp+"|"+my_nickname
    s.send(msg.encode())

def print_room():
    os.system('cls')
    print("# 방 목록")
    x = PrettyTable()
    x.field_names = ["번호", "제목", "방장", "인원"]
    cnt = 0;
    for key, value in roomList.items():
        cnt += 1;
        x.add_row([str(cnt), str(key), roomList[key][0],str(len(roomList[key]))])
    print(x)

if __name__ == '__main__':
    print("서버 연결에 성공하였습니다.")
    while True:
        my_nickname = input("사용할 닉네임: ")
        if my_nickname == "":
            print("사용 불가능한 닉네임입니다.")
            continue
        msg = "nickcheck"
        s.send(msg.encode())
        s.send(my_nickname.encode())
        r_msg = s.recv(BUFSIZE).decode()
        
        if r_msg == "True": # 닉네임이 이미 존재하면
            print("이미 사용중인 닉네임입니다.")
        else:
            break
    
    s.send("Load".encode())
    while True: # 방 목록을 로딩하기 위한 반복문
        r_msg = s.recv(BUFSIZE).decode()
        if r_msg=="LoadComplete":
            break
        tmp = r_msg.split("|")
        
        roomList[tmp[0]] = tmp[1][1:len(tmp[1])-1].replace("'", "").replace(" ", "").split(",")

    r_t = threading.Thread(target=receive_msg, args=())
    r_t.demon = True
    r_t.start()
    print_room()
    print(my_nickname+"님 환영합니다.")
    print("원하시는 작업을 선택해주세요.")
    print("1: 방 선택")
    print("2: 방 만들기")
    print("3: 종료하기")
    while True: # 선택을 위한 반복문
        sel = input("선택: ")
        if sel == "1":
            mode = 2
            select_room()
        elif sel == "2":
            mode = 2
            create_room()
        elif sel == "3":
            s.close()
            quit()
        else:
            print("올바른 입력이 아닙니다.")
            continue
        break

    s_t = threading.Thread(target=send_msg, args=())
    s_t.demon = True
    s_t.start()

    s_t.join()
    r_t.join()
