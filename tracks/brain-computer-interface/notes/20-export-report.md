# Week 6 Day 20：数据导出与报告生成

## 1. 为什么需要数据导出？

BCI 分析不是"跑完就完"——你需要：

1. **保存中间结果**：滤波后的数据、提取的 Epochs，下次不用重算
2. **导出分析结果**：分类准确率、混淆矩阵，写论文/做演示
3. **生成可读报告**：给导师、客户、同事看，他们不会看代码

```
分析流程中的导出点：

Raw → [滤波] → Filtered.fif ←── 导出点1
                    ↓
              [Epoch提取] → Epochs.fif ←── 导出点2
                               ↓
                         [解码] → results.json ←── 导出点3
                                       ↓
                                 [报告] → report.html ←── 最终输出
```

---

## 2. MNE 数据格式

### 2.1 FIF 格式（MNE 原生）

```python
# 保存
raw.save('filtered_raw.fif', overwrite=True)
epochs.save('epochs.fif', overwrite=True)

# 加载
raw = mne.io.read_raw_fif('filtered_raw.fif', preload=True)
epochs = mne.read_epochs('epochs.fif')
```

**FIF = MNE 的"原生语言"**：
- 保留所有元数据（通道信息、采样率、事件标记）
- 二进制格式，读写快
- 缺点：非 MNE 生态不能直接读

### 2.2 通用格式导出

```python
# 导出为 EDF+（临床标准格式）
raw.export('data.edf', overwrite=True)

# 导出为 BrainVision（EEGLAB 兼容）
raw.export('data.vhdr', overwrite=True)

# 导出为 CSV（通用，但丢失元数据）
import pandas as pd
df = raw.to_data_frame()
df.to_csv('eeg_data.csv', index=False)
```

### 2.3 格式选择指南

| 格式 | 优点 | 缺点 | 场景 |
|------|------|------|------|
| .fif | 保留所有 MNE 元数据 | 只能 MNE 读 | MNE 工作流内部 |
| .edf | 临床标准 | 精度有限(16bit) | 临床/医院 |
| .vhdr | EEGLAB 兼容 | 多文件 | 跨工具 |
| .csv | 通用 | 无元数据 | Excel/R 分析 |
| .hdf5 | 大数据友好 | 需 h5py | 批量处理 |

---

## 3. GUI 导出功能

### 3.1 Export Manager 设计

```python
class ExportManager:
    """数据导出管理器"""
    
    SUPPORTED_FORMATS = {
        'MNE FIF': '.fif',
        'EDF+': '.edf',
        'BrainVision': '.vhdr',
        'CSV': '.csv',
        'HDF5': '.h5',
    }
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
    
    def export_raw(self, filepath, format='fif'):
        """导出 Raw 数据"""
        raw = self.pipeline.filtered or self.pipeline.raw
        if format == 'fif':
            raw.save(filepath, overwrite=True)
        elif format == 'edf':
            raw.export(filepath, overwrite=True)
        elif format == 'csv':
            raw.to_data_frame().to_csv(filepath, index=False)
    
    def export_epochs(self, filepath, format='fif'):
        """导出 Epochs"""
        epochs = self.pipeline.epochs
        if format == 'fif':
            epochs.save(filepath, overwrite=True)
        elif format == 'csv':
            df = epochs.to_data_frame()
            df.to_csv(filepath, index=False)
    
    def export_results(self, filepath, format='json'):
        """导出解码结果"""
        metrics = self.pipeline.metrics
        if format == 'json':
            data = {
                'accuracy': float(metrics.accuracy),
                'kappa': float(metrics.kappa),
                'itr': float(metrics.itr),
                'confusion_matrix': metrics.confusion_matrix.tolist(),
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
    
    def export_plots(self, directory, formats=['png', 'svg']):
        """导出所有图表"""
        os.makedirs(directory, exist_ok=True)
        for name, fig in self.pipeline.figures.items():
            for fmt in formats:
                fig.savefig(os.path.join(directory, f'{name}.{fmt}'),
                           dpi=300, bbox_inches='tight')
```

### 3.2 Qt 文件对话框

```python
class ExportDialog(QDialog):
    """导出对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Data")
        layout = QVBoxLayout(self)
        
        # 选择导出类型
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            'Filtered Data (Raw)',
            'Epochs',
            'Decoding Results',
            'All Plots',
        ])
        layout.addWidget(QLabel("Export Type:"))
        layout.addWidget(self.type_combo)
        
        # 选择格式
        self.format_combo = QComboBox()
        self.format_combo.addItems(['FIF', 'EDF', 'CSV', 'JSON'])
        layout.addWidget(QLabel("Format:"))
        layout.addWidget(self.format_combo)
        
        # 选择路径
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)
        layout.addLayout(path_layout)
        
        # 确认/取消
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Export")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
    
    def _browse(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "All Files (*)"
        )
        if filepath:
            self.path_edit.setText(filepath)
```

---

## 4. 报告生成

### 4.1 MNE Report

MNE 内置了 HTML 报告生成功能：

```python
from mne.report import Report

report = Report(title='BCI Analysis Report')

# 添加各分析步骤
report.add_raw(raw, title='Raw Data', psd=True)
report.add_epochs(epochs, title='Epochs')
report.add_evoked(evoked, titles='ERP')

# 保存为 HTML
report.save('bci_report.html', overwrite=True)
```

### 4.2 自定义 HTML 报告

