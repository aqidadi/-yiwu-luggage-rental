#!/usr/bin/env python3
"""
ID 足迹查询工具 v2 - 内容级检测，类 Maigret 准确度
用法: python3 id_search.py <用户名>
"""
import sys, asyncio, aiohttp
from datetime import datetime

# 每个平台的检测规则：
# check_url   : 实际请求的URL
# found_if    : 页面包含这些字符串 → 找到
# not_found_if: 页面包含这些字符串 → 未找到
# status_404  : 直接用404判断（API类平台）

PLATFORMS = [

  # ══ 技术社区 ══
  { "name":"GitHub", "cat":"技术社区",
    "url":"https://github.com/{}",
    "check_url":"https://api.github.com/users/{}",
    "method":"status", "found_status":200, "not_found_status":404,
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"码云Gitee", "cat":"技术社区",
    "url":"https://gitee.com/{}",
    "check_url":"https://gitee.com/{}",
    "method":"content",
    "not_found_if":["404","页面不存在","用户不存在","not found"],
    "found_if":["个人主页","followers","following"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"GitLab", "cat":"技术社区",
    "url":"https://gitlab.com/{}",
    "check_url":"https://gitlab.com/api/v4/users?username={}",
    "method":"content_nonempty",
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"V2EX", "cat":"技术社区",
    "url":"https://www.v2ex.com/member/{}",
    "check_url":"https://www.v2ex.com/member/{}",
    "method":"content",
    "not_found_if":["该用户不存在","Member Not Found","没有找到"],
    "found_if":["加入于","主题数","回复数"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"CSDN", "cat":"技术社区",
    "url":"https://blog.csdn.net/{}",
    "check_url":"https://blog.csdn.net/{}",
    "method":"content",
    "not_found_if":["用户不存在","404","该用户还没有"],
    "found_if":["原创","粉丝","关注"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"博客园", "cat":"技术社区",
    "url":"https://www.cnblogs.com/{}",
    "check_url":"https://www.cnblogs.com/{}",
    "method":"content",
    "not_found_if":["404","找不到","not found"],
    "found_if":["随笔","文章","评论","博主"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"掘金", "cat":"技术社区",
    "url":"https://juejin.cn/user/{}",
    "check_url":"https://api.juejin.cn/user_api/v1/user/get?user_id={}",
    "method":"content",
    "not_found_if":["not_found","用户不存在","err_no"],
    "found_if":["user_name","follower_count"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"SegmentFault", "cat":"技术社区",
    "url":"https://segmentfault.com/u/{}",
    "check_url":"https://segmentfault.com/u/{}",
    "method":"content",
    "not_found_if":["404","页面不存在","用户不存在"],
    "found_if":["关注者","声望","提问","回答"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"npm", "cat":"技术社区",
    "url":"https://www.npmjs.com/~{}",
    "check_url":"https://registry.npmjs.org/-/user/org.couchdb.user:{}",
    "method":"status", "found_status":200, "not_found_status":404,
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"HackerNews", "cat":"技术社区",
    "url":"https://news.ycombinator.com/user?id={}",
    "check_url":"https://hacker-news.firebaseio.com/v0/user/{}.json",
    "method":"content",
    "not_found_if":["null"],
    "found_if":["karma","created","about","submitted"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  # ══ 中文社交 ══
  { "name":"微博", "cat":"中文社交",
    "url":"https://weibo.com/n/{}",
    "check_url":"https://weibo.com/n/{}",
    "method":"content",
    "not_found_if":["用户不存在","抱歉，没有找到","页面不存在","该账号因"],
    "found_if":["微博数","关注","粉丝","认证"],
    "headers":{"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
               "Accept-Language":"zh-CN,zh;q=0.9"} },

  { "name":"知乎", "cat":"中文社交",
    "url":"https://www.zhihu.com/people/{}",
    "check_url":"https://www.zhihu.com/people/{}",
    "method":"content",
    "not_found_if":["用户不存在","该账号因违规","404","抱歉，你访问的页面不存在"],
    "found_if":["关注者","被关注","回答","提问","文章"],
    "headers":{"User-Agent":"Mozilla/5.0","Accept-Language":"zh-CN"} },

  { "name":"豆瓣", "cat":"中文社交",
    "url":"https://www.douban.com/people/{}",
    "check_url":"https://www.douban.com/people/{}",
    "method":"content",
    "not_found_if":["没有找到","用户不存在","该账号","404"],
    "found_if":["关注的人","被关注","广播","影音书"],
    "headers":{"User-Agent":"Mozilla/5.0","Accept-Language":"zh-CN"} },

  { "name":"简书", "cat":"中文社交",
    "url":"https://www.jianshu.com/u/{}",
    "check_url":"https://www.jianshu.com/u/{}",
    "method":"content",
    "not_found_if":["404","抱歉","用户不存在","没有找到"],
    "found_if":["关注","粉丝","文章","字数"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"百度贴吧", "cat":"中文社交",
    "url":"https://tieba.baidu.com/home/main?id={}",
    "check_url":"https://tieba.baidu.com/home/main?id={}",
    "method":"content",
    "not_found_if":["该用户不存在","用户不存在","抱歉"],
    "found_if":["发帖数","关注吧","粉丝"],
    "headers":{"User-Agent":"Mozilla/5.0","Accept-Language":"zh-CN"} },

  # ══ 国际社交 ══
  { "name":"Reddit", "cat":"国际社交",
    "url":"https://www.reddit.com/user/{}",
    "check_url":"https://www.reddit.com/user/{}/about.json",
    "method":"content",
    "not_found_if":["\"error\": 404","USER_DOESNT_EXIST","not found"],
    "found_if":["link_karma","comment_karma","name"],
    "headers":{"User-Agent":"Mozilla/5.0 ID-Search/2.0"} },

  { "name":"Twitter/X", "cat":"国际社交",
    "url":"https://x.com/{}",
    "check_url":"https://x.com/{}",
    "method":"content",
    "not_found_if":["This account doesn't exist","页面不存在","Account suspended"],
    "found_if":["Followers","Following","@{}"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"Instagram", "cat":"国际社交",
    "url":"https://www.instagram.com/{}/",
    "check_url":"https://www.instagram.com/{}/",
    "method":"content",
    "not_found_if":["Sorry, this page","页面不存在","page isn't available"],
    "found_if":["followers","following","posts","edge_followed_by"],
    "headers":{"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"} },

  { "name":"TikTok", "cat":"国际社交",
    "url":"https://www.tiktok.com/@{}",
    "check_url":"https://www.tiktok.com/@{}",
    "method":"content",
    "not_found_if":["Couldn't find this account","找不到此账号"],
    "found_if":["Followers","Following","Likes","followerCount"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"Telegram", "cat":"国际社交",
    "url":"https://t.me/{}",
    "check_url":"https://t.me/{}",
    "method":"content",
    "not_found_if":["If you have Telegram, you can contact","tgme_page_description\">@"],
    "found_if":["tgme_page_title","tgme_page_extra","members","subscribers","online"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"LinkedIn", "cat":"国际社交",
    "url":"https://www.linkedin.com/in/{}",
    "check_url":"https://www.linkedin.com/in/{}",
    "method":"content",
    "not_found_if":["This profile doesn't exist","Page not found","该页面不存在"],
    "found_if":["profileInsights","connections","Experience","Education"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"Pinterest", "cat":"国际社交",
    "url":"https://www.pinterest.com/{}",
    "check_url":"https://www.pinterest.com/{}",
    "method":"content",
    "not_found_if":["Sorry! We couldn't find","404"],
    "found_if":["Followers","Following","Pins","pinterestapp"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"YouTube", "cat":"国际社交",
    "url":"https://www.youtube.com/@{}",
    "check_url":"https://www.youtube.com/@{}",
    "method":"content",
    "not_found_if":["This page isn't available","404","找不到此频道"],
    "found_if":["subscribers","channelId","og:title"],
    "headers":{"User-Agent":"Mozilla/5.0"} },

  # ══ 开发者 ══
  { "name":"Docker Hub", "cat":"开发者",
    "url":"https://hub.docker.com/u/{}",
    "check_url":"https://hub.docker.com/v2/users/{}/",
    "method":"status", "found_status":200, "not_found_status":404,
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"PyPI", "cat":"开发者",
    "url":"https://pypi.org/user/{}",
    "check_url":"https://pypi.org/user/{}",
    "method":"status", "found_status":200, "not_found_status":404,
    "headers":{"User-Agent":"Mozilla/5.0"} },

  { "name":"Steam", "cat":"开发者",
    "url":"https://steamcommunity.com/id/{}",
    "check_url":"https://steamcommunity.com/id/{}",
    "method":"content",
    "not_found_if":["The specified profile could not be found","error_ctn"],
    "found_if":["profile_header","persona_name","friendblock_content"],
    "headers":{"User-Agent":"Mozilla/5.0"} },
]

# ANSI
G="\033[92m"; R="\033[91m"; Y="\033[93m"; B="\033[94m"
C="\033[96m"; GR="\033[90m"; BO="\033[1m"; RS="\033[0m"

async def check(session, p, username):
    url = p["check_url"].format(username)
    headers = p.get("headers", {"User-Agent":"Mozilla/5.0"})
    method = p.get("method","content")

    try:
        async with session.get(url, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=10),
                               allow_redirects=True, ssl=False) as r:
            status = r.status

            if method == "status":
                found = status == p.get("found_status", 200)
                reason = f"HTTP {status}"

            elif method == "content_nonempty":
                text = await r.text(errors='ignore')
                found = len(text.strip()) > 5 and text.strip() not in ["null","[]","{}","false"]
                reason = "内容非空" if found else "空响应"

            else:  # content
                if status == 404:
                    return _res(p, username, False, "HTTP 404")
                text = await r.text(errors='ignore')
                text_lower = text.lower()

                # Check not_found strings first
                for nf in p.get("not_found_if", []):
                    if nf.lower() in text_lower:
                        return _res(p, username, False, f"含[{nf}]")

                # Check found strings
                found_hits = [f for f in p.get("found_if", []) if f.lower() in text_lower]
                if found_hits:
                    found = True
                    reason = f"含[{found_hits[0]}]"
                else:
                    found = None  # 无法确定
                    reason = "无法判断"

            return _res(p, username, found, reason)

    except asyncio.TimeoutError:
        return _res(p, username, None, "超时")
    except Exception as e:
        return _res(p, username, None, str(e)[:50])

def _res(p, username, found, reason):
    return {"name":p["name"], "cat":p["cat"],
            "url":p["url"].format(username),
            "found":found, "reason":reason}

async def main(username):
    print(f"\n{BO}{'═'*58}{RS}")
    print(f"  {BO}ID 足迹查询 v2{RS}  ·  {C}{username}{RS}")
    print(f"  平台: {len(PLATFORMS)} 个  ·  内容级检测  ·  {datetime.now().strftime('%H:%M:%S')}")
    print(f"{BO}{'═'*58}{RS}\n")

    results = []
    done = 0
    total = len(PLATFORMS)

    conn = aiohttp.TCPConnector(limit=15, ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        tasks = [check(session, p, username) for p in PLATFORMS]
        for coro in asyncio.as_completed(tasks):
            r = await coro
            results.append(r)
            done += 1
            bar = ("█"*int(done/total*24)).ljust(24)
            sys.stdout.write(f"\r  [{C}{bar}{RS}] {done}/{total}  ")
            sys.stdout.flush()

    print(f"\n")

    # 按分类打印
    cats = {}
    for r in results:
        cats.setdefault(r["cat"], []).append(r)

    found_list = []
    for cat, items in cats.items():
        items.sort(key=lambda x: (0 if x["found"] else (1 if x["found"] is None else 2), x["name"]))
        print(f"  {B}{BO}{cat}{RS}")
        for r in items:
            name = r["name"].ljust(14)
            reason = r["reason"]
            if r["found"] is True:
                print(f"    {G}✓{RS} {BO}{name}{RS}  {G}找到账号{RS}  {GR}({reason}){RS}")
                print(f"       {C}{r['url']}{RS}")
                found_list.append(r)
            elif r["found"] is False:
                print(f"    {GR}✗{RS} {GR}{name}  未找到  ({reason}){RS}")
            else:
                print(f"    {Y}?{RS} {Y}{name}  无法确认  ({reason}){RS}")
        print()

    # 汇总
    fc = sum(1 for r in results if r["found"] is True)
    nc = sum(1 for r in results if r["found"] is False)
    uc = sum(1 for r in results if r["found"] is None)

    print(f"  {BO}{'─'*58}{RS}")
    print(f"  {G}✓ 找到: {fc}{RS}  {GR}✗ 未找到: {nc}{RS}  {Y}? 无法确认: {uc}{RS}\n")

    # 保存报告
    fname = f"report_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(f"ID足迹查询报告 v2\n用户名: {username}\n时间: {datetime.now()}\n\n")
        f.write("=== 找到的账号 ===\n")
        for r in found_list:
            f.write(f"✓ {r['name']}: {r['url']}\n  ({r['reason']})\n")
        f.write("\n=== 未找到 ===\n")
        for r in results:
            if r["found"] is False:
                f.write(f"✗ {r['name']}: {r['url']}  ({r['reason']})\n")
        f.write("\n=== 无法确认 ===\n")
        for r in results:
            if r["found"] is None:
                f.write(f"? {r['name']}: {r['url']}  ({r['reason']})\n")

    print(f"  {BO}报告已保存: {fname}{RS}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"\n用法: python id_search.py <用户名>\n示例: python id_search.py zhangsan\n")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
