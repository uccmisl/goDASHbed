urls=(http://cs1dev.ucc.ie/misl/4K_non_copyright_dataset/4_sec/x264/tearsofsteel/DASH_Files/full/ http://cs1dev.ucc.ie/misl/4K_non_copyright_dataset/4_sec/x264/tearsofsteel/DASH_Files/main/ http://cs1dev.ucc.ie/misl/4K_non_copyright_dataset/4_sec/x264/tearsofsteel/DASH_Files/live/ http://cs1dev.ucc.ie/misl/4K_non_copyright_dataset/4_sec/x264/tearsofsteel/DASH_Files/full_byte_range/ http://cs1dev.ucc.ie/misl/4K_non_copyright_dataset/4_sec/x264/tearsofsteel/DASH_Files/main_byte_range/)

folders=(tos_4sec_full tos_4sec_main tos_4sec_live tos_4sec_full_byte_range tos_4sec_main_byte_range)

# get number of movies
mLen=${#urls[@]}


for (( j=0; j<${mLen}; j++ ))
do
	mkdir -p ${folders[j]}
        cd ${folders[j]}
        wget -r -np -nH --cut-dirs=3 -R index.html ${urls[j]}
        cd ..
done

