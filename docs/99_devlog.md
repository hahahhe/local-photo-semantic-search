indexer testing..

! SigLip 구조 오류

self.dim = int(self.encode_texts(["dim probe"]).shape[1])
AttributeError: 'NoneType' object has no attribute 'shape'

- SigLip은 img, text 모두 받아서 처리, 하나씩 던져줘서 문제
-> get_image/text_features() 사용


! BaseModelOutputWithPooling

(x.norm(dim=-1, keepdim=True) + eps) x:torch.Tensor
'BaseModelOutputWithPooling' object has no attribute 'norm'

- transformers 업데이트로 get_image/text_features() -> BaseModelOutputWithPooling (당연히 torch.Tensor일줄)
-> BaseModelOutputWithPooling의 pooler_output만 가져와서 작업 수행