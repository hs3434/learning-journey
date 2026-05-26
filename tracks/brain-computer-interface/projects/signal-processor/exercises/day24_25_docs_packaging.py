"""
Day 24-25: Docs, Type Hints, Packaging & Engineering
=====================================================
Week 7 Day 4-5 — 文档/类型提示 + 打包/工程化
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon
from matplotlib.gridspec import GridSpec
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# Plot 1 (Day24): Type Hints + Docstring Anatomy
# ============================================================
def plot1_type_hints_docstring():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor='#1a1a2e')
    
    # Left: Type hints benefits
    ax1.set_xlim(0, 7)
    ax1.set_ylim(0, 8)
    ax1.axis('off')
    ax1.set_title('Type Hints: Catch Bugs Before Runtime', color='white', fontsize=11, fontweight='bold')
    
    # Code without type hints
    no_type_rect = FancyBboxPatch((0.3, 4.5), 6.4, 3.0, boxstyle="round,pad=0.1",
                                   facecolor='#F44336', edgecolor='white', alpha=0.3, linewidth=1.5)
    ax1.add_patch(no_type_rect)
    ax1.text(0.5, 7.2, 'Without type hints:', fontsize=9, color='#F44336', fontweight='bold')
    
    code_no = [
        'def filter(data, freq1, freq2):',
        '    # What type is data?',
        '    # float or int for freq?',
        '    # What does it return?',
        '    ...',
        '',
        '# Caller has to GUESS:',
        'filter(my_list, "1", 40)  # BUG: wrong types!',
    ]
    for i, line in enumerate(code_no):
        ax1.text(0.5, 6.8 - i * 0.28, line, fontsize=7, color='white',
                fontfamily='monospace', alpha=0.8)
    
    # Code with type hints
    yes_type_rect = FancyBboxPatch((0.3, 0.5), 6.4, 3.7, boxstyle="round,pad=0.1",
                                    facecolor='#4CAF50', edgecolor='white', alpha=0.3, linewidth=1.5)
    ax1.add_patch(yes_type_rect)
    ax1.text(0.5, 3.9, 'With type hints:', fontsize=9, color='#4CAF50', fontweight='bold')
    
    code_yes = [
        'def bandpass_filter(',
        '    data: np.ndarray,',
        '    l_freq: float,',
        '    h_freq: float,',
        ') -> np.ndarray:',
        '    ...',
        '',
        '# mypy catches errors at CHECK time:',
        '# error: "list" incompatible with "ndarray"',
    ]
    for i, line in enumerate(code_yes):
        ax1.text(0.5, 3.5 - i * 0.28, line, fontsize=7, color='white',
                fontfamily='monospace', alpha=0.8)
    
    # Right: Docstring anatomy
    ax2.set_xlim(0, 7)
    ax2.set_ylim(0, 8)
    ax2.axis('off')
    ax2.set_title('Google-Style Docstring Anatomy', color='white', fontsize=11, fontweight='bold')
    
    sections = [
        (0.3, 6.8, 'One-line summary', '#FFD700', 'What does this function do?'),
        (0.3, 5.8, 'Args:', '#2196F3', 'Name, type, description for each param'),
        (0.3, 4.8, 'Returns:', '#4CAF50', 'Type and meaning of return value'),
        (0.3, 3.8, 'Raises:', '#F44336', 'Which exceptions, and when'),
        (0.3, 2.8, 'Examples:', '#9C27B0', 'Runnable code examples'),
        (0.3, 1.8, 'Notes:', '#607D8B', 'Extra context, references, warnings'),
    ]
    
    for (x, y, label, color, desc) in sections:
        rect = FancyBboxPatch((x, y), 6.4, 0.7, boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='white', alpha=0.5, linewidth=1.5)
        ax2.add_patch(rect)
        ax2.text(x + 0.3, y + 0.45, label, fontsize=9, color='white', fontweight='bold')
        ax2.text(x + 0.3, y + 0.12, desc, fontsize=7, color='white', alpha=0.8)
    
    # Tool labels
    ax2.text(3.5, 1.0, 'Sphinx + napoleon auto-generates API docs from this',
            ha='center', fontsize=8, color='#FFD700', fontstyle='italic')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day24_plot_1.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 2 (Day24): Sphinx Documentation Pipeline
# ============================================================
def plot2_sphinx_pipeline():
    fig, ax = plt.subplots(1, 1, figsize=(14, 6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6)
    ax.axis('off')
    ax.set_title('Sphinx Documentation Pipeline', fontsize=14, fontweight='bold', pad=15)
    
    steps = [
        (0.3, 2.0, 'Python\nSource Code\n(docstrings)', '#4CAF50'),
        (3.5, 2.0, 'Sphinx\n+ autodoc\n+ napoleon', '#2196F3'),
        (6.7, 2.0, '.rst Files\n(API reference\n+ tutorials)', '#FF9800'),
        (9.9, 2.0, 'HTML/PDF\nDocumentation\nWebsite', '#9C27B0'),
    ]
    
    for i, (x, y, label, color) in enumerate(steps):
        rect = FancyBboxPatch((x, y), 2.8, 2.0, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor='white', alpha=0.85, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.4, y + 1.0, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        
        if i < len(steps) - 1:
            ax.annotate('', xy=(steps[i+1][0], y + 1.0), xytext=(x + 2.8, y + 1.0),
                        arrowprops=dict(arrowstyle='->', color='white', lw=2.5))
    
    # Labels on arrows
    ax.text(3.2, 4.5, 'sphinx-apidoc', ha='center', fontsize=8, color='#aaa')
    ax.text(6.4, 4.5, 'sphinx-build', ha='center', fontsize=8, color='#aaa')
    ax.text(9.6, 4.5, 'make html', ha='center', fontsize=8, color='#aaa')
    
    # Extensions list
    ext_rect = FancyBboxPatch((3.5, 0.2), 6.5, 1.2, boxstyle="round,pad=0.08",
                               facecolor='#333', edgecolor='#4CAF50', alpha=0.8, linewidth=1.5)
    ax.add_patch(ext_rect)
    ax.text(6.75, 0.8, 'Extensions: autodoc | napoleon | typehints | viewcode | intersphinx',
            ha='center', va='center', fontsize=8, color='#4CAF50', fontfamily='monospace')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day24_plot_2.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 3 (Day25): Package Structure + pyproject.toml
# ============================================================
def plot3_package_structure():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor='#1a1a2e')
    
    # Left: Directory structure
    ax1.set_xlim(0, 7)
    ax1.set_ylim(0, 8)
    ax1.axis('off')
    ax1.set_title('Project Structure', color='white', fontsize=12, fontweight='bold')
    
    tree = [
        ('bci-pipeline/', '#FFD700', True),
        ('  pyproject.toml', '#4CAF50', False),
        ('  README.md', '#4CAF50', False),
        ('  LICENSE', '#4CAF50', False),
        ('  src/', '#2196F3', True),
        ('    bci/', '#2196F3', True),
        ('      __init__.py', '#607D8B', False),
        ('      config.py', '#FF9800', False),
        ('      loader.py', '#FF9800', False),
        ('      preprocessor.py', '#FF9800', False),
        ('      epocher.py', '#FF9800', False),
        ('      decoder.py', '#FF9800', False),
        ('      pipeline.py', '#FF9800', False),
        ('      cli.py', '#FF9800', False),
        ('  tests/', '#9C27B0', True),
        ('    test_preprocessor.py', '#9C27B0', False),
        ('    test_epocher.py', '#9C27B0', False),
        ('  docs/', '#00BCD4', True),
        ('    conf.py', '#00BCD4', False),
        ('    index.rst', '#00BCD4', False),
    ]
    
    for i, (line, color, is_dir) in enumerate(tree):
        marker = '/' if is_dir else ''
        ax1.text(0.3, 7.5 - i * 0.37, line + marker, fontsize=7,
                color=color, fontfamily='monospace')
    
    # Right: pyproject.toml highlights
    ax2.set_xlim(0, 7)
    ax2.set_ylim(0, 8)
    ax2.axis('off')
    ax2.set_title('pyproject.toml Highlights', color='white', fontsize=12, fontweight='bold')
    
    sections = [
        (0.3, 6.5, '[build-system]', '#FFD700',
         'requires = ["setuptools", "wheel"]\nbuild-backend = "setuptools"'),
        (0.3, 4.8, '[project]', '#4CAF50',
         'name = "bci-pipeline"\nversion = "0.1.0"\nrequires-python = ">=3.9"'),
        (0.3, 3.1, 'dependencies', '#2196F3',
         'numpy>=1.24, scipy>=1.10\nmne>=1.4, scikit-learn>=1.2'),
        (0.3, 1.4, '[project.scripts]', '#FF9800',
         'bci-run = "bci.cli:main"'),
    ]
    
    for (x, y, label, color, code) in sections:
        rect = FancyBboxPatch((x, y), 6.4, 1.3, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor='white', alpha=0.5, linewidth=1.5)
        ax2.add_patch(rect)
        ax2.text(x + 0.3, y + 1.0, label, fontsize=9, color='white', fontweight='bold')
        ax2.text(x + 0.3, y + 0.35, code, fontsize=7, color='white',
                fontfamily='monospace', alpha=0.8)
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day25_plot_1.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


# ============================================================
# Plot 4 (Day25): CI/CD Pipeline + Engineering Checklist
# ============================================================
def plot4_cicd_checklist():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor='#1a1a2e')
    
    # Left: CI/CD Pipeline
    ax1.set_xlim(0, 7)
    ax1.set_ylim(0, 8)
    ax1.axis('off')
    ax1.set_title('GitHub Actions CI/CD', color='white', fontsize=12, fontweight='bold')
    
    ci_steps = [
        (1.0, 7.0, 'Push / PR\nevent', '#607D8B', 0),
        (1.0, 5.5, 'Checkout\nCode', '#4CAF50', 1),
        (1.0, 4.0, 'Install\nDependencies', '#2196F3', 1),
        (1.0, 2.5, 'Run Tests\n+ Coverage', '#FF9800', 1),
        (1.0, 1.0, 'Type Check\n(mypy)', '#9C27B0', 1),
    ]
    
    for (x, y, label, color, has_arrow) in ci_steps:
        rect = FancyBboxPatch((x, y), 4.5, 1.0, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor='white', alpha=0.8, linewidth=1.5)
        ax1.add_patch(rect)
        ax1.text(x + 2.25, y + 0.5, label, ha='center', va='center',
                fontsize=9, color='white', fontweight='bold')
        if has_arrow:
            ax1.annotate('', xy=(3.25, y + 1.0), xytext=(3.25, y + 1.4),
                        arrowprops=dict(arrowstyle='->', color='white', lw=1.5))
    
    # Parallel Python versions
    ax1.text(5.8, 5.5, '3.9', fontsize=8, color='white')
    ax1.text(6.2, 5.5, '3.10', fontsize=8, color='white')
    ax1.text(6.6, 5.5, '3.11', fontsize=8, color='white')
    ax1.text(6.2, 5.1, 'matrix', fontsize=7, color='#FFD700', ha='center', fontstyle='italic')
    
    # Right: Engineering Checklist
    ax2.set_xlim(0, 7)
    ax2.set_ylim(0, 8)
    ax2.axis('off')
    ax2.set_title('Engineering Checklist', color='white', fontsize=12, fontweight='bold')
    
    checklist = [
        ('pyproject.toml', 'Package config + dependencies', True),
        ('src/ layout', 'Source-test separation', True),
        ('CLI tool', 'bci-run command entry', True),
        ('Test suite', 'pytest + 80% coverage', True),
        ('Type checking', 'mypy --strict', False),
        ('Documentation', 'Sphinx + autodoc', False),
        ('CI/CD', 'GitHub Actions', False),
        ('SemVer', 'v0.1.0 versioning', True),
        ('CHANGELOG', 'Change tracking', False),
        ('README', 'Quick start guide', True),
        ('LICENSE', 'MIT / Apache', True),
        ('.gitignore', 'Ignore rules', True),
    ]
    
    for i, (item, desc, done) in enumerate(checklist):
        y = 7.3 - i * 0.6
        marker = '+' if done else 'o'
        color = '#4CAF50' if done else '#FF9800'
        status = 'DONE' if done else 'TODO'
        
        ax2.text(0.3, y, f'[{marker}]', fontsize=10, color=color, fontfamily='monospace')
        ax2.text(1.0, y, item, fontsize=9, color='white', fontweight='bold')
        ax2.text(3.5, y, desc, fontsize=7, color='#aaa')
        ax2.text(6.2, y, status, fontsize=7, color=color, fontweight='bold')
    
    # Progress
    done_count = sum(1 for _, _, d in checklist if d)
    total = len(checklist)
    pct = done_count / total * 100
    ax2.text(3.5, 0.3, f'Progress: {done_count}/{total} ({pct:.0f}%)',
            ha='center', fontsize=10, color='#FFD700', fontweight='bold')
    
    fig.tight_layout()
    path = os.path.join(OUT_DIR, 'day25_plot_2.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == '__main__':
    print("Day 24-25: Docs, Types, Packaging & Engineering")
    print("=" * 50)
    plot1_type_hints_docstring()
    plot2_sphinx_pipeline()
    plot3_package_structure()
    plot4_cicd_checklist()
    print("\n✅ Day 24-25 所有图表生成完毕!")
