import threading
import time

def task(name):
    print(f"{name} 시작")
    time.sleep(2)
    print(f"{name} 완료")

start = time.time()

t1 = threading.Thread(target=task, args=("A",))
t2 = threading.Thread(target=task, args=("B",))
t1.start()
t2.start()

t1.join()
t2.join()

print("총 시간:", time.time() - start)