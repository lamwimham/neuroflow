"""
NeuroFlow Python SDK - Sandbox Module

Secure code execution with multiple isolation levels:
- Process isolation (basic)
- Linux namespace (strong)
- WASM (strongest, cross-platform)

v0.5.0: Added WASM sandbox support
"""

from .isolation import (
    SandboxSecurityLevel,
    SandboxConfig,
    SandboxResult,
    SandboxIsolator,
    SandboxManager,
)

from .wasm import (
    WasmRuntime,
    WasmSandboxConfig,
    WasmExecutionResult,
    WasmSandbox,
    WasmSandboxManager,
    execute_wasm,
)

__all__ = [
    # Process isolation
    "SandboxSecurityLevel",
    "SandboxConfig",
    "SandboxResult",
    "SandboxIsolator",
    "SandboxManager",
    
    # WASM isolation
    "WasmRuntime",
    "WasmSandboxConfig",
    "WasmExecutionResult",
    "WasmSandbox",
    "WasmSandboxManager",
    "execute_wasm",
]
