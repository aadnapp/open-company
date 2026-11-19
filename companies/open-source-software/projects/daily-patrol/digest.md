# 晚间复盘 digest · 2026-11-19(手动在 IDE 触发,补 11-18 晚间场)

数据来源:`~/.local/state/open-company/digests/2026-11-18`、`2026-11-19` 下三个角色的 digest,以及 Weband `goal.md`、`handoff.md`。`products/open-compare` 只是参考模板,不对账。`.munk/now.md`、`goals/index.md`、`.opencode/skills/`、`toolchains/tabs.json` 不存在,记「无数据」。

## 一、基础设施问题(需用户处理)

- **cron 的 daily-patrol 连续失败**:11-17、11-18 两个 21:00 场都以 exit=1 结束,没有产出 digest。原因在 `runs/daily-patrol/<时间>/agent.log`:Kiro 月度用量用完(`ServiceQuotaExceededException`,reason `MONTHLY_REQUEST_COUNT`,建议动作 `enableOverages`)。11-16 之前的场未查。按公司准则「对外承诺必须绑定实际开启的定时任务」,今晚 21:00 的场大概率仍会失败。
  - 建议:用户决定是开启超额用量,还是把晚间盘点改为只在 IDE 手动跑,并把 `crontab` 里这一行注释掉、`operator-manual.md` 同步。本复盘没有改 crontab。
  - 注意:cron 的 `build_digests.py` 每小时汇总不依赖 Agent,仍在正常生成。

## 二、产品对账

| 产品 | handoff 最近更新 | 判定 |
|---|---|---|
| Weband | 2026-11-18(本次同步为 11-19) | 在推进,不督办 |
| OpenCompare | 不对账 | 参考模板 |

### Weband 昨天(11-18)的结果
- **阶段 1 结案条件全部通过**:oppo + App 1.4.0 走通发现连接、配对、鉴权、状态、录音同步、解绑(`0046`)。
- 修了三处互通问题:广播缺服务 UUID、缺控制特征 `…ef2`、鉴权后缺 `device_features`(「正在验证设备」循环)。
- **按键配对跑通**:默认上报 `hw=2`、`fw_version` `2.15.35`、`caps` 含 `button_pair`,原版 App 改发 `button_confirm`,单击电源键配对成功(`0048`、`0049`)。同时修了灵感录音偶发立即超时(`elapsed_ge` 负差)。
- SD NAND 根目录满导致整夜停录:已修(录音改放 `/weband/rec/r/`,`0042`)。门控密度门 15/38 合入,敲击 0 段(`0043`–`0045`)。
- 差异分析 1.3.1 → 1.4.0 → 1.5.0 完成(含 Hermes 反编译)。
- 已推送 `origin/main` = `a2583d8`。V1 跑开发版 `7c8be8e9…`(`0050`)。
- 晚间充电采样(`0051`):18:26 插着充电器报充满(`charging` 1→0、`full` 0→1),说明不用复位就能置位;采样在 18:55 因电脑 OOM 重启中断。

### 今天(11-19)上午
- 查明重启原因:内存耗尽(3 个 java 进程约 4 GB,来源未明),交换区已扩到 8 GB,公司准则新增第七节 jadx 限 2 GB 堆。
- jadx 核实协议细节,写入 `refdevice-files/analysis/protocol-1.5.0-from-jadx.md`。
- `device_settings` / `device_event` 上报写好,分支 `device-report` `1ea7860`,主机单测 91/91,**未上板、未合入 main**。

### 卡点与待用户决定
1. 充电采样 `0051` 没有跑完:回充(掉到约 4065 mV 后是否重新充电)与拔掉充电器后 `full` 的行为没有数据;当前充电器已不在位。`goal.md` 的「充电时不报充满」待办据此部分推进(置位已确认,回充未测)。
2. `device-report` 分支等用户确认烧录上板,看 App 是否即时刷新充电状态。
3. 阶段 2 四项范围待用户定(复现范围、技术栈、仓库、与阶段 1 的先后);结案条件草案待确认;`AGENTS.md`「本阶段不做手机端 App」待改写。
4. 遗留 2b:`device_features` 的 `caps` 各项(`night_schedule`、`storage_clear`、`transfer_skip` 等)按需排期。
5. 未验证:改名中途掉电、文件数裁剪、`ACKED.txt` 原子替换上板、App 1.5.0 的升级入口实测。
6. 待办仍挂着:主控降配评估、无蜂鸣器的 LED 状态表、功耗偏高、莫斯码配对。

### 建议留话(给固件研发与实测)
- 先决定 `device-report` 是否烧录复测,再恢复回充采样(放到约 4.0 V 后插回,`battery_log.py … --slow 60`,电脑别同时跑多个 jadx)。
- 阶段 2 在用户定范围前只做不依赖范围的准备。

## 三、督办清单

无超过 3 天未更新的产品。

## 四、公司级 `AGENTS.md` 通用经验候选(待用户确认,本次未改)

1. **长任务与大内存工具的资源保护**:11-18 的重启由 jadx 等 java 进程耗尽内存引起。第七节已写 jadx 限 2 GB;候选补一句通用规则:无人值守采样(电池、串口)的原始日志写持久目录,不放 `/tmp`,且采样脚本每次落盘增量,重启后可续。证据:`0051` 的 `/tmp` 原始日志与收尾进程随重启丢失,只剩 `batt.csv` 23 行。
2. **定时任务依赖的 Agent 配额**:对外或对内承诺的定时任务,依赖的 Agent 额度耗尽时会静默 exit=1。候选:`run-task.sh` 在 `agent.log` 出现 `UsageLimitReachedError` 时写一行 `needs-owner.log`,避免连续多天无人发觉。

## 五、本次同步动作

- 2026-11-19 用户确认第四节两条候选,已写入公司准则第八节;`run-task.sh` 加了额度用尽检测(`bash -n` 通过,未实跑)。

- `handoff.md`:最近更新改 2026-11-19,顶部「现状」补 `0051` 充电采样与中断、cron 失败。
- `goal.md`:「充电时不报充满」待办补 `0051` 进展。
