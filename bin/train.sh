Date=$(date +%Y%m%d%H%M)

if [ "$1" == "debug" ]; then
    echo "debug...."
    python dcgen.py debug
    exit
fi

echo "production...."

CUDA_VISIBLE_DEVICES=1 nohup python dcgen.py>> ./logs/$Date.log 2>&1 &