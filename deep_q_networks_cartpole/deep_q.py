# -*- coding: utf-8 -*-
"""Deep q

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1s9HGq4mYsUEsPHtqWeRkkzOl1Pei8bTN
"""

import torch 
import torch.nn as nn
 
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
import numpy as np
import gym
env = gym.make('CartPole-v0')
from collections import namedtuple 
import random

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

num_epochs=4
alpha=0.001
batch_size=64

Experience = namedtuple('Experience',('state','action','next_state','reward','done'))

class replaymemory():
  def __init__(self,capacity):
    self.capacity=capacity
    self.memory=[]
    self.push_count=0
  
  def push(self,experience):
    if(self.push_count>self.capacity):
      self.memory[self.push_count%self.capacity]=experience
    else:
      self.memory.append(experience)
    self.push_count+=1
  
  
  def sample(self,batch_size):
    e=random.sample(self.memory,batch_size)
    #print(type(e1.state))
    states=torch.tensor([e1.state for e1 in e]).to(device)
    actions=torch.tensor([e1.action for e1 in e]).to(device)
    next=torch.tensor([e1.next_state for e1 in e]).to(device)
    rewards = torch.tensor(([e1.reward for e1 in e])).to(device)
    dones = torch.tensor([e1.done for e1 in e])
    
 
    return states.float(),actions,next,rewards,dones
  
  def can_provide(self,batch_size):
    return len(self.memory)>=batch_size

def soft_update(local,target,t):
  for target_param,local_param in zip(target.parameters(),local.parameters()):
    target_param.data.copy_(t*local_param.data+(1-t)*target_param.data)
    
class eps_strat():
  def __init__(self,num_actions,start,decay,end,device):
    self.cur_step=0
    self.num=num_actions
    self.device=device
    self.start=start
    self.decay=decay
    self.end=end
  def get_action(self,policy,state,step):
    self.cur_step=step
    ep=self.end+(self.start-self.end) * np.exp(-1*self.cur_step*self.decay)
    #self.cur_step=self.cur_step+1
    #print(ep,self.cur_step)
    if ep>random.random():
      #print("NO")
      action=random.randrange(self.num)
      return action
    else:
      policy.eval()
      with torch.no_grad():
        #print("yes")
        return torch.argmax(policy(state)).item()
  def get_value(self,step):
    self.cur_step=step
    ep=self.end+(self.start-self.end) * np.exp(-1*self.cur_step*self.decay)
    return ep

class convnet(nn.Module):
  def __init__(self):
    super(convnet,self).__init__()
    self.conv1= nn.Conv2d(3,6,5)
    self.conv2 = nn.Conv2d(6,16,5)
    self.fc1=nn.Linear(16*5*5,120)
    self.fc2=nn.Linear(120,84)
    self.fc3=nn.Linear(84,10)
  
  def forward(self,x):
    out=F.relu(self.conv1(x))
    out=F.relu(self.conv2(out))
    out = out.view(-1,16*5*5)
    out=F.relu(self.fc1(out))
    out=F.relu(self.fc2(out))
    out=self.fc3(out)
    return out

class lin(nn.Module):
  def __init__(self):
    super(lin,self).__init__()
    self.fc1=nn.Linear(4,128)
    self.fc2=nn.Linear(128,64)
    self.fc3=nn.Linear(64,2)
  def forward(self,x):
    out=F.relu(self.fc1(x))
    out=F.relu(self.fc2(out))
    out=self.fc3(out)
    return out

target_net = lin().to(device)
policy=lin().to(device)
soft_update(policy,target_net,1)
 
#optimizer=torch.optim.SGD(model.parameters(),lr=alpha)

num_episodes=1000000

ob=env.reset()
done_1=False
env = gym.make('CartPole-v0')
env=env.unwrapped
state=env.reset()
reward_sum=0
gamma=torch.tensor(0.999)
mem=replaymemory(10000)
start=1
end=0.0001
decay=0.1
 
#tau for soft update
 
tau=0.89
t_decay=eps_strat(2,0.9,0.01,0.001,device)
print(tau)



FILE='/content/drive/MyDrive/chrome_dino/target_net.pth'
File='/content/drive/MyDrive/chrome_dino/model.pth'
step=0
step_1=0
for eps in range(num_episodes):
  
  reward_sum=0
  state=env.reset()
  #print(state)
  done_1=False
  while not done_1:
    step=step+1
    ep=eps_strat(2,start,decay,end,device)
    #print(policy(state))
    action= ep.get_action(policy,torch.tensor(state).float().to(device),step)
    #print(action)
    next_state,reward,done_1,info=env.step(action)
    
   # print(next_state)
    
 
    e1=Experience(state,action,next_state,reward,done_1)
    #print(type(e1.state))
    mem.push(e1)
    reward_sum+=reward

    state=next_state
    #print(reward)
  #if reward_sum>300:
  print(eps,reward_sum)
  
  if(mem.can_provide(64)):
    states_1,actions,next_states,rewards,done=mem.sample(64)
    target_q=target_net.forward(next_states.float()).detach()
    target_q=torch.tensor([max(t) for t in target_q]).to(device).detach()
    
    done=done.int().to(device)
  
    q=rewards+gamma*(target_q*(1-done)).detach()
    q.unsqueeze_(1)
    #print(gamma*(target_q*(1-done)))
    l=torch.tensor([actions[i] for i in range(64)]).to(device)
    l=l.unsqueeze(1)
    #print(actions.size)
    exp_q=policy.forward(states_1.float()).gather(-1,l)
    #print(exp_q)
    #print(exp_q.size)
    #print(exp_q)
    #exp_q=torch.gather(exp_q,-1,l)
    #print(exp_q)
    #print(q)
    #print(l)
    #print(exp_q)
   # exp_q=torch.tensor([exp_q[i][actions[i]] for i in range(512)],requires_grad=True).to(device)
    #print(exp_q)
    #loss function
    loss=nn.MSELoss()
    
    tr=loss(exp_q,q)
    #print(tr)
    optimizer= torch.optim.Adam(policy.parameters(),lr=alpha)
    optimizer.zero_grad()
    tr.backward()
    # optimizer
    
    optimizer.step()
    
   
  if eps%10==0:
    step_1=step_1+1
    tau=t_decay.get_value(step_1)
    soft_update(policy,target_net,tau)
  if eps%100==0:
    torch.save(target_net.state_dict(),FILE)
    torch.save(policy.state_dict(),File)
    print("Weights saved")


