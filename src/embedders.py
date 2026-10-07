import torch
import numpy as np
from PIL import Image

from typing import List, Optional
from dataclasses import dataclass

# 공통
def get_device() -> torch.device:
    """
    Mac의 경우 MPS 우선 사용
    아니면 CUDA, 도 아니면 CPU
    """
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def l2_normalize(x: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    """
    벡터 길이1로 정규화
    """
    return x / (x.norm(dim=-1, keepdim=True) + eps)

class EmbedderBase:
    dim: int

    def encode_images(self, pil_images: List[Image.Image]) -> np.ndarray:
        raise NotImplementedError
    
    def encode_texts(self, texts: List[str]) -> np.ndarray:
        raise NotImplementedError
# CLIP (option)

# SigLIP
@dataclass
class SigLIPConfig:
    model_id: str = "google/siglip2-so400m-patch16-256"
    prompt_template: Optional[str] = None

# 이미지, 텍스트 따로 처리
class SigLIPEmbedder(EmbedderBase):

    def __init__(
        self,
        device: torch.device,
        cfg: SigLIPConfig
    ):
        from transformers import AutoProcessor, AutoModel

        self.device = device
        self.cfg = cfg

        self.processor = AutoProcessor.from_pretrained(
            cfg.model_id
        )

        self.model = AutoModel.from_pretrained(
            cfg.model_id
        ).to(device).eval()

        self.dim = int(
            self.encode_texts(["dim probe"]).shape[1]
        )


    def _apply_template(self, text: str) -> str:
        if not self.cfg.prompt_template:
            return text

        return self.cfg.prompt_template.format(
            text=text
        )


    @torch.no_grad()
    def encode_images(
        self,
        pil_images: List[Image.Image]
    ) -> np.ndarray:

        inputs = self.processor(
            images=[
                image.convert("RGB")
                for image in pil_images
            ],
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        outputs = self.model.get_image_features(**inputs)

        features = outputs.pooler_output

        features = l2_normalize(features)

        return (
            features
            .detach()
            .cpu()
            .numpy()
            .astype("float32")
        )


    @torch.no_grad()
    def encode_texts(
        self,
        texts: List[str]
    ) -> np.ndarray:

        texts = [
            self._apply_template(text)
            for text in texts
        ]

        inputs = self.processor(
            text=texts,
            padding="max_length",
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        outputs = self.model.get_text_features(**inputs)

        features = outputs.pooler_output

        features = l2_normalize(features)

        return (
            features
            .detach()
            .cpu()
            .numpy()
            .astype("float32")
        )

class SigLIPEmbedder1():
    def __init__(self, device: torch.device, cfg: SigLIPConfig):
        from transformers import AutoProcessor, AutoModel
    
        self.device = device
        self.cfg = cfg

        self.processor = AutoProcessor.from_pretrained(cfg.model_id)
        self.model = AutoModel.from_pretrained(cfg.model_id).to(device).eval()

        self.dim = int(self.encode_texts(["dim probe"]).shape[1])

    def _apply_template(self, t: str) -> str:
        if not self.cfg.prompt_template:
            return t
        return self.cfg.prompt_template.format(text=t)
    
    @torch.no_grad()
    def encode_images(self, pil_images: List[Image.Image]) -> np.ndarray:
        texts = [""]*len(pil_images)

        inputs = self.processor(
            text=texts, 
            return_tensors="pt",
        ).to(self.device)

        outputs = self.model(**inputs)
        img = outputs.image_embeds 
        img = l2_normalize(img).detach().cpu().numpy().astype("float32")

        return img

    @torch.no_grad()
    def encode_texts(self, texts: List[str]) -> np.ndarray:
        texts = [self._apply_template(t) for t in texts]

        inputs = self.processor(
            text=texts, 
            return_tensors="pt",
        ).to(self.device)

        outputs = self.model(**inputs)
        txt = outputs.text_embeds
        txt = l2_normalize(txt).detach().cpu().numpy().astype("float32")

        return txt

def make_embedder(
        backend: str, 
        device: torch.device, 
        model: str, 
        pretrained: str,
        prompt_template: Optional[str] = None,
) -> EmbedderBase:
    backend = backend.lower()
    if backend == "siglip":
        cfg = SigLIPConfig(model_id=model, prompt_template=prompt_template)
        return SigLIPEmbedder(device, cfg)
    if backend == "clip":
        raise ValueError("not yet")
    raise ValueError("backend must be one of: siglip, clip")