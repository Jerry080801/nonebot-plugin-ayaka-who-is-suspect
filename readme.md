# 谁是卧底

基于ayaka开发的 谁是卧底 小游戏

任何问题请发issue

<b>注意：由于更新pypi的readme.md需要占用版本号，因此其readme.md可能不是最新的，强烈建议读者前往[github仓库](https://github.com/bridgeL/nonebot-plugin-ayaka-who-is-suspect)以获取最新版本的帮助</b>


# How to start

## 安装插件

`poetry add nonebot-plugin-ayaka-who-is-suspect`

## 导入插件

修改nonebot2  `bot.py` 

```python
nonebot.load_plugin("ayaka_who_is_suspect")
```

## 导入数据

将本仓库的data文件夹（这是题库，可以自行修改，第一个是普通人，第二个是卧底词），放到nonebot的工作目录下

之后运行nonebot即可

# 指令

*最近更新*

## 没有打开游戏应用时

指令|效果
-|-
help 谁是卧底 | 查看帮助
谁是卧底 | 打开游戏应用，将创立一个游戏房间

## 房间内

指令|效果 
-|-
join/加入 | 加入房间
leave/离开 | 离开房间
start/begin/开始 | 开始游戏
info/信息 | 展示已加入房间的人员列表
exit/退出 | 关闭游戏 

注意，由于要私聊关键词，所以参与人都要提前加bot好友哦

## 游戏进行时

指令|效果 
-|-
vote \<at\> | 请at你要投票的对象，一旦投票无法更改，注意vote和at间加个空格（一般情况下不加也行，如果你是复制了其他人的投票，那么要加一个空格）
info/信息 | 展示投票情况
force_exit | 强制关闭游戏，有急事可用

注意：游戏进行时没有任何发言顺序控制，玩家可以自行协商一个发言顺序，或者自由发言，可以约定发言一轮，也可以约定发多轮后再投票，都可以，不做限制

