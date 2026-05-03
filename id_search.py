#!/usr/bin/env python3
"""
ID 足迹查询工具 - 查询用户名在各平台是否有账号
用法: python3 id_search.py <用户名>
"""

import sys
import asyncio
import aiohttp
import json
from datetime import datetime

PLATFORMS = [
    # ── 技术社区（可靠检测）──
    {"name": "GitHub", "cat": "技术社区",
     "url": "https://github.com/{}", "check_url": "https://api.github.com/users/{}",
     "found_if": "status_200", "not_found_if": "status_404"},

    {"name": "GitLab", "cat": "技术社区",
     "url": "https://gitlab.com/{}", "check_url": "https://gitlab.com/{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "码云Gitee", "cat": "技术社区",
     "url": "https://gitee.com/{}", "check_url": "https://gitee.com/{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "V2EX", "cat": "技术社区",
     "url": "https://www.v2ex.com/member/{}", "check_url": "https://www.v2ex.com/member/{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "掘金", "cat": "技术社区",
     "url": "https://juejin.cn/user/{}", "check_url": "https://juejin.cn/user/{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "博客园", "cat": "技术社区",
     "url": "https://www.cnblogs.com/{}", "check_url": "https://www.cnblogs.com/{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "CSDN", "cat": "技术社区",
     "url": "https://blog.csdn.net/{}", "check_url": "https://blog.csdn.net/{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "SegmentFault", "cat": "技术社区",
     "url": "https://segmentfault.com/u/{}", "check_url": "https://segmentfault.com/u/{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "npm", "cat": "技术社区",
     "url": "https://www.npmjs.com/~{}", "check_url": "https://registry.npmjs.org/-/user/org.couchdb.user:{}",
     "found_if": "status_200", "not_found_if": "status_404"},

    {"name": "Docker Hub", "cat": "技术社区",
     "url": "https://hub.docker.com/u/{}", "check_url": "https://hub.docker.com/v2/users/{}",
     "found_if": "status_200", "not_found_if": "status_404"},

    {"name": "HackerNews", "cat": "技术社区",
     "url": "https://news.ycombinator.com/user?id={}",
     "check_url": "https://hacker-news.firebaseio.com/v0/user/{}.json",
     "found_if": "not_null", "not_found_if": "null_response"},

    # ── 国际社交 ──
    {"name": "Twitter/X", "cat": "国际社交",
     "url": "https://x.com/{}", "check_url": "https://x.com/{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "Reddit", "cat": "国际社交",
     "url": "https://www.reddit.com/user/{}",
     "check_url": "https://www.reddit.com/user/{}/about.json",
     "found_if": "status_200", "not_found_if": "status_404",
     "headers": {"User-Agent": "Mozilla/5.0"}},

    {"name": "Pinterest", "cat": "国际社交",
     "url": "https://www.pinterest.com/{}", "check_url": "https://www.pinterest.com/{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "Telegram", "cat": "国际社交",
     "url": "https://t.me/{}", "check_url": "https://t.me/{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "Instagram", "cat": "国际社交",
     "url": "https://www.instagram.com/{}/", "check_url": "https://www.instagram.com/{}/",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "TikTok", "cat": "国际社交",
     "url": "https://www.tiktok.com/@{}", "check_url": "https://www.tiktok.com/@{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "LinkedIn", "cat": "国际社交",
     "url": "https://www.linkedin.com/in/{}", "check_url": "https://www.linkedin.com/in/{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    {"name": "YouTube", "cat": "国际社交",
     "url": "https://www.youtube.com/@{}", "check_url": "https://www.youtube.com/@{}",
     "found_if": "no_404", "not_found_if": "status_404"},

    # ── 中文平台（需要登录才能看的会返回重定向，所以用链接方式）──
    {"name": "微博", "cat": "中文社交",
     "url": "https://weibo.com/n/{}", "check_url": "https://weibo.com/n/{}",
     "found_if": "no_404", "not_found_if": "status_404",
     "headers": {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"}},

    {"name": "知乎", "cat": "中文社交",
     "url": "https://www.zhihu.com/people/{}", "check_url": "https://www.zhihu.com/people/{}",
     "found_if": "no_404", "not_found_if": "status_404",
     "headers": {"User-Agent": "Mozilla/5.0"}},

    {"name": "豆瓣", "cat": "中文社交",
     "url": "https://www.douban.com/people/{}", "check_url": "https://www.douban.com/people/{}",
     "found_if": "no_404", "not_found_if": "status_404",
     "headers": {"User-Agent": "Mozilla/5.0"}},

    {"name": "简书", "cat": "中文社交",
     "url": "https://www.jianshu.com/u/{}", "check_url": "https://www.jianshu.com/u/{}",
     "found_if": "no_404", "not_found_if": "status_404"},
]

# ANSI colors
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
GRAY   = "\033[90m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
CYAN   = "\033[96m"

async def check_platform(session, platform, username):
    url = platform["check_url"].format(username)
    headers = platform.get("headers", {"User-Agent": "Mozilla/5.0 (compatible; IDSearch/1.0)"})
    found_if = platform["found_if"]

    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8),
                               allow_redirects=True, ssl=False) as resp:
            status = resp.status

            if found_if == "status_200":
                found = status == 200
            elif found_if == "no_404":
                found = status != 404
            elif found_if == "not_null":
                text = await resp.text()
                found = text.strip() not in ["null", "", "false"]
            else:
                found = status != 404

            return {
                "name": platform["name"],
                "cat": platform["cat"],
                "url": platform["url"].format(username),
                "found": found,
                "status": status,
                "error": None
            }
    except asyncio.TimeoutError:
        return {"name": platform["name"], "cat": platform["cat"],
                "url": platform["url"].format(username), "found": None, "status": None, "error": "超时"}
    except Exception as e:
        return {"name": platform["name"], "cat": platform["cat"],
                "url": platform["url"].format(username), "found": None, "status": None, "error": str(e)[:40]}

