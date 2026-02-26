import requests
import time
import asyncio

async def fetch(url):
    print("요청 시작")
    response = requests.get(url, verify=False)
    print("응답 길이:", len(response.text))


async def main():
    start = time.time()
    await asyncio.gather(
        fetch("https://httpbin.org/delay/2"),
        fetch("https://httpbin.org/delay/2")
    )

    print("총 시간:", time.time() - start)

asyncio.run(main())