# yishuship

一个想法，从说出口到用户能用上，全程跟住，不丢。

你管用户能看到什么、能做什么；它管盒子里面的代码、测试和质量。需要你决定的时候，它停下来问你；说做完的时候，它拿出改之前和改之后的证据。

## 三个命令

```
/yishuship:idea 一句话说你的想法
   │  新想法。追问几个问题，写出用户能做什么、能看到什么，
   │  判断值不值得做，切出最小的第一块，然后等你决定
   ▼
/yishuship:next
   │  继续。在项目目录里用。读这个想法的进度，
   │  做下一小块，在真实 App 里验证，给你看证据；
   │  要你决定时停下。做到用户能用上，才算上线
   ▼
/yishuship:ideas
      看全部。所有项目里还活着的想法：
      走到哪、哪个在等你、哪个很久没动了
```

报错、调试、review、读网页这些不用专门记，交给 [Waza](https://github.com/tw93/Waza)：说"这个报错查一下"会触发 `/hunt`，说"帮我 review"会触发 `/check`。

## 它只管什么

yishuship 只放管理方式：记住每个想法、需要你决定时停下来问、做完时拿出证据。
怎么写代码、怎么做设计、怎么发布，这些做事方式都在外面，用到时才去读。
[INDEX.md](INDEX.md) 是这张地图，按"什么时候"写：要写代码时读哪份，要做界面时读哪份。
你本机的路径写在 `~/.yishuship/INDEX.md`，格式一样，不进仓库。
`scripts/check-index.py` 检查两份地图里的路径是否都还在，`/yishuship:ideas` 也会顺带报告。

## 你会看到什么

- **终端底部一行**：`yishuship ▸ 引用高亮原句 · 在做 · 等你：无`。不用输命令也知道有没有东西在等你。
- **需要你决定时**：选项竖着排，每个写清后果，标出推荐，回一句"1A 2B"就行。
- **做完时**：截图在终端旁边的页面里并排给你看，看完它会关掉。
- **每个想法一个进度文件**：`<项目>/.ship/ideas/<名字>.md`，记着为什么做、定了哪些行为、做到哪、下一步。换个会话、隔一周再来，都能接上。

## 安装

```bash
git clone https://github.com/yishu-ziyu/yishuship.git ~/Developer/yishuship
claude plugin marketplace add ~/Developer/yishuship
claude plugin install yishuship@yishuship

# 搭配的 Waza（只装这四个）
npx skills add tw93/Waza -s hunt think check read -g -y -a claude-code
```

底部状态行：把 `~/.claude/settings.json` 的 `statusLine.command` 改成

```
bash ~/Developer/yishuship/scripts/statusline.sh <原来的状态行命令>
```

原来的那行照常显示，yishuship 的一行加在下面。

可选：在真实 App 里自动验证需要 [cua-driver](https://github.com/trycua/cua)；截图页面优先开在 [cmux](https://cmux.com) 侧边，没有就用浏览器。

## 这一版为什么这么小

v2 有 14 个 skill、4 个拦截 hook、一套状态机和 21 个检查点，是在替当时较弱的模型补课，模型变强以后这些都成了每天要付的成本。v3 只留下在 vibereader 上真实试点过、确实管用的部分。旧版在 `v2-final` 标签里。

## License

MIT
