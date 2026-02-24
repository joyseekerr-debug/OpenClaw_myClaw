# Video Extractor Skill

视频/音频内容提取技能 - 从在线视频平台提取音频、字幕和转录文本

## 功能

- 下载视频/音频（支持B站、YouTube等）
- 提取字幕/CC字幕
- 音频转文字（Whisper ASR）
- 文本摘要和分析

## 依赖安装

```bash
cd skills/video-extractor
pip install -r requirements.txt

# 如果使用Whisper进行语音识别
pip install openai-whisper
```

## 使用方法

```javascript
const { VideoExtractor } = require('./video-extractor');

const extractor = new VideoExtractor();

// 提取视频信息
const info = await extractor.getInfo('https://b23.tv/xxx');

// 提取字幕
const subtitles = await extractor.extractSubtitles('https://b23.tv/xxx');

// 提取音频并转文字
const transcript = await extractor.transcribe('https://b23.tv/xxx');
```

## 支持平台

- Bilibili (B站)
- YouTube
- 其他 yt-dlp 支持的平台

## 文件说明

- `extractor.js` - 核心提取逻辑
- `transcriber.js` - 语音识别封装
- `index.js` - 主入口
