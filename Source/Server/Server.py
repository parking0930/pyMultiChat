import threading
from socket import *
from time import sleep

# 서버 IP
server_host = "127.0.0.1"
# 서버 PORT
port = 2500
# 버퍼 크기
BUFSIZE = 1024

# {방 제목:{닉네임:소켓}} 형태로 사용
roomList = {}
# 접속한 소켓만 저장하는 리스트
sockList = []
# {닉네임:소켓} 형태로 저장하여 사용
nicknameList = {}

# 플레이어가 속한 방 반환하는 함수
def findRoomByNick(nickname):
    # 방 개수만큼 반복
    for key, value in roomList.items():
        # 방 내부 플레이어 수만큼 반복
        for key2, value2 in roomList[key].items():
            # 키가 인수로 받은 닉네임과 같으면
            if key2 == nickname:
                # 해당 방 반환
                return roomList[key]

# 소켓을 인수로 받아 플레이어 내보내는 함수
def exitPlayerBySocket(c_sock):
    # 전역변수 roomList 사용
    global roomList
    # 방 개수만큼 반복
    for key, value in roomList.items():
        # 방 내부 플레이어 수만큼 반복
        for key2, value2 in roomList[key].items():
            # 값이 인수로 받은 소켓과 같으면
            if value2 == c_sock:
                # 해당 방의 플레이어 제거
                del roomList[key][key2]
                # 해당 방, 내보낸 유저 닉네임, True 반환
                return roomList[key], key2, True
    # 못찾을 시 빈 방, 빈 문자열, False 반환
    return {}, "", False

# 모든 클라이언트에 메시지 보내는 함수
def sendAllClients(message):
    # 접속한 소켓 수만큼 반복하여 꺼냄
    for c_sock in sockList:
        # 꺼낸 소켓에게 인수로 받은 메시지 전송
        c_sock.send(message.encode())

# 닉네임 중복 여부 반환하는 함수
def isNicknameExist(nickname):
    # 접속한 유저 닉네임 수만큼 반복
    for key, value in nicknameList.items():
        # 인수로 받은 닉네임이랑 같으면
        if key == nickname:
            # True 반환
            return True
    # 인수로 받은 닉네임을 찾지 못했을 경우 False 반환
    return False

# 소켓을 인수로 받아 닉네임 삭제하는 함수
def delNickBySocket(c_sock):
    # 전역변수 nicknameList 사용
    global nicknameList
    # 접속한 유저 닉네임 수만큼 반복
    for key, value in nicknameList.items():
        # 인수로 받은 소켓 찾을 시
        if value == c_sock:
            # 해당 소켓에 매치된 닉네임 삭제 알림
            print("[DELETE NICKNAME] "+key)
            # 해당 소켓에 매치된 닉네임 삭제
            del nicknameList[key]
            # for문 중단(함수 종료)
            break

# 모든 유저에게 방 새로고침 메시지를 방송하는 함수
def refreshRoom():
    # 모든 클라이언트에 refresh 메시지 전송(새로고침을 시작한다는 메시지)
    sendAllClients("refresh")
    # 방 개수만큼 반복
    for key, value in roomList.items():
        # '방제목|문자열화 한 유저리스트' 형태로 메시지 생성
        msg = key+"|"+str(list(value.keys()))
        # 해당 메시지를 모든 클라이언트에 전송
        sendAllClients(msg)
        # 0.1초 대기
        sleep(0.1)
    # 모든 클라이언트에 LoadComplete 메시지 전송(방 새로고침이 끝났다는 메시지)
    sendAllClients("LoadComplete")

# 빈 방을 찾아서 제거하는 함수
def checkEmptyRoom():
    # 전역변수 roomList 사용
    global roomList
    # 방 개수만큼 반복
    for key, value in roomList.items():
        # 해당 방이 비었으면
        if len(value) == 0:
            # 삭제 알림 메시지 출력
            print("[DELETE ROOM] '"+key+"' 방이 삭제되었습니다.")
            # 해당 방 삭제
            del roomList[key]
            # 함수 종료
            return

