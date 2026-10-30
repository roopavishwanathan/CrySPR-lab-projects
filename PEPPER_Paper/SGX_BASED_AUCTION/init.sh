#/bin/bash
start=$(date +%s.%N)

ego-go build enclave.go

end=$(date +%s.%N)    
runtime=$(python3 -c "print(${end} - ${start})")
echo "Build $runtime"


start=$(date +%s.%N)
ego sign enclave
end=$(date +%s.%N)    
runtime=$(python3 -c "print(${end} - ${start})")
echo "Sign $runtime"

start=$(date +%s.%N)
ego run enclave $1 $2
end=$(date +%s.%N)    
runtime=$(python3 -c "print(${end} - ${start})")
echo "Run $runtime"

rm -r enclave
