# Week 6 Day 5: Data Export and Report Generation

## 核心概念

### 1. 数据导出

```python
import mne
import numpy as np
import pandas as pd

def export_epochs(epochs, format='csv'):
    """导出 Epochs 数据"""
    if format == 'csv':
        df = epochs.to_data_frame()
        df.to_csv('epochs.csv')

    elif format == 'numpy':
        data = epochs.get_data()
        np.save('epochs.npy', data)

    elif format == 'fif':
        epochs.save('epochs-epo.fif')

    elif format == 'pandas':
        df = epochs.to_data_frame(index=True, scale_time=1000)
        return df
```

### 2. 结果导出

```python
def export_results(pipeline_result, filepath):
    """导出分析结果"""
    import json

    results = {
        'accuracy': pipeline_result.accuracy,
        'itr': pipeline_result.itr,
        'confusion_matrix': pipeline_result.confusion_matrix.tolist(),
        'classifier': str(pipeline_result.classifier)
    }

    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
```

### 3. 报告生成

```python
class ReportGenerator:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def generate(self, output_path):
        import markdown

        md_content = self.build_markdown()
        html = markdown.markdown(md_content)

        with open(output_path, 'w') as f:
            f.write(html)

    def build_markdown(self):
        return f"""
# BCI Analysis Report

## Dataset
- File: {self.pipeline.filepath}
- Channels: {len(self.pipeline.raw.ch_names)}
- Duration: {self.pipeline.raw.times[-1]:.1f}s

## Preprocessing
- Filter: {self.pipeline.filter_params}

## Results
- Accuracy: {self.pipeline.result.accuracy:.3f}
- ITR: {self.pipeline.result.itr:.2f} bits/min

## Epochs
- Total: {len(self.pipeline.epochs)}
- Conditions: {list(self.pipeline.epochs.event_id.keys())}
"""
```

### 4. 图像导出

```python
def export_figures(figures, output_dir):
    """导出所有图像"""
    from pathlib import Path
    output_dir = Path(output_dir)

    for name, fig in figures.items():
        fig.savefig(output_dir / f'{name}.png', dpi=300)
        fig.savefig(output_dir / f'{name}.pdf')
```

### 5. 完整报告模板

```python
def generate_full_report(pipeline, output_dir):
    """生成完整 HTML 报告"""
    from jinja2 import Template

    template = """
    <html>
    <head><title>BCI Analysis Report</title></head>
    <body>
        <h1>BCI Analysis Report</h1>

        <h2>Data Summary</h2>
        <p>Channels: {{ n_channels }}</p>
        <p>Duration: {{ duration }}s</p>

        <h2>Preprocessing</h2>
        <ul>
        {% for step in preprocessing %}
            <li>{{ step }}</li>
        {% endfor %}
        </ul>

        <h2>Results</h2>
        <table>
            <tr><td>Accuracy</td><td>{{ accuracy }}</td></tr>
            <tr><td>ITR</td><td>{{ itr }}</td></tr>
        </table>

        <h2>Figures</h2>
        <img src="psd.png">
        <img src="topomap.png">
    </body>
    </html>
    """
```

## 练习要点

1. 掌握多种格式导出
2. 学会生成分析报告
3. 理解报告模板

## 参考资料

- [MNE 导出](https://mne.tools/stable/auto_tutorials/epochs/plot_epochs_to_dataframe.html)
- [Jinja2 模板](https://jinja.palletsprojects.com/)