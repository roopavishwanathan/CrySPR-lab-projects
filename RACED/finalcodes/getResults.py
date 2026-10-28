import argparse,os
import numpy as np
import ast

parser = argparse.ArgumentParser(description="Number of nodes in the ring")
parser.add_argument('--num_nodes', default=int)
args = parser.parse_args()

num_nodes = args.num_nodes
os.chdir('/content/drive/MyDrive/RACED/finalcodes/rand_tx_output/'+num_nodes+'/')


def getminChordlen(string):
  return min([int(x.strip().split(":")[1]) for x in string])

files_w_Chord = {}
for i in range(500):
  try:
    with open("rand_tx_o_insideChord_"+str(i+1)+".txt","r") as f:
      content = f.readlines()
      files_w_Chord[i+1] = getminChordlen(content)
  except: pass

Failed = 0
path_len = []

files = list(files_w_Chord.keys())
all_runtime = []
all_tx_Sender_Router_Dest = []
for i in files:
  with open("rand_tx_o_"+str(i)+".txt","r") as f:
    content = f.readlines()
    content = [x.strip() for x in content]
    chord_len = files_w_Chord[i]
    tx_Sender_Router_Dest = []
    runtime = []
    if 'There is no path' == content[-1]:
      Failed +=1
      continue 
    for c in content:
        if ' --- ' in c:
          runtime.append(float(c.split(" ---")[0]))
        
        if 'S (Route:' in c:
          s = c.split("S (")[1].split(": ")[1][:-1]
          tx_Sender_Router_Dest.append(len(ast.literal_eval(s)))
    
    tx_Sender_Router_Dest.insert(1,chord_len)
    all_tx_Sender_Router_Dest.append(tx_Sender_Router_Dest) 
    all_runtime.append(runtime)  

total_path_len = []
senderRouter_path_len = []
routerReceiver_path_len = []
successful_runtime = []
avg_runtime_chord = []
for i in range(len(all_tx_Sender_Router_Dest)):
  s = all_tx_Sender_Router_Dest[i]
  if len(s) == 3:
    total_path_len.append(np.sum(s))
    senderRouter_path_len.append(s[0])
    routerReceiver_path_len.append(s[-1])
    successful_runtime.append(np.sum(all_runtime[i]))
    avg_runtime_chord.append(all_runtime[i][1])

# os.chdir('/content/drive/MyDrive/RACED/finalcodes/rand_tx_output/'+num_nodes+'/finalResults')
# with open('results.txt','w') as f:
print("max(total_path_len),min(total_path_len),np.mean(total_path_len)")
print(max(total_path_len),min(total_path_len),np.mean(total_path_len))
print()
print("max(senderRouter_path_len),min(senderRouter_path_len),np.mean(senderRouter_path_len)")
print(max(senderRouter_path_len),min(senderRouter_path_len),np.mean(senderRouter_path_len))
print()
print("max(routerReceiver_path_len),min(routerReceiver_path_len),np.mean(routerReceiver_path_len)")
print(max(routerReceiver_path_len),min(routerReceiver_path_len),np.mean(routerReceiver_path_len))
print()
print("np.mean(successful_runtime)")
print(np.mean(successful_runtime))
print()
print("np.mean(avg_runtime_chord)")
print(np.mean(avg_runtime_chord))