const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs');

const execAsync = promisify(exec);

async function transcribeVideo() {
  const videoPath = 'C:\\Users\\Jhon\\AppData\\Local\\Temp\\video-extractor\\bilibili_1771908851041.f100026.mp4';
  const pythonPath = 'C:\\Users\\Jhon\\AppData\\Local\\Programs\\Python\\Python311\\python.exe';
  
  console.log('🎤 开始转录视频音频...\n');
  console.log('⏳ 这可能需要 5-10 分钟，请耐心等待...\n');
  
  try {
    // 创建 Python 脚本
    const scriptPath = 'C:\\Users\\Jhon\\AppData\\Local\\Temp\\transcribe.py';
    const script = `
import whisper
import json
import sys

print("正在加载 Whisper 模型...", file=sys.stderr)
model = whisper.load_model("base")

print("开始转录...", file=sys.stderr)
result = model.transcribe(r"${videoPath}", language="zh", verbose=True)

output = {
    "text": result["text"],
    "language": result["language"],
    "duration": result["segments"][-1]["end"] if result["segments"] else 0
}

print(json.dumps(output, ensure_ascii=False))
print("转录完成!", file=sys.stderr)
`;
    
    fs.writeFileSync(scriptPath, script);
    
    // 执行转录
    const { stdout, stderr } = await execAsync(
      `${pythonPath} "${scriptPath}"`,
      { timeout: 600000, maxBuffer: 50 * 1024 * 1024 }
    );
    
    // 输出进度信息
    if (stderr) {
      console.log(stderr);
    }
    
    // 解析结果
    const lines = stdout.trim().split('\n');
    const jsonLine = lines.find(l => l.startsWith('{'));
    
    if (jsonLine) {
      const result = JSON.parse(jsonLine);
      
      console.log('\n=== 转录结果 ===\n');
      console.log(result.text);
      
      // 保存到文件
      fs.writeFileSync('video-content.txt', result.text);
      console.log('\n✅ 已保存到 video-content.txt');
      
      return result;
    } else {
      console.log('未找到转录结果');
      console.log('原始输出:', stdout);
    }
    
    // 清理
    fs.unlinkSync(scriptPath);
    
  } catch (error) {
    console.error('❌ 转录失败:', error.message);
    if (error.stderr) console.error(error.stderr);
  }
}

transcribeVideo();
