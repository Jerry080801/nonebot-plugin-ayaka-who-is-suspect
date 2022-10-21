'''
    谁是卧底？
'''
from random import choice, randint
from typing import List
from ayaka import AyakaApp, MessageSegment

init_help = '''
至少4人游玩，游玩前请加bot好友，否则无法通过私聊告知关键词
参与玩家的群名片不要重名，否则会产生非预期的错误=_=||
卧底只有一个
'''.strip()

room_help = '''
房间已建立，正在等待玩家加入...
- join/加入
- leave/离开
- start/begin/开始
- info/信息 展示房间信息
- exit/退出 关闭游戏
'''.strip()

play_help = '''
游戏正在进行中...
- vote <at> 请at你要投票的对象，一旦投票无法更改
- info/信息 展示投票情况
- force_exit 强制关闭游戏，有急事可用
'''.strip()

app = AyakaApp("谁是卧底")
app.help = {
    "init": init_help,
    "room": room_help,
    "play": play_help
}

words_list = app.plugin_storage("data", default=[["Test", "test"]]).load()


class Player:
    def __init__(self, uid: int, name: str) -> None:
        self.uid = uid
        self.name = name
        self.word = ""

        self.vote_cnt = 0
        self.vote_to: Player = None
        self.in_revote = False
        self.is_suspect = False
        self.out = False

    def __str__(self):
        return f"[{self.name}]"

    def clear(self):
        self.vote_cnt = 0
        self.vote_to = None
        self.in_revote = False
        self.is_suspect = False
        self.out = False

    def set_normal(self, word: str):
        self.clear()
        self.word = word

    def set_suspect(self, word: str):
        self.clear()
        self.word = word
        self.is_suspect = True

    def clear_vote(self, preserve_revote=False):
        self.vote_to = None
        self.vote_cnt = 0
        if not preserve_revote:
            self.in_revote = False

    @property
    def vote_info(self):
        info = f"[{self.name}] "
        if self.out:
            info += "已出局 "
            return info

        if not self.vote_to:
            info += "未投票 "

        info += f"得票数：{self.vote_cnt} "

        if self.in_revote:
            info += "(上一轮平票)"

        return info


class Game:
    def __init__(self) -> None:
        self.players: List[Player] = []

    @property
    def player_cnt(self):
        return len(self.players)

    @property
    def no_out_players(self):
        return [p for p in self.players if not p.out]

    @property
    def in_revote_players(self):
        return [p for p in self.no_out_players if p.in_revote]

    @property
    def in_revote(self):
        return len(self.in_revote_players) > 0

    @property
    def voted_end(self):
        if all(p.vote_to for p in self.no_out_players):
            return True

        # 或者有人已获得半数以上的票数
        cnt = int(len(self.no_out_players)/2)
        for p in self.no_out_players:
            if p.vote_cnt > cnt:
                return True

    @property
    def vote_info(self):
        items = ["投票情况："]
        items.extend(p.vote_info for p in self.players)
        return "\n".join(items)

    @property
    def room_info(self):
        items = ["房间成员："]
        items.extend(str(p) for p in self.players)
        return "\n".join(items)

    def get_player(self, uid: int):
        for p in self.players:
            if p.uid == uid:
                return p

    def join(self, uid: int, name: str):
        p = self.get_player(uid)
        if p:
            return False, f"{p} 已在房间中"
        p = Player(uid, name)
        self.players.append(p)
        return True, f"{p} 加入房间"

    def leave(self, uid: int):
        p = self.get_player(uid)
        if not p:
            return False, f"({uid}) 不在房间中"
        self.players.remove(p)
        return True, f"{p} 离开房间"

    def start(self, uid: int):
        p = self.get_player(uid)
        if not p:
            return False, f"({uid}) 没有加入游戏"

        if self.player_cnt < 4:
            return False, "至少需要4人才能开始游戏"

        normal, fake = choice(words_list)

        # 有可能翻转
        if randint(0, 1):
            normal, fake = fake, normal

        # 初始化状态
        for p in self.players:
            p.set_normal(normal)

        i = randint(0, self.player_cnt - 1)
        self.players[i].set_suspect(fake)

        return True, "游戏开始"

    def vote(self, uid: int, vote_to_uid: int):
        p = self.get_player(uid)
        if not p:
            return False, f"({uid}) 没有加入游戏"

        if p.vote_to:
            return False, f"{p} 已经投票过了"

        vote_to = self.get_player(vote_to_uid)
        if not vote_to:
            return False, f"({vote_to_uid}) 没有加入游戏"

        if self.in_revote:
            if not vote_to.in_revote:
                return False, "只能投给上一轮平票的人"

        p.vote_to = vote_to
        vote_to.vote_cnt += 1
        return True, f"{p} 投票给了 {vote_to}"

    def kickout(self):
        info = self.vote_info + "\n"
        ps = self.no_out_players

        # 取最高者
        ps.sort(key=lambda p: p.vote_cnt, reverse=True)
        vote_cnt = ps[0].vote_cnt
        for i, p in enumerate(ps):
            if p.vote_cnt < vote_cnt:
                ps = ps[:i]
                break

        # 只票出一人，正常结算
        if len(ps) == 1:
            p = ps[0]
            p.out = True
            info += f"{p} 出局"

            # 清理本轮投票
            for p in self.no_out_players:
                p.clear_vote()

            return True, info

        # 平票
        # 清除in_revote
        for p in self.no_out_players:
            p.in_revote = False
        # 设置in_revote
        for p in ps:
            p.in_revote = True

        info += "平局\n"
        info += " ".join(str(p) for p in ps) + " 请发言申辩\n"
        info += "所有玩家可再次投票，投出其中一人"

        # 清理本轮投票
        for p in self.no_out_players:
            p.clear_vote(preserve_revote=True)

        return False, info

    def check_end(self):
        for p in self.players:
            if p.is_suspect and p.out:
                return True, "普通人赢了！"
        if len(self.no_out_players) <= 2:
            return True, "卧底赢了！"
        return False, ""

    def get_words(self):
        ps = [p for p in self.players if not p.is_suspect]
        word = ps[0].word

        items = []
        items.append(f"普通人的关键词： {word}")
        items.append(" ".join(str(p) for p in ps) + " 是普通人！")

        for p in self.players:
            if p.is_suspect:
                break

        items.append(f"卧底的关键词： {p.word}")
        items.append(f"{p} 是卧底！")
        return "\n".join(items)


