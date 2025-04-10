import numpy as np
from pedalboard import *

# 读取 PCM 文件参数
input_pcm_path = 'test.pcm'
output_pcm_path = 'processed-output.pcm'
samplerate = 16000  # 采样率
dtype = np.int16    # 16位整数
num_channels = 1    # 单声道

# 读取 PCM 数据（16bit 小端 单声道）
with open(input_pcm_path, 'rb') as f:
    raw_data = f.read()
    audio = np.frombuffer(raw_data, dtype=dtype).astype(np.float32) / 32768.0  # 归一化
    audio = np.reshape(audio, (1, -1))  # 转换为形状 (channels, samples)

# 配置“狗叫”效果
board = Pedalboard([
    Compressor(threshold_db=-40, ratio=10),
    LadderFilter(mode=LadderFilter.Mode.LPF12, cutoff_hz=1000),
    Convolution('./woolf.wav', 1),
    PitchShift(semitones=0.0),
    Compressor(threshold_db=-25, ratio=10),
    Gain(gain_db=30),
    Limiter(),
])

# 应用效果器
effected = board(audio, samplerate)

# 反归一化并转换为 int16 写入 PCM 文件
effected = (np.clip(effected, -1.0, 1.0) * 32767.0).astype(np.int16).flatten()

with open(output_pcm_path, 'wb') as f:
    f.write(effected.tobytes())
