#!/usr/bin/env bash
# Open Company 定时值班任务的 cron 入口。
# 用法: run-task.sh <task-id>
#   github-issue-pr-actions  每 5 分钟,先跑 guard,有新事件才唤醒 Agent
#   release-batch            每日 07:00
#   daily-patrol             每晚 21:00
# 依赖: kiro-cli(headless 模式,需 KIRO_API_KEY)、node、gh、flock、timeout
set -uo pipefail

TASK="${1:-}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# cron 的环境很干净:密钥和 PATH 从 env 文件读取(不入库,建议 chmod 600)
ENV_FILE="${OPEN_COMPANY_ENV:-$HOME/.config/open-company/env}"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi
export PATH="${NODE_DIR:+$NODE_DIR:}$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"

STATE_DIR="${OPEN_COMPANY_STATE_DIR:-$HOME/.local/state/open-company}"
LOG_DIR="$STATE_DIR/logs"
mkdir -p "$LOG_DIR"

# 值班任务盯的 GitHub 仓库;guard 直接读这个环境变量
export GITHUB_REPO="${GITHUB_REPO:-chaxiu/OpenCompare}"

GH_DIR="$REPO/companies/open-source-software/products/open-compare/projects/github"
GUARD=""
case "$TASK" in
  github-issue-pr-actions)
    WORKDIR="$GH_DIR"; GUARD="guards/github-sentinel.mjs"; LIMIT="15m" ;;
  release-batch)
    WORKDIR="$GH_DIR"; LIMIT="120m" ;;
  daily-patrol)
    WORKDIR="$REPO/companies/open-source-software/projects/daily-patrol"; LIMIT="30m" ;;
  *)
    echo "usage: $0 {github-issue-pr-actions|release-batch|daily-patrol}" >&2
    exit 64 ;;
esac

LOG="$LOG_DIR/$TASK-$(date +%F).log"
log() { printf '%s [%s] %s\n' "$(date '+%F %T')" "$TASK" "$*" >>"$LOG"; }

# guard 是 ES module;旧 node 下会语法报错并以 exit=1 退出,看起来像「无新事件」
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
if [ "$NODE_MAJOR" -lt 18 ]; then
  log "error: node >= 18 required, got $(node --version 2>/dev/null || echo none); set NODE_DIR in $ENV_FILE"
  exit 127
fi

# 同一任务不重叠运行:上一场没结束就跳过本场
exec 9>"$LOG_DIR/$TASK.lock"
if ! flock -n 9; then
  log "skip: previous run still active"
  exit 0
fi

# 零 Token 预检:exit 0 有新事件 / 1 无新事件 / 2 guard 出错
GUARD_OUT=""
if [ -n "$GUARD" ]; then
  # guard 在缺少 gh 时会静默返回 exit=1,看起来像「无新事件」,这里提前拦下
  if ! command -v gh >/dev/null 2>&1; then
    log "error: gh CLI not found; guard cannot query GitHub"
    exit 127
  fi
  GUARD_OUT="$(cd "$WORKDIR" && node "$GUARD" 2>&1)"
  rc=$?
  case "$rc" in
    0) log "guard exit=0, waking agent" ;;
    1) log "guard exit=1, no new events"; exit 0 ;;
    *) log "guard exit=$rc (guard error): $GUARD_OUT"; exit 2 ;;
  esac
fi

KIRO_CLI="${KIRO_CLI:-kiro-cli}"
if ! command -v "$KIRO_CLI" >/dev/null 2>&1; then
  log "error: $KIRO_CLI not found in PATH"
  exit 127
fi
if [ -z "${KIRO_API_KEY:-}" ]; then
  log "error: KIRO_API_KEY not set (see $ENV_FILE)"
  exit 78
fi

RUN_DIR="$STATE_DIR/runs/$TASK/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
DIGEST="$RUN_DIR/digest.md"

PROMPT="你在 cron 无人值守模式下运行 Open Company 值班任务「$TASK」。

- 工作目录: $WORKDIR(所有相对路径、guards/ 脚本、state/ 游标都以它为准)
- 本场 digest: $DIGEST
- 先读 .kiro/steering/open-company-index.md 和 .kiro/steering/task-$TASK.md,再读后者 #[[file:...]] 引用的任务原文,按原文执行。公司与产品准则见对应的 AGENTS.md。
- 本场是定时触发,没有人工 brief。
- 目标 GitHub 仓库: $GITHUB_REPO。任务原文和 AGENTS.md 里写的 chaxiu/OpenCompare 一律换成这个仓库。
- 对外身份: 以 \`node guards/gh.mjs api user --jq .login\` 返回的账号为准。原文要求回帖作者为 munk-agent 的复核,改为核对作者等于这个账号。"

if [ -n "$GUARD" ]; then
  PROMPT="$PROMPT
- guard 已在本脚本中跑过,exit=0,输出如下(marker 用于回写 state/seen.txt):
$GUARD_OUT"
fi

PROMPT="$PROMPT

无人值守规则(优先于任务文件里「先问用户」的说法):
1. 没有人能回答你。凡需要用户确认或 needsOwner: true 的地方,不要等待:把原因和待人执行的完整命令写进 digest,在 digest 单独写一行 \`needsOwner: true\`(这一行不要有别的文字;不需要人处理时不要写这个标记,也不要在句子里提到它),然后收工。
2. 不推 tag、不建或修改 Release、不 force push、不删除任何 ref 或文件。这些操作一律按规则 1 交给人。
3. 任务原文规定的 GitHub 回执、打标签,可以通过 node guards/gh.mjs 照做;不得用其它身份发帖。
4. 做不了的步骤记为 blocked 并写明原因,不伪造结果。
5. 任务原文提到的文件,只在原路径检查一次;不存在就记「无数据」,不要全仓搜索、不要派子 Agent 去找。"

log "start: run_dir=$RUN_DIR"
# 在仓库根目录启动,保证 kiro-cli 能加载 .kiro/steering
( cd "$REPO" && timeout "$LIMIT" "$KIRO_CLI" chat --no-interactive ${KIRO_TRUST_FLAGS:---trust-all-tools --trust-workspace} "$PROMPT" ) \
  >"$RUN_DIR/agent.log" 2>&1
rc=$?
log "end: exit=$rc"

# 只认「独占一行」的标记(可带列表符号或反引号),避免把「未标记 needsOwner: true」这类句子误判
if [ -f "$DIGEST" ] && grep -qE '^[[:space:]*-]*`?needsOwner:[[:space:]]*true`?[[:space:]]*$' "$DIGEST"; then
  printf '%s %s %s\n' "$(date '+%F %T')" "$TASK" "$DIGEST" >>"$STATE_DIR/needs-owner.log"
  log "needsOwner: true -> $STATE_DIR/needs-owner.log"
fi
exit "$rc"
