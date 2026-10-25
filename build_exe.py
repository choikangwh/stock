import os
import sys
import subprocess
import streamlit

def build():
    print("Preparing build configuration...")
    
    # Resolve streamlit directory path
    streamlit_path = os.path.dirname(streamlit.__file__)
    streamlit_static = os.path.join(streamlit_path, "static")
    
    print(f"Streamlit static path: {streamlit_static}")
    
    # Generate Spec file content with copy_metadata for streamlit
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata, collect_submodules

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app.py', '.'),
        ('stock_analyzer.py', '.'),
        (r'{streamlit_static}', 'streamlit/static'),
    ] + copy_metadata('streamlit'),
    hiddenimports=[
        'streamlit',
        'yfinance',
        'google.genai',
        'plotly',
        'pandas',
        'requests',
        'dotenv',
    ] + collect_submodules('streamlit') + collect_submodules('google.genai'),
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='StockDashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    spec_file = "StockDashboard.spec"
    with open(spec_file, "w", encoding="utf-8") as f:
        f.write(spec_content)
    print(f"Generated Spec file: {spec_file}")
    
    # Run PyInstaller
    print("Running PyInstaller to compile executable with Streamlit metadata...")
    pyinstaller_cmd = [
        os.path.join(".venv", "Scripts", "pyinstaller"),
        "--clean",
        spec_file
    ]
    
    subprocess.run(pyinstaller_cmd, check=True)
    print("=" * 60)
    print("Build completed successfully!")
    print("The standalone executable can be found at: dist/StockDashboard.exe")
    print("=" * 60)

if __name__ == "__main__":
    build()
