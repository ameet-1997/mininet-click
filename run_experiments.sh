#/bin/bash

routers=8;
nodes=1;

fn="output/exp_${routers}_${nodes}.tsv"
touch ${fn};

for topology in "single_switch"; do
    for rate in "10000M"; do
        python start.py \
               --topology ${topology} \
               --udpBw ${rate} \
               --ttl 5 \
               --num_routers ${routers} \
               --nodes_per_router ${nodes} \
               --run_experiment \
               --output ${fn};
    done;
done;
              
for topology in "star" "chain"; do
    for rate in "10000M"; do
        python start.py \
               --topology ${topology} \
               --udpBw ${rate} \
               --ttl 5 \
               --num_routers ${routers} \
               --nodes_per_router ${nodes} \
               --run_experiment \
               --output ${fn};
    done;
done;
               
for topology in "random"; do
    for sparsity in 0.25 0.50; do
        for rate in "10000M"; do
            python start.py \
                   --topology ${topology} \
                   --sparsity ${sparsity} \
                   --udpBw ${rate} \
                   --ttl 5 \
                   --num_routers ${routers} \
                   --nodes_per_router ${nodes} \
                   --run_experiment \
                   --output ${fn};
        done;
    done;
done;
