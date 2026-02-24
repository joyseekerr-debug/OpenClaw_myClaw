import os

# Create directory structure for investment skills
dirs = [
    'skills/investment/01_basics/docs',
    'skills/investment/01_basics/code',
    'skills/investment/01_basics/tests',
    'skills/investment/02_technical/docs',
    'skills/investment/02_technical/code',
    'skills/investment/02_technical/tests',
    'skills/investment/03_quantitative/docs',
    'skills/investment/03_quantitative/code',
    'skills/investment/03_quantitative/tests',
    'skills/investment/04_risk/docs',
    'skills/investment/04_risk/code',
    'skills/investment/04_risk/tests',
    'skills/investment/05_execution/docs',
    'skills/investment/06_monitoring/docs',
    'skills/investment/07_psychology/docs',
    'skills/investment/08_advanced/docs',
    'memory/learning'
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f'Created: {d}')

print('\n✅ Directory structure created successfully!')
