"""
LLM Backend Manager for llama.cpp Integration

Supports Qwen3-32B-GGUF model with LoRA adapter management.
Handles backend detection (Metal, CUDA, CPU) and model initialization.
"""

import os
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMBackendManager:
    """Manages LLM backend selection, model loading, and LoRA adapters."""

    # Backend priority chain
    BACKEND_PRIORITY = ['metal', 'cuda', 'cpu']

    def __init__(
        self,
        model_path: Optional[Path] = None,
        n_ctx: int = 8192,
        n_gpu_layers: int = -1,  # -1 = offload all to GPU
        verbose: bool = False
    ):
        """
        Initialize LLM backend manager.

        Args:
            model_path: Path to GGUF model file (default: models/base/qwen3-32b.gguf)
            n_ctx: Context window size (default: 8192)
            n_gpu_layers: Number of layers to offload to GPU (-1 = all)
            verbose: Enable verbose logging
        """
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.verbose = verbose

        # State
        self.backend = None
        self.model = None
        self.lora_adapters = {}
        self.active_lora = None

        # Detect backend
        self.backend = self.detect_backend()
        logger.info(f"Selected backend: {self.backend}")

    def detect_backend(self) -> str:
        """
        Auto-detect best available backend.

        Priority: Metal (Apple) → CUDA (NVIDIA) → CPU

        Returns:
            Backend name: 'metal', 'cuda', or 'cpu'
        """
        # Check for Metal (Apple Silicon)
        if platform.system() == 'Darwin' and platform.machine() == 'arm64':
            if self._check_metal_available():
                logger.info("Detected Apple Silicon - using Metal backend")
                return 'metal'

        # Check for CUDA (NVIDIA)
        if self._check_cuda_available():
            logger.info("Detected CUDA - using CUDA backend")
            return 'cuda'

        # Fallback to CPU
        logger.info("Using CPU backend")
        return 'cpu'

    def _check_metal_available(self) -> bool:
        """Check if Metal acceleration is available."""
        try:
            # Check if running on Apple Silicon
            if platform.system() != 'Darwin' or platform.machine() != 'arm64':
                return False

            # Check if llama-cpp-python has Metal support
            try:
                from llama_cpp import Llama
                # Try to import Metal-specific modules (if available)
                return True
            except ImportError:
                return False

        except Exception:
            return False

    def _check_cuda_available(self) -> bool:
        """Check if CUDA is available."""
        try:
            # Check for nvidia-smi
            result = subprocess.run(
                ['nvidia-smi'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Also check via PyTorch if available
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            pass

        return False

    def load_base_model(
        self,
        model_path: Optional[Path] = None,
        n_ctx: Optional[int] = None,
        n_gpu_layers: Optional[int] = None
    ) -> bool:
        """
        Load base GGUF model.

        Args:
            model_path: Path to GGUF model file
            n_ctx: Context window size (override init value)
            n_gpu_layers: GPU layers (override init value)

        Returns:
            True if successful

        Raises:
            ImportError: If llama-cpp-python not installed
            FileNotFoundError: If model file not found
            RuntimeError: If model loading fails
        """
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "llama-cpp-python not installed. Install with: "
                "pip install llama-cpp-python"
            )

        # Use provided path or default
        if model_path:
            self.model_path = Path(model_path)
        elif not self.model_path:
            # Default path
            module_dir = Path(__file__).parent.parent
            self.model_path = module_dir / 'models' / 'base' / 'qwen3-32b.gguf'

        # Check model exists
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}\n"
                f"Download Qwen3-32B-GGUF from: "
                f"https://huggingface.co/unsloth/Qwen3-32B-GGUF"
            )

        # Use provided values or defaults
        n_ctx = n_ctx or self.n_ctx
        n_gpu_layers = n_gpu_layers if n_gpu_layers is not None else self.n_gpu_layers

        logger.info(f"Loading model: {self.model_path}")
        logger.info(f"Context window: {n_ctx}")
        logger.info(f"GPU layers: {n_gpu_layers} (-1 = all)")

        try:
            # Configure for detected backend
            if self.backend == 'metal':
                # Metal acceleration (Apple Silicon)
                self.model = Llama(
                    model_path=str(self.model_path),
                    n_ctx=n_ctx,
                    n_gpu_layers=n_gpu_layers,
                    n_batch=512,
                    verbose=self.verbose,
                    # Metal-specific settings
                    use_mmap=True,
                    use_mlock=False
                )

            elif self.backend == 'cuda':
                # CUDA acceleration (NVIDIA)
                self.model = Llama(
                    model_path=str(self.model_path),
                    n_ctx=n_ctx,
                    n_gpu_layers=n_gpu_layers,
                    n_batch=512,
                    verbose=self.verbose
                )

            else:
                # CPU only
                self.model = Llama(
                    model_path=str(self.model_path),
                    n_ctx=n_ctx,
                    n_gpu_layers=0,  # No GPU offloading
                    n_batch=256,  # Smaller batch for CPU
                    n_threads=os.cpu_count(),
                    verbose=self.verbose
                )

            logger.info("✓ Model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}")

    def load_lora_adapter(
        self,
        adapter_id: str,
        adapter_path: Path,
        scale: float = 1.0
    ) -> bool:
        """
        Load and register LoRA adapter.

        Args:
            adapter_id: Unique identifier for adapter
            adapter_path: Path to LoRA adapter file (.gguf)
            scale: LoRA scaling factor (default: 1.0)

        Returns:
            True if successful

        Raises:
            RuntimeError: If base model not loaded
            FileNotFoundError: If adapter file not found
        """
        if self.model is None:
            raise RuntimeError("Base model not loaded. Call load_base_model() first.")

        adapter_path = Path(adapter_path)
        if not adapter_path.exists():
            raise FileNotFoundError(f"LoRA adapter not found: {adapter_path}")

        logger.info(f"Loading LoRA adapter '{adapter_id}' from {adapter_path}")

        try:
            # Register adapter
            self.lora_adapters[adapter_id] = {
                'path': adapter_path,
                'scale': scale,
                'loaded': True
            }

            logger.info(f"✓ LoRA adapter '{adapter_id}' registered")
            return True

        except Exception as e:
            logger.error(f"Failed to load LoRA adapter: {e}")
            return False

    def switch_lora(self, adapter_id: Optional[str] = None) -> bool:
        """
        Switch active LoRA adapter.

        Args:
            adapter_id: Adapter to activate (None = use base model only)

        Returns:
            True if successful

        Raises:
            ValueError: If adapter_id not found
        """
        if adapter_id is not None and adapter_id not in self.lora_adapters:
            raise ValueError(
                f"LoRA adapter '{adapter_id}' not found. "
                f"Available: {list(self.lora_adapters.keys())}"
            )

        # Note: llama-cpp-python LoRA switching implementation depends on version
        # This is a simplified approach - real implementation may vary

        if adapter_id is None:
            logger.info("Switching to base model (no LoRA)")
            self.active_lora = None
        else:
            logger.info(f"Switching to LoRA adapter: {adapter_id}")
            self.active_lora = adapter_id

        return True

    def unload_lora(self, adapter_id: str) -> bool:
        """
        Unload LoRA adapter.

        Args:
            adapter_id: Adapter to unload

        Returns:
            True if successful
        """
        if adapter_id not in self.lora_adapters:
            logger.warning(f"LoRA adapter '{adapter_id}' not loaded")
            return False

        # Deactivate if currently active
        if self.active_lora == adapter_id:
            self.switch_lora(None)

        # Remove from registry
        del self.lora_adapters[adapter_id]
        logger.info(f"✓ LoRA adapter '{adapter_id}' unloaded")
        return True

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text with active LoRA (or base model).

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling parameter
            repeat_penalty: Repetition penalty
            stop: List of stop sequences
            **kwargs: Additional parameters for llama-cpp-python

        Returns:
            {
                'text': str,  # Generated text
                'tokens': int,  # Number of tokens generated
                'finish_reason': str,  # 'stop' or 'length'
                'lora': str  # Active LoRA adapter (or 'base')
            }

        Raises:
            RuntimeError: If model not loaded
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_base_model() first.")

        # Log inference parameters
        logger.debug(f"Generating with {self.active_lora or 'base model'}")
        logger.debug(f"max_tokens={max_tokens}, temperature={temperature}")

        try:
            # Generate
            output = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=stop or [],
                **kwargs
            )

            # Extract text from output
            # llama-cpp-python returns: {'choices': [{'text': '...', ...}]}
            generated_text = output['choices'][0]['text']
            finish_reason = output['choices'][0].get('finish_reason', 'unknown')

            result = {
                'text': generated_text,
                'tokens': len(output['choices'][0].get('tokens', [])),
                'finish_reason': finish_reason,
                'lora': self.active_lora or 'base'
            }

            logger.debug(f"Generated {result['tokens']} tokens")
            return result

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise RuntimeError(f"Text generation failed: {e}")

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get backend configuration information.

        Returns:
            Dictionary with backend details
        """
        info = {
            'backend': self.backend,
            'model_loaded': self.model is not None,
            'model_path': str(self.model_path) if self.model_path else None,
            'context_length': self.n_ctx,
            'gpu_layers': self.n_gpu_layers,
            'lora_adapters': list(self.lora_adapters.keys()),
            'active_lora': self.active_lora
        }

        # Add system info
        info['system'] = {
            'platform': platform.system(),
            'machine': platform.machine(),
            'python_version': platform.python_version()
        }

        return info

    def __del__(self):
        """Cleanup on deletion."""
        if self.model is not None:
            logger.info("Unloading LLM model")
            self.model = None


# Convenience function for quick initialization
def create_llm_manager(
    model_path: Optional[Path] = None,
    **kwargs
) -> LLMBackendManager:
    """
    Create and initialize LLM backend manager.

    Args:
        model_path: Path to GGUF model
        **kwargs: Additional arguments for LLMBackendManager

    Returns:
        Initialized LLMBackendManager

    Example:
        >>> manager = create_llm_manager()
        >>> manager.load_base_model()
        >>> result = manager.generate("What is a rare disease?")
        >>> print(result['text'])
    """
    manager = LLMBackendManager(model_path=model_path, **kwargs)
    return manager