```python
class BCIReportGenerator:
    """BCI 分析报告生成器"""
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.sections = []
    
    def add_section(self, title, content, figures=None):
        """添加报告章节"""
        self.sections.append({
            'title': title,
            'content': content,
            'figures': figures or [],
        })
    
    def generate_html(self, filepath):
        """生成完整 HTML 报告"""
        html = self._html_header()
        
        for section in self.sections:
            html += f'<h2>{section["title"]}</h2>'
            html += f'<div class="content">{section["content"]}</div>'
            for fig_path in section['figures']:
                html += f'<img src="{fig_path}" style="max-width:100%">'
        
        html += self._html_footer()
        
        with open(filepath, 'w') as f:
            f.write(html)
    
    def _html_header(self):
        return '''<!DOCTYPE html>
<html><head>
<style>
  body { font-family: Arial; max-width: 1000px; margin: auto; 
         background: #1a1a2e; color: #eee; padding: 20px; }
  h1 { color: #4CAF50; border-bottom: 2px solid #4CAF50; }
  h2 { color: #2196F3; margin-top: 30px; }
  .content { background: #16213e; padding: 15px; border-radius: 8px; }
  img { border-radius: 8px; margin: 10px 0; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #444; padding: 8px; text-align: center; }
  th { background: #0f3460; }
</style>
</head><body>
<h1>BCI Analysis Report</h1>'''
    
    def _html_footer(self):
        return '</body></html>'
```

### 4.3 报告内容模板

一份完整的 BCI 分析报告应包含：

```python
def generate_full_report(self, output_dir):
    """生成完整分析报告"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 数据概览
    self.add_section('Data Overview', 
        f'<p>Channels: {len(self.pipeline.raw.ch_names)}</p>'
        f'<p>Sampling Rate: {self.pipeline.raw.info["sfreq"]} Hz</p>'
        f'<p>Duration: {self.pipeline.raw.times[-1]:.1f} s</p>'
    )
    
    # 2. 预处理
    self.add_section('Preprocessing',
        f'<p>Bandpass: {self.pipeline.config.filter_params.l_freq}-'
        f'{self.pipeline.config.filter_params.h_freq} Hz</p>'
        f'<p>Notch: {self.pipeline.config.filter_params.notch_freqs} Hz</p>',
        figures=[f'{output_dir}/filter_effect.png']
    )
    
    # 3. Epoch 提取
    self.add_section('Epoch Extraction',
        f'<p>Valid Epochs: {len(self.pipeline.epochs)}</p>'
        f'<p>Rejected: {self.pipeline.n_rejected}</p>',
        figures=[f'{output_dir}/erp_overlay.png']
    )
    
    # 4. 解码结果
    m = self.pipeline.metrics
    self.add_section('Decoding Results',
        f'<p>Accuracy: {m.accuracy:.1%}</p>'
        f'<p>Kappa: {m.kappa:.3f}</p>'
        f'<p>ITR: {m.itr:.1f} bits/min</p>',
        figures=[f'{output_dir}/confusion_matrix.png',
                 f'{output_dir}/band_topomaps.png']
    )
    
    # 生成 HTML
    self.generate_html(f'{output_dir}/report.html')
```

---

## 5. 批量导出与 Pipeline 可复现性

### 5.1 配置文件驱动

```yaml
# bci_config.yaml
filter:
  l_freq: 1.0
  h_freq: 40.0
  notch_freqs: [50, 100]
  method: fir

epoch:
  tmin: -0.2
  tmax: 0.5
  baseline: [null, 0]
  reject:
    eeg: 100e-6

decode:
  method: lda
  cv_folds: 5

export:
  formats: [fif, csv, json]
  plots: [png, svg]
  report: true
```

### 5.2 一键复现

```python
class ReproduciblePipeline:
    """可复现的 BCI Pipeline"""
    
    def __init__(self, config_path):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
    
    def run(self, data_path, output_dir):
        """一键运行完整 pipeline"""
        # 1. 加载
        raw = mne.io.read_raw_fif(data_path, preload=True)
        
        # 2. 滤波
        cfg = self.config['filter']
        raw.filter(cfg['l_freq'], cfg['h_freq'], method=cfg['method'])
        raw.notch_filter(cfg['notch_freqs'])
        
        # 3. Epoch
        ecfg = self.config['epoch']
        events = mne.find_events(raw)
        epochs = mne.Epochs(raw, events, tmin=ecfg['tmin'],
                           tmax=ecfg['tmax'], baseline=tuple(ecfg['baseline']),
                           reject=ecfg['reject'], preload=True)
        
        # 4. 解码
        # ...
        
        # 5. 导出
        # ...
        
        return results
```

---

## 6. 总结

| 概念 | 核心要点 |
|------|----------|
| FIF 格式 | MNE 原生，保留所有元数据 |
| 通用格式 | EDF(临床) / CSV(通用) / HDF5(大数据) |
| ExportManager | 统一管理所有导出操作 |
| MNE Report | 内置 HTML 报告生成 |
| 自定义报告 | 数据概览 + 预处理 + Epoch + 解码 |
| 配置驱动 | YAML 配置文件 → 一键复现整个 pipeline |

**Week 6 总结**：
- Day 16：Qt GUI 架构（信号-槽、MVC、线程）
- Day 17：滤波与可视化组件集成
- Day 18：事件标记与 Epoch 提取 UI
- Day 19：解码结果与频谱拓扑图
- Day 20：数据导出与报告生成

→ 完整的 BCI 数据分析 GUI 工具！下一步 Week 7：Pipeline 工程化。
