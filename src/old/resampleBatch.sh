
find -iname '*.wav' -exec zita-resampler --wav --16bit --rate 32000 {} ../impulse-32k-16b/{} \; 
cd ../impulse-32k-16b/
find -name "* *" -type d | rename 's/ /_/g' 
find -name "* *" -type f | rename 's/ /_/g'
