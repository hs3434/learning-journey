# Week 5 Day 6: Deep Learning in BCI

## 核心概念

### 1. 深度学习优势

- 自动特征学习
- 处理原始数据
- 端到端训练
- 处理复杂模式

### 2. EEGNet

轻量级 CNN 用于 EEG：

```python
import torch
import torch.nn as nn

class EEGNet(nn.Module):
    def __init__(self, n_channels=64, n_times=256, n_classes=2):
        super().__init__()

        # 块1: 时间卷积
        self.block1 = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=(1, 25), padding=(0, 12)),
            nn.BatchNorm2d(16),
            nn.Conv2d(16, 16, kernel_size=(n_channels, 1)),
            nn.BatchNorm2d(16),
            nn.ELU(),
            nn.AvgPool2d(kernel_size=(1, 4)),
            nn.Dropout(0.5)
        )

        # 块2: 深度卷积
        self.block2 = nn.Sequential(
            nn.Conv2d(16, 32, kernel_size=(1, 15), padding=(0, 7)),
            nn.BatchNorm2d(32),
            nn.ELU(),
            nn.AvgPool2d(kernel_size=(1, 8)),
            nn.Dropout(0.5)
        )

        # 分类器
        self.classifier = nn.Sequential(
            nn.Linear(32 * n_times // 32, n_classes),
            nn.Softmax(dim=1)
        )

    def forward(self, x):
        x = self.block1(x)
        x = self.block2(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)
```

### 3. 数据增强

```python
def augment_data(X, y, n_augment=5):
    """数据增强"""
    X_aug = [X]
    y_aug = [y]

    for _ in range(n_augment):
        # 随机时间偏移
        shift = np.random.randint(-10, 10)
        X_shifted = np.roll(X, shift, axis=-1)

        # 随机噪声
        noise = np.random.randn(*X.shape) * 0.1
        X_noisy = X_shifted + noise

        X_aug.append(X_noisy)
        y_aug.append(y)

    return np.concatenate(X_aug), np.concatenate(y_aug)
```

### 4. 训练流程

```python
def train_model(model, train_loader, test_loader, epochs=100):
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        for X, y in train_loader:
            optimizer.zero_grad()
            output = model(X)
            loss = criterion(output, y)
            loss.backward()
            optimizer.step()

        # 评估
        model.eval()
        accuracy = evaluate(model, test_loader)
```

## 常用模型

| 模型 | 特点 |
|------|------|
| EEGNet | 轻量、高效 |
| DeepCNN | 深度CNN |
| ShallowCNN | 浅层CNN |
| SleepStager | 睡眠分期专用 |

## 练习要点

1. 理解 CNN 在 EEG 上的应用
2. 掌握 EEGNet 结构
3. 学会数据增强方法

## 参考资料

- [EEGNet 论文](https://arxiv.org/abs/1611.08024)
- [Deep Learning for EEG](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6185604/)