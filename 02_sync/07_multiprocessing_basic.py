from multiprocessing import Process
import time
import os

def task():
    print("PID:", os.getpid())
    time.sleep(2)


if __name__ == "__main__":
    start = time.time()

    p1 = Process(target=task)
    p2 = Process(target=task)


    p1.start()
    p2.start()

    p1.join()
    p2.join()

    print("총 시간:", time.time() - start)
