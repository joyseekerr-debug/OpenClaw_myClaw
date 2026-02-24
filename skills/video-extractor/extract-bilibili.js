const { extractVideoContent } = require('./index');

async function extractBilibiliVideo() {
  const url = 'https://b23.tv/QzlOfdB';
  
  console.log('开始提取B站视频内容...\n');
  
  try {
    const result = await extractVideoContent(url, {
      languages: ['zh-CN'],
      autoSubtitles: true,
      transcribe: true,  // 启用音频转录
      summarize: false,
      language: 'zh',
      model: 'base'  // 使用轻量级模型
    });
    
    console.log('\n=== 提取结果 ===\n');
    
    // 视频信息
    console.log('📺 视频信息:');
    console.log(`  标题: ${result.info?.title}`);
    console.log(`  上传者: ${result.info?.uploader}`);
    console.log(`  时长: ${Math.round(result.info?.duration / 60)}分钟`);
    
    // 字幕/转录内容
    if (result.subtitles?.rawText) {
      console.log('\n📝 字幕内容:');
      console.log(result.subtitles.rawText.substring(0, 2000));
    } else if (result.transcript?.text) {
      console.log('\n🎤 音频转录:');
      console.log(result.transcript.text.substring(0, 2000));
    }
    
    // 保存完整内容到文件
    const fs = require('fs');
    const content = result.subtitles?.rawText || result.transcript?.text || '';
    fs.writeFileSync('video-content.txt', content);
    console.log('\n✅ 完整内容已保存到 video-content.txt');
    
  } catch (error) {
    console.error('提取失败:', error.message);
    console.error(error.stack);
  }
}

extractBilibiliVideo();
