list=`ls zh-CN*.mp3`

for i in $list; do
    echo $i
    ffmpeg  -i 1.avif -i $i  -vf "scale=ih*9/16:ih, crop=ih*9/16:ih" \
    -c:v libx264 -crf 23 -preset fast
    -c:a copy
    -shortest $i.mp4
done
# 时长跟随较短的流（图片循环/音频）