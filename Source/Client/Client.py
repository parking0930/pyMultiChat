import threading
import os
import socket
from prettytable import PrettyTable # pip install PrettyTable 로 설치 후 사용 가능
from time import sleep

# 서버 PORT
port = 2500
# {서버 IP, PORT}
address = ("localhost", port)
# 버퍼 크기
BUFSIZE = 1024

# 방 목록을 담을 딕셔너리, {방 제목:[닉네임1, 닉네임2, ...]} 형태로 사용
roomList = {}
# 내 닉네임을 설정할 변수
my_nickname = ""

# IPv4, TCP 방식의 클라이언트 소켓 생성
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 미리 세팅해둔 서버 정보로 접속 요청
s.connect(address)
# 모드 설정(1은 채팅방 입장 전 2는 입장 후)
mode = 1

# 메시지를 지속적으로 수신받을 스레드 전용 함수
def receive_msg():
    while True:
        # 서버로부터 메시지 수신
        r_msg = s.recv(BUFSIZE)
        # 빈 메시지 수신 시 종료
        if not r_msg:
            break
        # 채팅방 입장 전인 경우
        if mode==1:
            # 수신한 메시지가 refresh이면(방 새로고침 시작 매사지)
            if r_msg.decode()=="refresh":
                # 전역 변수 roomList 사용
                global roomList
                # roomList 빈 딕셔너리로 초기화
                roomList = {}
                # 방 목록을 로딩하기 위한 반복문
                while True:
                    # 서버로부터 메시지 수신
                    r_msg = s.recv(BUFSIZE).decode()
                    # 해당 메시지가 방 목록 로딩이 끝났다는 메시지이면
                    if r_msg=="LoadComplete":
                        # 반복문 종료(방 새로고침 작업 종료)
                        break
                    # 해당 메시지가 방 목록이면 |을 기준으로 분리
                    tmp = r_msg.split("|")
                    # roomList에 해당 방과 유저 정보를 수신한 데이터를 가공하여 추가
                    roomList[tmp[0]] = tmp[1][1:len(tmp[1])-1].replace("'", "").replace(" ", "").split(",")
                # 방 목록을 재출력 해주는 함수 실행
                print_room()
                # 방 선택을 위한 메시지 콘솔 재출력
                print(my_nickname+"님 환영합니다.")
                print("원하시는 작업을 선택해주세요.")
                print("1: 방 선택")
                print("2: 방 만들기")
                print("3: 종료하기\n선택: ", end="")
        # 채팅방 입장 후인 경우
        elif mode==2:
            # :또는 [SYSTEM] 메시지가 아닌 경우(방에 수신된 메시지가 아닐 경우)
            if r_msg.decode().find(':')==-1 and r_msg.decode().find('[SYSTEM]')==-1:
                # 이후는 처리하지 않고 반복문 처음으로
                continue
            # 메시지 수신 시 기존 inp 메시지 형태가 이상해지는 것을 방지 하기 위해
            # inp 메시지 길이를 측정하여 덮어쓰고 수신한 메시지 출력하는 부분
            print("", end="\r", flush=True)
            print(" "*(len(my_nickname)*2+2), end="")
            print("", end="\r", flush=True)
            print("%s\n%s:" %(r_msg.decode(), my_nickname), end="")

# 방 입장 후 사용할 메시지 전송을 위한 스레드 전용 함수 
def send_msg():
    # 첫 호출인지 구분하기 위한 내부 state 변수 0으로 초기화
    state = 0

    # 지속적으로 입력을 하기 위한 반복문
    while True:
        # 0.01초 대기
        sleep(0.01)
        # 첫 실행인 경우
        if state == 0:
            # state 1로 설정
            state = 1
            # 이전 콘솔 메시지 덮어쓰도록 설정
            print("", end="\r", flush=True)
        # 닉네임: 형태로 채팅 입력 받음
        data = input(my_nickname+":")
        # 송신할 메시지가 /나가기 인 경우
        if data == "/나가기":
            # 내(클라이언트) 소켓 종료
            s.close()
            # 함수(스레드) 종료
            return
        # 명령어가 아닌 일반 채팅인 경우, 닉네임:채팅 내용으로 송신 메시지 설정
        data = my_nickname+":"+data
        # 해당 메시지 서버로 송신
        s.send(data.encode())
    # 반복문 탈출 시 접속 종료
    s.close()

