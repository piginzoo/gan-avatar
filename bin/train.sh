Date=$(date +%Y%m%d%H%M)
CUDA_VISIBLE_DEVICES=1 nohup python dcgen.py>> ./logs/$Date.log 2>&1 &