# 클라이언트마다 할당하는 스레드 전용 함수
def client_handler(c_sock, c_host, c_port):
    # 접속한 소켓 정보 리스트에 추가
    sockList.append(c_sock)
    try:
        # 접속 종료 시 까지 반복
        while True:
            # 클라이언트로부터 메시지 수신
            data = c_sock.recv(BUFSIZE).decode()
            
            # 수신한 데이터가 없을 시 반복문 종료
            if not data:
                break

            # 방 목록 전송을 요청한 경우
            if data == "Load":
                # 방 개수만큼 반복
                for key, value in roomList.items():
                    # '방제목|문자열화 한 유저리스트' 형태로 메시지 생성
                    msg = key+"|"+str(list(value.keys()))
                    # 요청한 클라이언트에만 방 목록을 담은 메시지 송신
                    c_sock.send(msg.encode())
                    # 0.1초 대기
                    sleep(0.1)
                # 해당 클라이언트에 LoadComplete 메시지 전송(방 새로고침이 끝났다는 메시지)
                c_sock.send("LoadComplete".encode())
                # 다음 반복으로 이동
                continue
            # 방 생성을 요청한 경우
            elif data == "create":
                # 제목|닉네임 형태로 메시지 수신
                data = c_sock.recv(BUFSIZE).decode().split("|")
                # 방 만들고 추가
                roomList[data[0]] = {data[1]:c_sock}
                # 방 생성 알림 출력
                print("[CREATE ROOM] '"+data[0]+"' 방이 생성되었습니다.")
                # 모든 클라이언트에 새로고침 방송
                refreshRoom()
                # 다음 반복으로 이동
                continue
            # 방 입장을 요청한 경우
            elif data == "enter":
                # 방 번호|닉네임 형태 메시지 수신
                data = c_sock.recv(BUFSIZE).decode().split("|")
                # 해당 방 번호에 맞는 딕셔너리에 닉네임:소켓 형태로 추가 (입장 처리완료)
                roomList[list(roomList.keys())[int(data[0])-1]][data[1]] = c_sock
                # 입장을 요청한 방의 유저 수만큼 반복
                for key, value in roomList[list(roomList.keys())[int(data[0])-1]].items():
                    # 해당 방에 있는 유저에게 입장 알림 메시지 송신
                    roomList[list(roomList.keys())[int(data[0])-1]][key].send(("[SYSTEM] "+data[1]+"님이 입장하셨습니다.").encode())
                # 모든 유저에게 방 새로고침 메시지 전송
                refreshRoom()
                # 다음 반복으로 이동
                continue
            # 닉네임 체크를 요청한 경우
            elif data == "nickcheck":
                # 닉네임 수신
                data = c_sock.recv(BUFSIZE).decode()
                # 닉네임이 중복될 시
                if isNicknameExist(data):
                    # 해당 클라이언트에 중복(True)된다는 메시지 송신
                    c_sock.send("True".encode())
                # 닉네임이 중복되지 않을 시
                else:
                    # 닉네임 딕셔너리에 '닉네임:소켓' 형태로 삽입
                    nicknameList[data]=c_sock
                    # 해당 클라이언트에 중복 되지 않는다(False)는 메시지 송신
                    c_sock.send("False".encode())
                    # 닉네임 생성 알림 콘솔에 출력
                    print("[ADD NICKNAME] "+data)
                # 다음 반복으로 이동
                continue
            # 채팅 요청 시(방에 속한 경우 해당)
            else:
                # 수신한 메시지 :을 기준으로 분리(닉네임:채팅)
                tmp = data.split(":")
                # 수신한 닉네임이 속한 방을 가져옴
                room = findRoomByNick(tmp[0])
                # 해당 방의 유저 수만큼 반복
                for key, value in room.items():
                    # 유저 닉네임이 본인이 아니면
                    if key != tmp[0]:
                        # 해당 채팅 메시지 전송
                        room[key].send(data.encode())
                # 다음 반복으로 이동
                continue
    # 플레이어가 '/나가기' 또는 강제종료 한 경우
    except Exception as e:
        # 접속을 종료한 유저를 닉네임 목록에서 제거
        delNickBySocket(c_sock)
        # 접속한 소켓 수만큼 반복
        for i in range(0, len(sockList)):
            # 접속을 종료한 소켓 발견 시
            if sockList[i]==c_sock:
                # 해당 소켓을 리스트에서 제거
                del sockList[i]
                # for문 종료
                break
        # 해당 소켓이 속해있는 방이 있으면 목록에서 제거
        room, nickname, result = exitPlayerBySocket(c_sock)
        # 방에 속해있었고 내보내는데 성공한 경우
        if result:
            # 해당 방의 유저 수만큼 반복
            for key, value in room.items():
                # 해당 유저의 퇴장 알림을 송신
                room[key].send(("[SYSTEM] "+nickname+"님이 퇴장하셨습니다.").encode())
        # 빈 방이 있는지 체크하고 비었으면 방 제거
        checkEmptyRoom()
        # 모든 클라이언트에 방 목록 새로고침 방송
        refreshRoom()
    # 해당 클라이언트 연결 종료
    c_sock.close()
    # 접속 종료한 클라이언트 IP, PORT와 함께 알림 콘솔에 출
    print("[DISCONNECTED] IP: %s, PORT: %s" %(c_host, c_port))

# 초기 실행 부분(main)
if __name__ == '__main__':
    # 서버 준비중 콘솔 출력
    print("채팅 서버 준비중...")
    # IPv4, TCP 방식으로 서버 소켓 생성
    serv_sock = socket(AF_INET, SOCK_STREAM)
    # 소켓에 IP, PORT 할당
    serv_sock.bind((server_host, port))
    # 소켓 연결 요청 10개까지 대기
    serv_sock.listen(10)
    # 채팅 서버 오픈 알림 콘솔 출력
    print("채팅 서버가 오픈되었습니다!")

    # 클라이언트 접속을 수신할 반복문
    while True:
        # 클라이언트 접속 받음
        c_sock, (c_host, c_port) = serv_sock.accept()
        # 접속한 클라이언트 IP, PORT 콘솔 출력
        print("[CONNECTED] IP: %s, PORT: %s" %(c_host, c_port))
        # 접속한 클라이언트 전용 스레드 생성
        t = threading.Thread(target=client_handler, args=(c_sock, c_host, c_port))
        # 프로그램 종료 시 스레드도 종료되도록 설정
        t.daemon = True
        # 스레드 시작
        t.start()
