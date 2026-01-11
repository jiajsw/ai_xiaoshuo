import io
import concurrent.futures
import asyncio
from pathlib import Path
import threading
from pydub import AudioSegment  # type: ignore
from edge_tts import Communicate  # type: ignore

rate_speed: str = "+30%"
reslt: list[AudioSegment] = []
number: int
voice_type: str = "zh-CN-YunyiMultilingualNeural"
all_text: list[str]

lock = threading.Lock()
lock2 = threading.Lock()


async def generate_segment_audio(text: str, voice: str = voice_type) -> bytes:
    communicate = Communicate(text, voice, rate=rate_speed)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk.get("data", b"")
    return audio_data


async def srt_to_audio(task_index: int):
    with lock:
        sub = all_text[task_index]
    audio_data = await generate_segment_audio(sub, voice=voice_type)

    segment_audio = AudioSegment.from_file(
        io.BytesIO(audio_data),
        format="mp3"
    )
    with lock2:
        reslt[task_index] = segment_audio

    print(f"音频已生成：{task_index}")


def worker_task(task_id: int):
    asyncio.run(srt_to_audio(task_id))


def init_glb_args(file_path: Path):
    text = file_path.read_text(encoding="utf-8").splitlines()
    global all_text, number, reslt
    all_text = [line.strip() for line in text if line.strip() != ""]
    number = len(all_text)
    reslt = [AudioSegment.empty()] * number


def post_process(output_path: Path):
    merged_audio = AudioSegment.empty()
    for seg in reslt:
        merged_audio += seg
        merged_audio += AudioSegment.silent(duration=100)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_audio.export(str(output_path), format="mp3")  # pydub 需要 str 路径


def main(file_path: Path, output_path: Path, speed: str = "+30%"):
    global rate_speed
    rate_speed = speed

    init_glb_args(file_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker_task, i) for i in range(number)]
        concurrent.futures.wait(futures)

    post_process(output_path)
    print("全部完成")


if __name__ == "__main__":
    voice_types = [
        "zh-CN-YunfengNeural",
        "zh-CN-YunhaoNeural",
        "zh-CN-YunjianNeural",
        "zh-CN-YunxiNeural",
        "zh-CN-YunxiaoMultilingualNeural",
        "zh-CN-YunyangNeural",
        "zh-CN-YunyeNeural",
        "zh-CN-YunyiMultilingualNeural",
        "zh-CN-YunzeNeural"
    ]

    # 构建输入文件路径
    txt_file = Path("txt/第0033章-献替可否，无中生有.txt")
    base_dir = Path(r"D:\做视频\大号B站\136-万历明君")
    file_path = base_dir / txt_file

    voice_type = "zh-CN-YunjianNeural"
    file_name = file_path.stem
    output_dir = base_dir / "mp3"
    # output_path = output_dir/f"{file_name}-{voice_type}.mp3"
    output_path = Path(f"{file_name}-{voice_type}.mp3")

    speed = "+40%"

    # 删除已存在的输出文件
    if output_path.exists():
        output_path.unlink()

    main(file_path, output_path, speed=speed)
