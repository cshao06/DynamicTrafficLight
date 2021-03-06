def algr (time):
  #初始化，可行置1，不可行置0，本身置1
  line0 = [-1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1]
  line1 = [1, -1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1]
  line2 = [1, 1, -1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1]
  line3 = [0, 0, 0, -1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1]
  state_temp = torch.FloatTensor([line0, line1, line2, line3])
  state = torch.zeros(16, 16)
  privilege = torch.zeros(16)
  for i in range(16):
    for j in range(16):
      bias = i // 4
      line = i % 4
      state[i][j] = state_temp[line][(j + 12 * bias) % 16]
  state = state + 1
  #print(state)
  light = torch.zeros(16)
  #根据时间片初始化penalty
  penalty = torch.rand(16, 16) * time
  penalty = penalty.to(int)
  print('penalty',penalty.size())

  state_copy = state.clone()
  state_copy[state_copy != 1] = 0
  print('state_copy',state_copy.size())
  #获取当前loss最低对象
  loss = penalty * state_copy
  print('loss',loss.size())
  loss_line = loss.sum(0)
  print('loss_line',loss_line.size())
  min_mum  = min(loss_line)
  list_temp = []
  min_p = 9999
  index = -1
  prob = torch.ones(16)

  for i in range(loss_line.shape[0]):
    if loss_line[i] == min_mum:
      if privilege[i] < min_p:
        min_p = privilege[i]
        index = i
  light[index] = 1
  privilege[index] = 0
  state_temp = state[index]
  state_temp -= 1
  state_temp[state_temp < 0] = 0 
  prob = prob * state_temp #求prob空间
  print(index)
  print(prob)
  #调度可行域
  while (prob.sum() != 0):
    loss_line[index] = 9999
    list_temp = []
    min_p = 9999
    min_loss = 9999
    index = -1

    #获取可行域下一个执行对象index
    for i in range(16):
      if prob[i] > 0:
        if loss_line[i] < min_loss:
          min_loss == loss_line[i]
          index = i
          min_p = privilege[i]
        elif loss_line[i] == min_loss:
          if privilege[i] < min_p:
            min_loss = loss_line[i]
            index = i
            min_p = privilege[i]
    light[index] = 1
    privilege[index] = 0
    state_temp = state[index]
    state_temp -= 1
    state_temp[state_temp < 0] = 0
    prob = prob * state_temp  #更新prob空间
    print(index)
    print(prob)



  print(light)
  privilege += 1 #时间片结束，所有状态优先级均上升

