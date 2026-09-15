import io
import os
import sys
from pathlib import Path

import torch
import torchaudio
from dotenv import load_dotenv


load_dotenv()


# =========================
# Sado TTS sozlamalari
# =========================

COSYVOICE_DIR = Path(
    os.getenv("COSYVOICE_DIR", "./CosyVoice")
)

BASE_MODEL_DIR = Path(
    os.getenv(
        "BASE_MODEL_DIR",
        "./CosyVoice/pretrained_models/CosyVoice2-0.5B"
    )
)

NAVOIY_CHECKPOINT = Path(
    os.getenv(
        "NAVOIY_CHECKPOINT",
        "./navoiy-tts/emotion_600h_joint.pt"
    )
)

REFERENCE_AUDIO = Path(
    os.getenv(
        "REFERENCE_AUDIO",
        "./voices/asal_reference.wav"
    )
)


class NavoiyEngine:
    """
    Sado TTS uchun Navoiy/CosyVoice2 engine.

    Muhim:
    - NVIDIA CUDA GPU kerak.
    - Navoiy checkpointi CosyVoice2 runtime bilan ishlaydi.
    - Reference audio faqat ovoz egasining roziligi bilan ishlatilishi kerak.
    """

    def __init__(self):
        self.model = None
        self.loaded = False

        self._check_paths()
        self._load_model()

    def _check_paths(self):
        """Kerakli fayl va papkalarni tekshiradi."""

        if not COSYVOICE_DIR.exists():
            raise FileNotFoundError(
                f"CosyVoice topilmadi: {COSYVOICE_DIR}"
            )

        if not BASE_MODEL_DIR.exists():
            raise FileNotFoundError(
                f"CosyVoice2 modeli topilmadi: {BASE_MODEL_DIR}"
            )

        if not NAVOIY_CHECKPOINT.exists():
            raise FileNotFoundError(
                f"Navoiy checkpoint topilmadi: {NAVOIY_CHECKPOINT}"
            )

        if not REFERENCE_AUDIO.exists():
            raise FileNotFoundError(
                f"Reference audio topilmadi: {REFERENCE_AUDIO}"
            )

    def _load_model(self):
        """CosyVoice2 modelini yuklaydi."""

        if not torch.cuda.is_available():
            raise RuntimeError(
                "Navoiy TTS uchun NVIDIA CUDA GPU kerak."
            )

        # CosyVoice papkasini Python path'ga qo'shamiz.
        sys.path.insert(
            0,
            str(COSYVOICE_DIR.resolve())
        )

        try:
            from cosyvoice.cli.cosyvoice import CosyVoice2
        except ImportError as error:
            raise ImportError(
                "CosyVoice runtime yuklanmadi. "
                "COSYVOICE_DIR yo'lini tekshiring."
            ) from error

        self.model = CosyVoice2(
            str(BASE_MODEL_DIR),
            load_jit=False,
            load_trt=False,
            fp16=True,
            use_flow_cache=False
        )

        self.loaded = True

    def generate(
        self,
        text: str,
        prompt_text: str = "",
        speed: float = 1.0
    ) -> bytes:
        """
        Uzbek matnni WAV audio bytes ko'rinishida qaytaradi.
        """

        if not self.loaded or self.model is None:
            raise RuntimeError(
                "Navoiy engine hali yuklanmagan."
            )

        text = text.strip()

        if not text:
            raise ValueError(
                "Matn bo'sh bo'lishi mumkin emas."
            )

        # Reference ovozni 16 kHz formatda yuklaymiz.
        prompt_speech = self._load_reference_audio()

        # CosyVoice2 zero-shot generation.
        results = self.model.inference_zero_shot(
            text,
            prompt_text,
            prompt_speech,
            stream=False
        )

        result = next(results)

        audio = result["tts_speech"]

        # Speed CosyVoice versiyasiga qarab qo'llanadi.
        # Modelning o'z speed parametri bo'lmasa,
        # audio playback tezligini frontend boshqaradi.
        audio = audio.cpu()

        buffer = io.BytesIO()

        torchaudio.save(
            buffer,
            audio,
            self.model.sample_rate,
            format="wav"
        )

        buffer.seek(0)

        return buffer.read()

    def _load_reference_audio(self):
        """Reference audio faylini 16 kHz mono tensor qiladi."""

        audio, sample_rate = torchaudio.load(
            str(REFERENCE_AUDIO)
        )

        # Stereo bo'lsa mono qilamiz.
        if audio.shape[0] > 1:
            audio = audio.mean(dim=0, keepdim=True)

        # CosyVoice zero-shot prompt odatda 16 kHz.
        if sample_rate != 16000:
            audio = torchaudio.functional.resample(
                audio,
                sample_rate,
                16000
            )

        return audio
