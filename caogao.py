import numpy as np
import matplotlib.pyplot as plt

# 给定参数
Tmax = 243
Ri = [43, 42, 31, 20]  # 东京、悉尼、弗吉尼亚、俄勒冈
Rbase = 44.62
k = 0.453

# 计算累积速率
cumulative_R = np.cumsum(Ri)

# 定义速率函数
def total_rate(sum_R):
    return Tmax * (1 - np.exp(-k * sum_R / Rbase))

# 生成数据点
x = range(1, len(Ri)+1)
y = [total_rate(sum(Ri[:n])) for n in x]

# 绘制曲线
plt.figure(figsize=(10, 6))
plt.plot(x, y, 'bo-', label=f'$R_{{total}} = 243(1-e^{{-0.453 \cdot S/44.62}})$')
plt.axhline(y=Tmax, color='r', linestyle='--', label='Max Threshold (243 Mb/s)')

# 标注节点信息
node_names = ['Tokyo', '+Sydney', '+Virginia', '+Oregon']
for i, (xi, yi) in enumerate(zip(x, y)):
    plt.annotate(f'{node_names[i]}\n{yi:.1f} Mb/s', 
                 (xi, yi), textcoords="offset points", 
                 xytext=(0,10), ha='center')
# 设置中文字体（Windows系统用'SimHei'，Mac/Linux用'WenQuanYi Zen Hei'）
plt.rcParams['font.sans-serif'] = ['SimHei']  # 替换为系统已有的中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
# 图表美化
plt.title('Transmission Rate Aggregation with Increasing Nodes', pad=20)
plt.xlabel('节点数量')
plt.ylabel('总传输速率 (Mb/s)')
plt.xticks(x)
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()