def print_result(r, i, total):
    name = r["name"].ljust(16)
    if r["found"] is True:
        icon = f"{GREEN}✓{RESET}"
        status_str = f"{GREEN}找到账号{RESET}"
        url_str = f"{CYAN}{r['url']}{RESET}"
        print(f"  {icon} {BOLD}{name}{RESET} {status_str}  {url_str}")
    elif r["found"] is False:
        icon = f"{GRAY}✗{RESET}"
        print(f"  {icon} {GRAY}{name} 未找到{RESET}")
    else:
        icon = f"{YELLOW}?{RESET}"
        print(f"  {icon} {YELLOW}{name} 无法检测 ({r['error']}){RESET}")

async def main(username):
    print(f"\n{BOLD}{'═'*55}{RESET}")
    print(f"  {BOLD}ID 足迹查询{RESET}  ·  用户名: {CYAN}{username}{RESET}")
    print(f"  平台数量: {len(PLATFORMS)}  ·  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{BOLD}{'═'*55}{RESET}\n")

    results = []
    cats = {}
    for p in PLATFORMS:
        cats.setdefault(p["cat"], [])

    connector = aiohttp.TCPConnector(limit=20, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [check_platform(session, p, username) for p in PLATFORMS]

        done = 0
        for coro in asyncio.as_completed(tasks):
            r = await coro
            results.append(r)
            done += 1
            # print progress
            bar = ("█" * int(done/len(PLATFORMS)*20)).ljust(20)
            sys.stdout.write(f"\r  [{CYAN}{bar}{RESET}] {done}/{len(PLATFORMS)}")
            sys.stdout.flush()

    print(f"\n\n{BOLD}{'─'*55}{RESET}")

    # Group by category
    cat_results = {}
    for r in results:
        cat_results.setdefault(r["cat"], []).append(r)

    found_list = []
    for cat, items in cat_results.items():
        print(f"\n  {BLUE}{BOLD}{cat}{RESET}")
        items.sort(key=lambda x: (x["found"] is not True, x["name"]))
        for r in items:
            print_result(r, 0, 0)
            if r["found"]:
                found_list.append(r)

    # Summary
    found_count = sum(1 for r in results if r["found"] is True)
    notfound_count = sum(1 for r in results if r["found"] is False)
    error_count = sum(1 for r in results if r["found"] is None)

    print(f"\n{BOLD}{'═'*55}{RESET}")
    print(f"  {GREEN}找到: {found_count}{RESET}  ·  "
          f"{GRAY}未找到: {notfound_count}{RESET}  ·  "
          f"{YELLOW}无法检测: {error_count}{RESET}")

    if found_list:
        print(f"\n  {BOLD}✓ 找到的账号汇总:{RESET}")
        for r in found_list:
            print(f"    {GREEN}•{RESET} {r['name']}: {CYAN}{r['url']}{RESET}")

    # Save report
    report_file = f"id_report_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"ID足迹查询报告\n")
        f.write(f"查询用户名: {username}\n")
        f.write(f"查询时间: {datetime.now()}\n")
        f.write(f"平台总数: {len(PLATFORMS)}\n\n")
        f.write(f"=== 找到的账号 ===\n")
        for r in found_list:
            f.write(f"✓ {r['name']}: {r['url']}\n")
        f.write(f"\n=== 未找到 ===\n")
        for r in results:
            if r["found"] is False:
                f.write(f"✗ {r['name']}: {r['url']}\n")

    print(f"\n  报告已保存: {BOLD}{report_file}{RESET}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"\n用法: python3 id_search.py <用户名>\n示例: python3 id_search.py zhangsan\n")
        sys.exit(1)
    username = sys.argv[1]
    asyncio.run(main(username))