# 생성하려는 방이 존재하는지 검증하는 함수
def isRoomExist(roomName):
    # 방 개수만큼 반복
    for key, value in roomList.items():
        # 인수로 받은 방 제목과 일치하는 방이 있다면
        if key == roomName:
            # 생성 불가(True) 반환
            return True
    # 중복되는 방이 없다면 생성 가능(False) 반환
    return False

# 방을 만들기 위해 사용하는 함수
def create_room():
    # 방 생성을 시작한다는 메시지(create) 생성
    msg = "create"
    # 서버에 해당 메시지 송신
    s.send(msg.encode())
    # 유효한 방 제목 입력 시까지 반복
    while True:
        # 방 제목 입력 받음
        roomName = input("방 제목: ")
        # 중복되지 않고 빈 제목이 아닐 경우
        if not isRoomExist(roomName) and roomName != "":
            # 반복문 종료
            break
        # 중복 또는 빈 제목 입력 시
        else:
            # 올바른 제목 입력 콘솔 메시지 출력
            print("올바른 제목을 입력해주세요.")
    # '입력받은 방 제목|내 닉네임' 형태로 메시지 설정
    msg = roomName+"|"+my_nickname
    # 해당 메시지 서버로 송신
    s.send(msg.encode())
    # 콘솔 화면 청소(clear)
    os.system('cls')
    # 방 UI 콘솔 출력
    print("방 제목: "+ roomName)
    print("나의 닉네임: "+my_nickname)
    print("명령어: /나가기")
    print("-"*100)
    # 방 생성 메시지 콘솔 출력
    print("[SYSTEM] "+my_nickname+"님이 방을 생성하셨습니다.")

# 방을 선택하기 위한 함수
def select_room():
    # 유효한 방 번호를 입력할 때까지 반복
    while True:
        # 방 번호 입력 받음
        inp = input("입장할 방 번호를 선택하세요:")
        # 제대로 된 방 번호 이면
        if int(inp)<=len(roomList) and int(inp)>0:
            # 반복문 탈출
            break
        # 잘못된 방 번호이면 오류 메시지 출력
        print("존재하지 않는 방입니다.")
    # 방에 입장을 시작한다는 메시지(enter) 생성
    msg = "enter"
    # 해당 메시지 송신
    s.send(msg.encode())
    # 콘솔 화면 청소(clear)
    os.system('cls')
    # 방 UI 콘솔 출력
    print("방 제목: "+list(roomList.keys())[int(inp)-1])
    print("나의 닉네임: "+my_nickname)
    print("명령어: /나가기")
    print("-"*100)
    # '방 번호|내 닉네임' 형태의 메시지 생성
    msg = inp+"|"+my_nickname
    # 방 입장을 위해 해당 메시지 송신
    s.send(msg.encode())

# 방 목록을 출력하는 함수
def print_room():
    # 콘솔 화면 청소(clear)
    os.system('cls')
    ######## 방 정보 출력 ########
    print("# 방 목록")
    x = PrettyTable() # prettytable 사용, 방 목록 이쁘게 출력 위함
    x.field_names = ["번호", "제목", "방장", "인원"]
    cnt = 0; # 방 번호 지정을 위한 cnt 변수
    for key, value in roomList.items():
        cnt += 1;
        x.add_row([str(cnt), str(key), roomList[key][0],str(len(roomList[key]))])
    print(x)
    ###############################

