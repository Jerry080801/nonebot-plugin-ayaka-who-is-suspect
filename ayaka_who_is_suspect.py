'''
    谁是卧底？
'''
from random import choice, randint
from typing import List
from ayaka import AyakaApp

app = AyakaApp("谁是卧底")
app.help = {
    "init": "join 加入房间\nleave 离开房间\nbegin 开始游戏",
    "playing": "vote <at:qq号> 投票",
}

words_list = app.plugin_storage("data").load()


class Player:
    def __init__(self, uid: int, name: str) -> None:
        self.uid = uid
        self.name = name
        self.word = ""
        # 投给了谁
        self.vote_uid = 0
        # 得票数
        self.vote_cnt = 0
        # 是否进入重投范围
        self.in_revote = False
        # 是否已出局
        self.failed = False

    def __str__(self):
        if self.failed:
            return f"[{self.name}] 已出局"
        return f"[{self.name}] {'已投票' if self.voted else '未投票'} 得票数：{self.vote_cnt}"

    @property
    def voted(self):
        return self.vote_uid != 0

    def vote(self, p: "Player"):
        if not self.voted:
            self.vote_uid = p.uid
            p.vote_cnt += 1
            return p.name

    def clear_vote(self):
        self.vote_uid = 0
        self.vote_cnt = 0
        self.in_revote = False


class Game:
    def __init__(self) -> None:
        self.player_list: List[Player] = []

    def build(self):
        '''生成一套题'''
        words: list = choice(words_list)
        # 有可能翻转
        if randint(0, 1):
            words.reverse()
        self.words = words

        # 提供词汇
        for p in self.player_list:
            p.word = self.words[0]

        # 生成内鬼
        i = randint(0, self.player_cnt-1)
        self.suspect = self.player_list[i]

        # 提供内鬼词汇
        self.suspect.word = self.words[1]

    @property
    def player_cnt(self):
        return len(self.player_list)

    @property
    def left_player_list(self):
        ps = [p for p in self.player_list if not p.failed]
        return ps

    @property
    def left_player_cnt(self):
        return len(self.left_player_list)

    @property
    def all_info(self):
        normal = []
        for p in self.player_list:
            if p != self.suspect:
                normal.append(p)
        text = f"普通人的关键词：{self.words[0]}\n"
        for p in normal:
            text += f"[{p.name}] "
        text += f"是普通人！\n卧底的关键词：{self.words[1]}\n[{self.suspect.name}] 是卧底！\n"
        text += f"场上最终剩余人数：{self.left_player_cnt}人！"
        return text

    @property
    def all_voted(self):
        return all(p.voted for p in self.left_player_list)

    @property
    def revote_list(self):
        '''重投列表'''
        ps = [p for p in self.player_list if p.in_revote]
        return ps

    @property
    def is_revoting(self):
        return len(self.revote_list) > 0

    def get_player(self, uid: int):
        for p in self.player_list:
            if uid == p.uid:
                return p

    def join(self, uid: int, name: str):
        '''加入'''
        p = self.get_player(uid)
        if not p:
            self.player_list.append(Player(uid, name))
            return True

    def leave(self, uid: int):
        '''退出'''
        p = self.get_player(uid)
        if p:
            self.player_list.remove(p)
            return True

    def begin(self):
        '''开始一轮游戏'''
        if self.player_cnt >= 4:
            self.build()
            return True

    def vote(self, voter_uid: int, uid: int):
        '''投票'''
        voter = self.get_player(voter_uid)
        p = self.get_player(uid)
        if not voter or not p:
            return

        # 普通投票
        if not self.is_revoting:
            return voter.vote(p)

        # 重投只能投给上一轮平票的人
        if p.in_revote:
            return voter.vote(p)

    def clear_last_vote(self):
        '''清空上一次投票'''
        for p in self.player_list:
            p.clear_vote()

    def kick_out(self):
        '''踢出得票最多的人，如果平票则针对平票人进行无限轮投票，直到一人被踢出'''
        # 找出最高的玩家
        ps = [p for p in self.left_player_list]
        ps.sort(key=lambda p: p.vote_cnt, reverse=True)

        max_vote = ps[0].vote_cnt
        i = 0
        for p in ps:
            if p.vote_cnt < max_vote:
                break
            i += 1

        ps = ps[:i]

        # 只有一个
        if len(ps) == 1:
            p = ps[0]
            p.failed = True
            return p.name

        # 有多个，进入重投
        for p in ps:
            p.in_revote = True

    @property
    def people_win(self):
        return self.suspect.failed

    @property
    def suspect_win(self):
        return not self.suspect.failed and self.left_player_cnt <= 2


@app.on_command("谁是卧底")
async def app_entrance():
    await app.start()
    app.cache.game = Game()


@app.on_state_command(["join", "加入"])
async def join():
    uid = app.user_id
    name = app.user_name

    users = await app.bot.get_friend_list()
    for user in users:
        if user["user_id"] == uid:
            break
    else:
        await app.send("只有bot的好友才可以加入房间，因为游戏需要私聊关键词")
        return

    game: Game = app.cache.game
    f = game.join(uid, name)
    if f:
        await app.send(f"[{name}] 加入了房间")
    else:
        await app.send(f"[{name}] 已经在房间里了")


@app.on_state_command(["leave", "离开"])
async def leave():
    game: Game = app.cache.game
    f = game.leave(app.user_id)
    if f:
        await app.send(f"[{app.user_name}] 离开了房间")
    else:
        await app.send(f"[{app.user_name}] 不在房间里")


@app.on_state_command(["start", "开始", "begin"])
async def begin():
    game: Game = app.cache.game
    p = game.get_player(app.user_id)
    if not p:
        await app.send(f"[{app.user_name}] 不在房间里")
        return
    f = game.begin()
    if f:
        await app.send("谁是卧底开始！")
    else:
        await app.send("至少需要4人才能游玩")
        return

    app.set_state("playing")
    for p in game.player_list:
        await app.bot.send_private_msg(user_id=p.uid, message=p.word)


@app.on_state_command(["exit", "退出", "quit"], "*")
async def exit_app():
    await app.close()


@app.on_state_command(["vote", "投票"], "playing")
async def vote():
    if not app.args or app.args[0].type != "at":
        await app.send("没有提供参数，请在vote命令后艾特你要投的人，不可以复制，bot无法识别")
        return
    
    try:
        uid = int(app.args[0].data["qq"])
    except:
        await app.send("参数不对！不要at全体成员")
        return

    game: Game = app.cache.game
    name = game.vote(app.user_id, uid)
    if not name:
        return

    await app.send(f"[{app.user_name}] 投给了 [{name}]！")
    info = "\n".join(str(p) for p in game.player_list)
    await app.send(info)

    if game.all_voted:
        name = game.kick_out()
        if name:
            await app.send(f"[{name}] 得票最多！出局！")
            if game.people_win:
                await app.send("普通人赢了！")
                await app.send(game.all_info)
                await app.close()
            elif game.suspect_win:
                await app.send("卧底赢了！")
                await app.send(game.all_info)
                await app.close()
            else:
                text = " ".join(f"[{p.name}]" for p in game.left_player_list)
                await app.send(f"场上剩余{game.left_player_cnt}人\n请 {text} 继续发言")
            game.clear_last_vote()
        else:
            ps = game.revote_list
            await app.send("出现了平局！")
            await app.send(" ".join(f"[{p.name}]" for p in ps) + " 请继续发言！在他们发言结束后，所有未出局的玩家可再次在他们中投出一人！")
            game.clear_last_vote()
