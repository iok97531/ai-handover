# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs

block_cipher = None

# Collect all data/binaries/hiddenimports for key packages
chromadb_datas,    chromadb_binaries,    chromadb_hiddenimports    = collect_all('chromadb')
ort_datas,         ort_binaries,         ort_hiddenimports          = collect_all('onnxruntime')
tokenizers_datas,  tokenizers_binaries,  tokenizers_hiddenimports   = collect_all('tokenizers')
grpc_datas,        grpc_binaries,        grpc_hiddenimports         = collect_all('grpc')

# chromadb_rust_bindings is a separate package in chromadb >= 1.0
try:
    rb_datas, rb_binaries, rb_hiddenimports = collect_all('chromadb_rust_bindings')
except Exception:
    rb_datas, rb_binaries, rb_hiddenimports = [], [], []

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=(
        ort_binaries +
        chromadb_binaries +
        rb_binaries +
        tokenizers_binaries +
        grpc_binaries +
        collect_dynamic_libs('onnxruntime')
    ),
    datas=(
        chromadb_datas +
        rb_datas +
        ort_datas +
        tokenizers_datas +
        grpc_datas +
        collect_data_files('chromadb', includes=['**/*.sql', '**/*.json', '**/*.yaml'])
    ),
    hiddenimports=[
        # uvicorn internals
        'uvicorn.logging',
        'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.loops.asyncio',
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl', 'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan', 'uvicorn.lifespan.on',
        # app modules
        'routers.projects', 'routers.chat', 'routers.index', 'routers.settings',
        'services.chunker', 'services.file_watcher', 'services.indexer',
        'services.parser', 'services.rag',
        'ai.provider', 'ai.openai_provider', 'ai.claude_provider',
        'models.database', 'models.schemas',
        'vector_store.chroma',
        # native extensions
        'mmh3', 'tokenizers', 'chromadb_rust_bindings',
        # async / db
        'aiosqlite', 'anyio', 'anyio._backends._asyncio',
        # cryptography
        'cryptography.fernet',
        'cryptography.hazmat.primitives.ciphers.algorithms',
        # watchdog (Windows)
        'watchdog.observers', 'watchdog.observers.winapi',
        # sse
        'sse_starlette',
    ] + chromadb_hiddenimports + rb_hiddenimports + ort_hiddenimports
      + tokenizers_hiddenimports + grpc_hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['pytest', 'pytest_asyncio', 'httpx', 'tests'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='backend',
    debug=False,
    strip=False,
    upx=False,   # UPX can corrupt .pyd/.dll files — keep disabled
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='backend',   # output: backend/dist/backend/
)