# 클라이언트 정보 설정 이후 초기 실행 부분(main)
if __name__ == '__main__':
    # 서버 연결 성공 메시지 콘솔 출력
    print("서버 연결에 성공하였습니다.")
    
    # 유효한 닉네임을 입력할 때까지 반복
    while True:
        # 사용할 닉네임 수신
        my_nickname = input("사용할 닉네임: ")
        # 빈 닉네임 입력 시
        if my_nickname == "":
            # 사용 불가 메시지 콘솔 출력
            print("사용 불가능한 닉네임입니다.")
            # 반복문 처음부터 다시 실행
            continue
        # 빈 닉네임이 아니면
        # 닉네임 체크를 시작한다는 메시지(nickcheck) 메시지 생성
        msg = "nickcheck"
        # 해당 메시지 서버로 송신
        s.send(msg.encode())
        # 입력한 닉네임 인코딩하여 송신
        s.send(my_nickname.encode())
        # 중복 검사 여부 수신
        r_msg = s.recv(BUFSIZE).decode()
        # 해당 닉네임이 이미 존재하면
        if r_msg == "True":
            # 사용중인 닉네임 메시지 콘솔 출력
            print("이미 사용중인 닉네임입니다.")
        # 해당 닉네임이 중복이 아니면
        else:
            # 반복문 종료
            break

    # 방 목록 로딩을 시작한다는 메시지 송신
    s.send("Load".encode())
    # 방 목록을 수신하기 위한 반복문
    while True:
        # 서버로부터 메시지 수신
        r_msg = s.recv(BUFSIZE).decode()
        # 방 목록 로드 완료 메시지(LoadComplete) 수신 시
        if r_msg=="LoadComplete":
            # 반복문 종료
            break
        
        # 방 정보 수신 시
        # |을 기준으로 문자열 분리(방 제목|문자열화된 유저목록)
        tmp = r_msg.split("|")

        # 방 목록에 해당 방 정보 추가
        roomList[tmp[0]] = tmp[1][1:len(tmp[1])-1].replace("'", "").replace(" ", "").split(",")

    # 메시지를 수신하기 위한 수신 전용 스레드 생성
    r_t = threading.Thread(target=receive_msg, args=())
    # 프로그램 종료 시 스레드도 종료되도록 설정
    r_t.daemon = True
    # 수신 스레드 시작
    r_t.start()
    # 방 목록 출력
    print_room()
    # 방 선택을 위한 메시지 콘솔 출력
    print(my_nickname+"님 환영합니다.")
    print("원하시는 작업을 선택해주세요.")
    print("1: 방 선택")
    print("2: 방 만들기")
    print("3: 종료하기")
    # 옵션 선택을 위한 반복문
    while True:
        # 옵션 입력 받음
        sel = input("선택: ")
        # 1번(방 선택) 기능 선택 시
        if sel == "1":
            # mode를 2로 설정(1은 채팅방 입장 전 2는 입장 후)
            mode = 2
            # 방 선택을 위한 함수 실행
            select_room()
        # 2번(방 만들기) 기능 선택 시
        elif sel == "2":
            # mode를 2로 설정(1은 채팅방 입장 전 2는 입장 후)
            mode = 2
            # 방 생성을 위한 함수 실행
            create_room()
        # 3번(종료하기) 기능 선택 시
        elif sel == "3":
            # 소켓 접속 종료
            s.close()
            # 프로그램 종료
            quit()
        # 옵션 선택이 아닌 경우
        else:
            # 오류 메시지 콘솔 출력
            print("올바른 입력이 아닙니다.")
            # 반복문 처음부터 다시 실행
            continue
        break

    # 방 생성, 입장이 완료되면 실행 되는 부분
    # 채팅 송신을 위한 스레드 생성
    s_t = threading.Thread(target=send_msg, args=())
    # 프로그램 종료 시 스레드도 종료되도록 설정
    s_t.daemon = True
    # 송신 스레드 실행
    s_t.start()

    # 송신 스레드 종료 시까지 대기
    s_t.join()
    # 수신 스레드 종료 시까지 대기
    r_t.join()