async def get_uid(arg: MessageSegment):
    users = await app.bot.get_group_member_list(group_id=app.group_id)

    # at？
    if arg.type == "at":
        at = arg
        try:
            uid = int(at.data["qq"])
        except:
            return

        for user in users:
            if user["user_id"] == uid:
                return user["user_id"]
        return

    # 名称？
    name = str(arg)
    if name.startswith("@"):
        name = name[1:]

    for user in users:
        if user["card"] == name:
            return user["user_id"]


async def check_friend(uid: int):
    users = await app.bot.get_friend_list()
    for user in users:
        if user["user_id"] == uid:
            return True


@app.on_command("谁是卧底")
async def app_entrance():
    if not await app.start():
        return

    await app.send(init_help)
    app.set_state("room")
    await app.send(room_help)

    app.cache.game = Game()
    await join()


@app.on_state_command(["exit", "退出"], "room")
async def exit_room():
    await app.close()


@app.on_state_command(["exit", "退出"], "play")
async def exit_play():
    await app.send("游戏已开始，你确定要终结游戏吗？请使用命令：强制退出")


@app.on_state_command(["force_exit", "强制退出"], "play")
async def app_force_exit():
    await app.close()


@app.on_state_command(["join", "加入"], "room")
async def join():
    # 校验好友
    if not await check_friend(app.user_id):
        await app.send("只有bot的好友才可以加入房间，因为游戏需要私聊关键词")
        return

    game: Game = app.cache.game
    f, info = game.join(app.user_id, app.user_name)
    await app.send(info)


@app.on_state_command(["leave", "离开"], "room")
async def leave():
    game: Game = app.cache.game
    f, info = game.leave(app.user_id)
    await app.send(info)

    if f and game.player_cnt == 0:
        await app.close()


@app.on_state_command(["start", "begin", "开始"], "room")
async def start():
    game: Game = app.cache.game
    f, info = game.start(app.user_id)
    await app.send(info)

    # 启动失败
    if not f:
        return

    app.set_state("play")
    for p in game.players:
        await app.bot.send_private_msg(user_id=p.uid, message=p.word)


@app.on_state_command(["info", "信息"], "room")
async def room_info():
    game: Game = app.cache.game
    await app.send(game.room_info)


@app.on_state_command(["info", "信息"], "play")
async def vote_info():
    game: Game = app.cache.game
    await app.send(game.vote_info)


@app.on_state_command(["vote", "投票"], "play")
async def vote():
    game: Game = app.cache.game

    # 验证参数
    if not app.args:
        await app.send("没有获取到有效参数")
        return

    vote_to_uid = await get_uid(app.args[0])
    if not vote_to_uid:
        await app.send("没有获取到有效参数")

    # 投票
    f, info = game.vote(app.user_id, vote_to_uid)
    await app.send(info)

    # 投票失败
    if not f:
        return

    # 投票是否结束
    if not game.voted_end:
        return

    # 结算时公布投票结果
    f, info = game.kickout()
    await app.send(info)

    # 出现平局
    if not f:
        return

    # 成功踢出一人，判断游戏是否结束
    f, info = game.check_end()
    if not f:
        return

    # 展示结果
    await app.send(game.get_words())
    await app.send(info)

    # 返回房间
    app.set_state("room")
    await app.send("已回到房间")
