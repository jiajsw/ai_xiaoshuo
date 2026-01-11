import os
import io
import concurrent.futures
import re
import asyncio
from pathlib import Path
import threading
from pydub import AudioSegment  # type: ignore
from edge_tts import Communicate  # type: ignore

rate_speed: str = "+30%"
reslt: list[AudioSegment] = []
number: int
# 语音类型
voice_type: str = "zh-CN-YunyiMultilingualNeural"
# 结果文件夹
output_folder = "output"

all_text: list[str]


lock = threading.Lock()
lock2 = threading.Lock()


async def generate_segment_audio(text, voice=voice_type):
    # 打印速度
    # print(f" 速度：{rate}")
    communicate = Communicate(text, voice, rate=rate_speed)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk.get("data", b"")

    return audio_data


async def srt_to_audio(task_index: int):
    with lock:
        global all_text
        sub = all_text[task_index]
    audio_data = await generate_segment_audio(sub, voice=voice_type)

    segment_audio = AudioSegment.from_file(
        io.BytesIO(audio_data),
        format="mp3"  # edge-tts默认输出mp3格式
    )
    # 直接保存到本地文件
    # file_name = f"{output_folder}/{task_index}.mp3"
    # segment_audio.export(file_name, format="mp3")
    with lock2:
        reslt[task_index] = segment_audio

    print(f"音频已生成：{task_index}")
    # length_ms = len(segment_audio)
    # 生成文件名
    # file_name = f"{output_folder}/{task_index}-{sub.index}-{sub.audio_length}-{length_ms}.mp3"
    # segment_audio.export(file_name, format="mp3")
    # print(f"音频已保存至：{file_name}")


def worker_task(task_id: int):
    asyncio.run(srt_to_audio(task_id))


def init_glb_args(file_path: str):
    # 创建文件夹
    # os.makedirs(output_folder, exist_ok=True)
    # # 清理文件夹中的内容
    # for filename in os.listdir(output_folder):
    #     file_path = os.path.join(output_folder, filename)
    #     try:
    #         if os.path.isfile(file_path) or os.path.islink(file_path):
    #             os.unlink(file_path)
    #     except Exception as e:
    #         print(f"Failed to delete {file_path}. Reason: {e}")

    # 读取文本文件 file_path
    # 读取全部行
    text = Path(file_path).read_text(encoding="utf-8").splitlines()

    # 按行处理,去掉首尾全部不可见字符,然后将 空字符串去掉,赋值到 all_text 中
    global all_text
    all_text = [line.strip() for line in text if line.strip() != ""]

    global number
    number = len(all_text)
    global reslt
    # 正确初始化 reslt
    reslt = [AudioSegment.empty()] * number


def post_process(output_path: str):
    # 合并所有音频
    merged_audio = AudioSegment.empty()

    # 合并音频  result[i]
    for i in reslt:
        merged_audio += i
        # 添加 0.2 秒的间隔
        merged_audio += AudioSegment.silent(duration=100)
    # 保存合并后的音频
    merged_audio.export(output_path, format="mp3")


def main(file_path: str, output_path: str, speed: str = "+30%"):
    init_glb_args(file_path)
    global rate_speed
    rate_speed = speed

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # 提交任务
        futures = [executor.submit(worker_task, i) for i in range(number)]
        # 等待所有任务完成
        concurrent.futures.wait(futures)

    post_process(output_path)
    print("全部完成")


# 运行
if __name__ == "__main__":

    voice_types = [
        "zh-CN-YunfengNeural",
        "zh-CN-YunhaoNeural",
        "zh-CN-YunjianNeural",
        # "zh-CN-YunjieNeural",
        "zh-CN-YunxiNeural",
        # "zh-CN-YunxiaNeural",
        "zh-CN-YunxiaoMultilingualNeural",  # √
        "zh-CN-YunyangNeural",
        "zh-CN-YunyeNeural",
        "zh-CN-YunyiMultilingualNeural",
        "zh-CN-YunzeNeural"
    ]
    # 遍历
    # for voice in voice_types:
    #     file_path = "神秘复苏-第1章"
    #     output_path = f"{voice}-{file_path}-output.mp3"
    #     voice_type = voice
    #     # 删除
    #     if os.path.exists(output_path):
    #         os.remove(output_path)
    #     main(file_path, output_path)
    # txt = "第0010章-贪腐枉法，日讲太甲"
    txt = rf"txt\第0049章-南来北往，诈以邀赏.txt"
    file_path = rf"D:\做视频\大号B站\136-万历明君\{txt}"
    # file_path = rf"C:\Users\jsw\Documents\00project\wen_an\团结壬与LGBT.txt"
    voice_type = "zh-CN-YunjianNeural"
    file_name = os.path.basename(file_path).replace(".txt", "")
    output_path = fr"D:\做视频\大号B站\136-万历明君\mp3\{file_name}-{voice_type}.mp3"
    # output_path = fr"{file_name}-{voice_type}.mp3"

    speed = "+60%"
    # 删除
    if os.path.exists(output_path):
        os.remove(output_path)
    main(file_path, output_path, speed=speed)
