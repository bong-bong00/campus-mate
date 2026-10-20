"""서버 3개(메인·AI·웹 화면)를 한 번에 켠다.

실행: python run_all.py
종료: Ctrl+C (3개가 함께 꺼짐)
"""
import socket
import subprocess
import sys
import time

PY = sys.executable
SERVERS = [
    ("메인 서버", [PY, "-m", "uvicorn", "main_server.app:app", "--port", "8000", "--reload"]),
    ("AI 서버", [PY, "-m", "uvicorn", "ai_server.app:app", "--port", "8001", "--reload"]),
    ("웹 화면", [PY, "-m", "web.main"]),
]


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    busy = [p for p in (8000, 8001, 8080) if port_in_use(p)]
    if busy:
        print(f"포트 {busy}가 이미 사용 중입니다. 서버가 이미 켜져 있는지 확인하세요.")
        print("다른 터미널에서 켜 둔 서버를 Ctrl+C로 끄거나, 그대로 http://127.0.0.1:8080 을 쓰면 됩니다.")
        return
    procs = []
    try:
        for name, cmd in SERVERS:
            print(f"[{name}] 시작")
            procs.append(subprocess.Popen(cmd))
            time.sleep(2)  # 메인 서버가 먼저 뜨도록 잠깐 대기
        print("\n준비 완료: http://127.0.0.1:8080  (끄려면 Ctrl+C)\n")
        while all(p.poll() is None for p in procs):
            time.sleep(1)
        print("서버 하나가 멈췄습니다. 위 오류 메시지를 확인하세요.")
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        print("모든 서버를 종료했습니다.")


if __name__ == "__main__":
    main()
