@echo off
chcp 65001 >nul
echo ==========================================
echo 股价预测系统 - 测试执行批处理
echo ==========================================
echo.

echo [1/4] 检查Python环境...
python --version 2>nul
if errorlevel 1 (
    echo 错误: 未找到Python，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

echo.
echo [2/4] 检查项目目录...
cd /d "%~dp0"
echo 当前目录: %cd%

echo.
echo [3/4] 安装依赖...
pip install pandas numpy requests -q
if errorlevel 1 (
    echo 警告: 依赖安装失败，尝试继续...
)

echo.
echo [4/4] 执行测试...
python run_tests.py

echo.
echo ==========================================
echo 测试执行完成
echo ==========================================
pause
