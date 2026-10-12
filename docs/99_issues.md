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


! Indexing 과정에서 Thread 도입 필요
- gui 환경에서 멈춤/crash, 중복, 취소 등의 문제
-> QThread -> indexWorker -> build_index() -> main thread (업데이트/완료/오류/취소)


! 다량 skipped 현상
- 전체 파일 중 절반이 skip됨 : mac에서 파일을 가져올때 ._으로 생기는 파일로 인한 착시
-> 파일 수집할 때 거르기 (utils.py)