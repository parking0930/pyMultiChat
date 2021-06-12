import threading
from socket import *
from time import sleep

server_host = "127.0.0.1"
port = 2500
BUFSIZE = 1024

roomList = {} # {방 제목:{닉네임:소켓}} 형태로 사용
sockList = []
nicknameList = {}

def findRoomByNick(nickname): # 플레이어가 속한 방 반환
    for key, value in roomList.items():
        for key2, value2 in roomList[key].items():
            if key2 == nickname:
                return roomList[key]

def exitPlayerBySocket(c_sock): # 소켓을 인수로 받아 플레이어 내보냄
    global roomList
    for key, value in roomList.items():
        for key2, value2 in roomList[key].items():
            if value2 == c_sock:
                del roomList[key][key2]
                return roomList[key], key2, True
    return {}, "", False

def sendAllClients(message): # 모든 클라이언트에 메시지 보냄
    for c_sock in sockList:
        c_sock.send(message.encode())

def isNicknameExist(nickname): # 닉네임 체크
    for key, value in nicknameList.items():
        if key == nickname:
            return True
    return False

def delNickBySocket(c_sock): # 소켓을 인수로 받아 닉네임 삭제
    global nicknameList
    for key, value in nicknameList.items():
        if value == c_sock:
            print("[DELETE NICKNAME] "+key)
            del nicknameList[key]
            break

def refreshRoom(): # 방 새로고침 메시지를 방송
    sendAllClients("refresh")
    for key, value in roomList.items():
        msg = key+"|"+str(list(value.keys()))
        sendAllClients(msg)
        sleep(0.1)
    sendAllClients("LoadComplete")

def checkEmptyRoom(): # 빈 방을 찾아서 제거
    global roomList
    for key, value in roomList.items():
        if len(value) == 0:
            print("[DELETE ROOM] '"+key+"' 방이 삭제되었습니다.")
            del roomList[key]
            return

def client_handler(c_sock, c_host, c_port): # 클라이언트마다 할당하는 스레드 전용 함수
    sockList.append(c_sock)
    try:
        while True:
            data = c_sock.recv(BUFSIZE).decode()
            if not data:
                break
            if data == "Load": # 방 목록 전송을 요청한 경우
                for key, value in roomList.items():
                    msg = key+"|"+str(list(value.keys()))
                    c_sock.send(msg.encode())
                    sleep(0.1) # 클라이언트가 수신할 때까지 대기
                c_sock.send("LoadComplete".encode())
                continue
            elif data == "create": # 방 생성을 요청한 경우
                data = c_sock.recv(BUFSIZE).decode().split("|") # 제목|닉네임
                roomList[data[0]] = {data[1]:c_sock} # 방 만들고 추가
                print("[CREATE ROOM] '"+data[0]+"' 방이 생성되었습니다.")
                refreshRoom()
                continue
            elif data == "enter": # 방 입장을 요청한 경우
                data = c_sock.recv(BUFSIZE).decode().split("|") # 방 번호|닉네임
                roomList[list(roomList.keys())[int(data[0])-1]][data[1]] = c_sock
                #c_sock.send(("방 제목: " +list(roomList.keys())[int(data[0])-1]).encode())
                for key, value in roomList[list(roomList.keys())[int(data[0])-1]].items():
                    roomList[list(roomList.keys())[int(data[0])-1]][key].send(("[SYSTEM] "+data[1]+"님이 입장하셨습니다.").encode())
                refreshRoom()
                continue
            elif data == "nickcheck": # 닉네임 체크를 요청한 경우
                data = c_sock.recv(BUFSIZE).decode()
                if isNicknameExist(data):
                    c_sock.send("True".encode())
                else:
                    nicknameList[data]=c_sock
                    c_sock.send("False".encode())
                    print("[ADD NICKNAME] "+data)
                continue
            else: # 채팅 시, 방에 속한 경우!
                tmp = data.split(":") # 닉네임:채팅
                room = findRoomByNick(tmp[0])
                for key, value in room.items():
                    if key != tmp[0]:
                        room[key].send(data.encode())
                continue
    except Exception as e: # 플레이어가 '/나가기' 또는 강제종료 한 경우
        delNickBySocket(c_sock)
        for i in range(0, len(sockList)):
            if sockList[i]==c_sock:
                del sockList[i]
                break
        room, nickname, result = exitPlayerBySocket(c_sock)
        if result:
            for key, value in room.items():
                room[key].send(("[SYSTEM] "+nickname+"님이 퇴장하셨습니다.").encode())
        checkEmptyRoom()
        refreshRoom()
    c_sock.close()
    print("[DISCONNECTED] IP: %s, PORT: %s" %(c_host, c_port))

if __name__ == '__main__':
    print("채팅 서버 준비중...")
    serv_sock = socket(AF_INET, SOCK_STREAM)
    serv_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serv_sock.bind((server_host, port))
    serv_sock.listen(10)
    print("채팅 서버가 오픈되었습니다!")

    while True:
        c_sock, (c_host, c_port) = serv_sock.accept()
        print("[CONNECTED] IP: %s, PORT: %s" %(c_host, c_port))
        t = threading.Thread(target=client_handler, args=(c_sock, c_host, c_port))
        t.demon = True
        t.start()
