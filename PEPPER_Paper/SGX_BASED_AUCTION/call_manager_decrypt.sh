#!/bin/bash

# for i in {1..100}
# do
#   start_time=$(date +%s)
#   response=$(curl -k -w "%{http_code}" https://0.0.0.0:8045/findWinner2)
#   if [ ${response: -3} == "200" ]; then
#     end_time=$(date +%s)
#     request_time=$((end_time - start_time))
#     echo "Request $i took $request_time seconds"
#   else
#     echo "Request $i failed with HTTP status code $response"
#   fi
# done


#!/bin/bash

for i in {1..100}
do     > stdout.txt 2> stderr.txt
    curl -k   https://0.0.0.0:8045/findWinner2 -w %{time_total} >> decrypt_20K.txt 
    echo ' ' >> decrypt_20K.txt
    # res=$?
    # if test "$res" != "0"; then
    #     curl -k  https://0.0.0.0:8045/closeApp
    # fi
done
