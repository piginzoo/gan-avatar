Date=$(date +%Y%m%d%H%M)
nohup CUDA_VISIBLE_DEVICES=1 python dcgen.py>> ./logs/$Date.log 2>&1 &