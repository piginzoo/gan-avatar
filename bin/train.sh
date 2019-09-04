Date=$(date +%Y%m%d%H%M)
CUDA_VISIBLE_DEVICES=1 nohup python dcgen.py $1>> ./logs/$Date.log 2>&1 &