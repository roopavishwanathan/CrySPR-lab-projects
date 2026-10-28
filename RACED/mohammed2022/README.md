# Companion Repository "Attachment Strategies for Payment Channel Networks"

## Contact
For further questions, please contact `elias.rohrer AT tu-berlin.de`.

## Usage
First, install the required packages:
```
pip3 install networkx numpy simpy psutil
```

Then, in order to conduct an analysis of attachment strategies for a single node joining the network, run:
```
python3 main.py <strategy> <tx_amt> <k> <cpus> <seed>
```

Otherwise, in order to start an evaluation of the long-term impact of attachment strategies, run:
```
python3 eval_centralization.py <metric> <tx_amt> <eval_interval> <nodes_to_add> <cpus> <seed>
```

## Paper
Kimberly Lange and Elias Rohrer and Florian Tschorsch (2020). On the Impact of Attachment Strategies for Payment Channel Networks.

## BibTeX

tba
