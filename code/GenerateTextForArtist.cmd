@@echo off

if "%~2"=="" (
	set outputLength=200 
)else (
set outputLength=%2
)
python runner.py -a %1 -l ../save/models/%1/%1.ckpt -t -s %outputLength%