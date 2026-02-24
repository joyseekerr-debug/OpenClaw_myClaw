const { VideoExtractor } = require('./extractor');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

async function extractWithDirectDownload() {
  const url = 'https://b23.tv/QzlOfdB';
  const extractor = new VideoExtractor();
  
  console.log('尝试直接下载视频并提取音频...\n');
  
  try {
    // 1. 获取视频信息
    const info = await extractor.getInfo(url);
    console.log('✅ 视频信息:');
    console.log(`   标题: ${info.title}`);
    console.log(`   时长: ${Math.round(info.duration / 60)}分钟`);
    
    // 2. 尝试下载视频（不转码，直接下载）
    console.log('\n📥 下载视频中...');
    const videoId = `bilibili_${Date.now()}`;
    const outputPath = path.join(extractor.tempDir, videoId);
    
    // 使用 yt-dlp 下载（不指定格式，自动选择）
    const downloadCmd = `${extractor.ytDlpPath} -o "${outputPath}.%(ext)s" "${url}"`;
    
    console.log(`   执行: ${downloadCmd}`);
    
    await execAsync(downloadCmd, { timeout: 300000 });
    
    // 查找下载的文件
    const files = fs.readdirSync(extractor.tempDir);
    const videoFile = files.find(f => f.startsWith(videoId));
    
    if (!videoFile) {
      throw new Error('视频下载失败');
    }
    
    const videoPath = path.join(extractor.tempDir, videoFile);
    console.log(`✅ 视频下载完成: ${videoFile}`);
    
    // 3. 尝试使用 whisper 直接转录视频
    console.log('\n🎤 开始音频转录（这可能需要几分钟）...');
    
    const pythonPath = 'C:\\Users\\Jhon\\AppData\\Local\\Programs\\Python\\Python311\\python.exe';
    const transcriptCmd = `${pythonPath} -c "
import whisper
import json

model = whisper.load_model('base')
result = model.transcribe('${videoPath.replace(/\\/g, '\\\\')}', language='zh', verbose=False)

output = {
    'text': result['text'],
    'segments': result['segments'],
    'language': result['language'],
    'duration': result['segments'][-1]['end'] if result['segments'] else 0
}
print(json.dumps(output, ensure_ascii=False))
"`;
    
    const { stdout } = await execAsync(transcriptCmd, { timeout: 600000 });
    const transcript = JSON.parse(stdout);
    
    console.log('\n=== 转录结果 ===\n');
    console.log(transcript.text);
    
    // 保存到文件
    fs.writeFileSync('video-transcript.txt', transcript.text);
    console.log('\n✅ 完整转录已保存到 video-transcript.txt');
    
    // 4. 生成摘要
    console.log('\n📝 生成内容摘要...');
    const summary = generateSummary(transcript.text);
    console.log(summary);
    
    // 清理
    fs.unlinkSync(videoPath);
    
  } catch (error) {
    console.error('❌ 提取失败:', error.message);
    
    if (error.message.includes('ffmpeg')) {
      console.log('\n💡 提示: FFmpeg 未正确安装，尝试手动安装:');
      console.log('   1. 访问 https://ffmpeg.org/download.html');
      console.log('   2. 下载 Windows build');
      console.log('   3. 解压并添加到 PATH');
    }
  }
}

function generateSummary(text) {
  // 简单的摘要生成
  const sentences = text.split(/[。！？.!?]/).filter(s => s.trim().length > 10);
  
  // 提取关键句（包含关键词的句子）
  const keywords = ['agent', '配置', '部署', '身份', '路由', '状态', 'token', '多'];
  const keySentences = sentences.filter(s => 
    keywords.some(k => s.toLowerCase().includes(k))
  );
  
  return {
    totalSentences: sentences.length,
    keyPoints: keySentences.slice(0, 10),
    preview: text.substring(0, 500) + '...'
  };
}

extractWithDirectDownload();
