# Weband 交接记录
最近更新：2026-11-23（待办16 完成：`5b192fd` 已推送（`origin/main` = `5b192fd`），正式版夜间计划台架 13/13 通过；板上为 `5b192fd`，未配对，夜间计划已关）

- **录音按小时一个文件（2026-11-19，Weband `01a195e`，已合入 `main`，2026-11-23 核对已随 `5b192fd` 推送，未发版）**：与参考设备一致，每个 UTC 小时一个 `M.D.HH.opus`，带分段表；灵感录音单独成文件，ACK 与清理按小时文件处理。主机单测全绿（test_hour 12/12），V1 构建通过，证据 `evidence/0056_hourly_rec_build/`。**没有烧录，上板验证等用户确认**（待测：整点跨小时、App 同步按小时文件、重启续写）。
  - 代码评审 APPROVED，留 4 条非阻塞发现（Weband `.agents/tasks/hourly-rec/review.md`）：① 某个旧 `NNNNNN.ogg` 读失败后，本次开机剩下的旧文件都不再上传（建议只在没有旧文件时才停）；② 从 TF 文件恢复的时钟标为 stale、不参与命名，比设计 §4 保守；③ `mb_clock_set` 超过一天未读时总是重设基准，休眠一天以上的路径待确认；④ 上板项未验证：RTC 休眠保持、`file_spans` 帧与 `srcMs`、`duration_ms`、文件间空档 < 200 ms、掉电续写、`ftruncate`/长文件名（设计 §14 第 1 步要先上板确认）。
  - **Nano 实测（2026-11-19，Weband `evidence/0057_nano_hourly_rec/`）**：`01a195e` 的 `file_spans` 用了 MBF1 类型 3，App 当成 `file_end` 回 error 并重连；一个旧文件读失败后，所有旧文件都停传。修复 `6ce68e5` 已合入 `main`（2026-11-23 核对已推送；当时 Nano 跑这一版）：一次连接传完 217 个文件、0 error，文件间空档 6–32 ms；跨整点、热重启续写、清理通过。未测：空小时文件、App 同步时状态是否还跳（用户暂不看）、V1 上的 SD NAND 行为。
  - 文件名的"时"是 UTC；`file_start` 带 `start_ts`，App 用它显示本地时间。从未校时期间文件名 `REC_<n>.opus` 是推断（设计 §13）。
## 现状
- **待办16 收尾（2026-11-23，`evidence/0091_v1_release_night/`）**：`5b192fd` 已普通推送，推送前查过没有参考设备名、广播名前缀和令牌。正式版上 `ble_night_check.py` 13/13：窗口 12:13–12:17 开始即封口、休眠、停止广播，窗口结束 11 s 后 RTC 唤醒，计划在休眠后仍在。V1 现在未配对、夜间计划已关、没接充电器，新手机要重新按键配对。测试前主机扫不到设备、`reboot` 后正常，原因没查明。
- **新手机配对超时（2026-11-23，Weband `5b192fd`，`evidence/0088_v1_newphone_pair/`、`0089_v1_factory_no_link_encryption/`、`0090_v1_no_link_enc_repair_over_idea/`）**：原因是旧固件的 GATT 要求加密链路、连接时还主动发安全请求，没有系统绑定的手机每次连接都弹 Android 配对框，没人点就 30 s `SMP_RSP_TIMEOUT`，App 报连接超时并每 30 多秒重连一次。核实原厂 V1 不加密链路（24 h 日志 0 次加密事件，特征权限 NO_AUTH，App 不调 `createBond`）。用户选方案 A：GATT 改 NO_AUTH、去掉连接时安全请求、配对不再要求加密；同时定双击清配对优先于灵感录音（先结束并封好录音段再清）。单测 96/96，V1 已烧录（`93eb4b7c…`，回读 MATCH）。实测：新手机按键配对成功、系统配对框 0 次；灵感录音中双击 → `re-pair overrides the running idea recording` → 录音段封口 → 清令牌与绑定 → 重启，通过。代价：空口不加密，与原厂相同。双击要两下间隔 ≤ 400 ms，用户前两次按慢或按太短都没识别成双击。
- **无人待办进展（2026-11-20 19:35）**：
  - App 电量与剩余时间改为自动采：`evidence/0081_app_battery_auto/poll.sh` 每 5 分钟用 `adb uiautomator dump` 读设置页文本，写 `app_battery_auto.csv`（19:22 读到 89%、22 小时）；前提是手机亮屏、App 停在设置页（脚本每轮先发唤醒键）。日志里没有 App 的电量帧（logcat 只有连接时的 `device_status`），所以没用日志。串口 `0079`、App 日志 `0080` 仍在记。
  - 待办15 已修（`aadf1f0`，已合入 `main`，2026-11-23 核对已推送）：`storage snapshot` / `storage clear` 两行字节数改成 KiB 用 `%lu`；V1 构建通过，未烧录（协议回复里的 `%llu` 走自带格式化，不动）。
  - 待办19：ggwave 主机仿真 `0082`（窄带滤波 + 噪声 + 16 kHz）：平坦与 2000 Hz 带宽基本全通；800 Hz、SNR 5 dB 掉到 0–2/20；400 Hz、SNR 15 dB 掉到 0–4/20。MLT-5030 真实频响没查，仍要 V2 板上扫频。
  - 待办9：评估 `0083`：PSRAM 用量为 0（`0023`），523 / 520 都够用；520U36 要外供 VDD18、外设差异未核对；不阻塞。
  - 待办12：第一条（旧文件读失败后停传）已在 `6ce68e5` 修掉；第二条 TF 时钟 stale 是设计取舍；第三条 `mb_clock_set` 休眠超一天的路径没分析，仍待办。待办13：跨午夜窗口主机单测已有（N1、N5、N6 覆盖 wrap、次日、开机在窗口内），不用再补；剩余项要真机。
  - 待办8 [中][进行中] 功耗偏高（平均约 37–41 mA，构建无 `RT_USING_PM`）：SDK 默认休眠模式为 IDLE、空闲≥30 ms 才进深睡，主循环 10 ms 轮询进不了深睡；`pm-light-sleep` 分支（`.worktrees/pm-light-sleep`）只加 `CONFIG_BSP_USING_PM=y`，V1 构建通过未烧录（有未提交改动）。V1 原厂固件放电 24.8 h 的串口记录已完成（`evidence/0079`，4094 mV/91% → 3704 mV/44%，全程空闲、BLE 连着、无任何低功耗状态，粗算平均约 8–9 mA，Weband 实测推算 37–41 mA，相差 4 倍以上）；2026-11-21 19:30 按计划停记录，板子未关机，之后状态未知。无电流表，靠串口 vbat 做相对对比。原厂低功耗机制已逆向（`.agents/tasks/v1-runtime-hours/report.md` 第三节）：空闲 WFI 钩子/deep-WFI（默认待确认）、空闲 60 s 降到 96 MHz、空闲 5/15 分钟分级降轮询、夜间窗口关机、小时账本；**原厂在持续录音加 BLE 连接时也没有进任何低功耗**（账本 `pm 0 lcpu slp 0s q1 0s q2 0s`），所以 Weband 功耗高未必是软件休眠缺失，要在同样负载下比 vbat 下降速度。下一步：Weband 抓同样的 vbat 日志做相对对比；再决定是否做主循环事件驱动。
  - 待办20①（反编译 V1 原厂固件找 `runtime_hours`）：另有 workflow 在跑（`refdevice-files/analysis/v1-runtime-hours/`），本会话没动。
  - Weband 仓库工作区仍有另一会话未提交的改动（`SConscript`、`main.c`、`mb_proto.h`、`CHANGELOG.md`、`VERSION`、`evidence/digest.md`），没动。
- **V1 写回原厂固件作功耗基准（2026-11-20，用户同意，`evidence/0078_v1_factory_baseline/`）**：先整片读回 16 MB 作还原点（`weband_before_16MB.bin`，SHA-256 `3d9a7b53…87bc12e`，当时板上是 Weband `main` 开发版），再把 `refdevice-v1/flash_backup/v1_nor_full_16MB.bin` 以 `write_flash --verify` 整片写回 `0x12000000`，exit 0。V1 现在是原厂固件，Weband 的配对、夜间计划、NOR 数据已被覆盖；SD NAND 录音未动。开机与原厂 App 配对已确认正常（用户口述，2026-11-20）。**未做**：电压放电曲线。2026-11-20 18:36 起测（充电器已拔，App 93%），读数写 `evidence/0078_v1_factory_baseline/app_battery.csv`，串口原厂日志由 `evidence/0079_v1_factory_runtime/capture.py` 从 18:42 起后台持续记录（逐行落盘，直到关机；原厂固件调试口有日志输出，之前判断「串口无输出」不对）；用户定周一充满后重测；电量读数要用户隔 1–2 小时报时间、电量、App 剩余时间（待办20 用），串口日志（`0079`）与手机 App 日志（`0080`）已在后台自动记录，不靠人。`pm-light-sleep` 工作树（`.worktrees/pm-light-sleep`）有未提交的 `proj.conf` 改动（加 `CONFIG_BSP_USING_PM=y`），下一步把主循环改成事件驱动才能进深睡，等基准测完再做。恢复 Weband：用 `scripts/build.sh` 构建后按 `sftool_param.json` 烧 4 个镜像，或写回 `weband_before_16MB.bin`。
- **`transfer_skip` V1 已配对台架通过（2026-11-20 15:27，`main` `685cbc5` 开发版，Weband `evidence/0076_v1_skip_paired/`）**：按键配对取令牌后 `ble_skip_check.py` 24/24，含已配对未鉴权 `skip_add` 回 `auth_required`；错 CRC 23/23（`0075`）。`0073`/`0074` 扫不到板子是脚本默认前缀 `Weband-` 与 V1 现用广播名不符，不是板子问题。收尾已 `unpair`；用户随后在 App 按键重新配对（2026-11-20），V1 现已和手机配对。
- **V2 蜂鸣器型号与出声传消息评估（2026-11-20，只读 `refdevice-v2/ProPrj_V2…_2026-11-20.epro2`，未做实测，原待办19）**：V2 `BUZZER1` 是 MLT-5030（C95297，华能）无源电磁式蜂鸣器，谐振 4 kHz、3 V、约 80 dB、约 100 mA，控制网络 `BUZZER_CTL`；V1 无蜂鸣器。无源器件，频率由 PWM 决定，离开 4 kHz 声压下降（频响曲线未查）。结论：ggwave 接收端可行，发送端在 MLT-5030 上宽频不平，不推荐；窄带方案（OOK/莫斯码、2-FSK）更合适。详见待办19。
- **待办4 台架（2026-11-20 13:05，V1 正式版 `f6be3f5`，`evidence/0068_v1_skip_checks/`）**：`ble_skip_check.py` 19/19（开放模式，无令牌），只有 1 个文件 `11.20.12.opus` 所以错 CRC 步骤跳过。前三次连接失败：电脑 BlueZ 缓存着旧绑定，连接时发起加密，板子认不了；`bluetoothctl remove <板子地址>` 后通过。教训：只解绑 App、双击清板子配对还不够，BlueZ 缓存也要删。V1 现在开放模式，手机未配对。
- **开发版只改广播名（2026-11-20，Weband `685cbc5`，原待办17）**：开发版环境变量由 `WEBAND_DEV_PAIR_CODE=1` 改为 `WEBAND_DEV_BUILD=1`，只换广播名前缀；删掉 `WEBAND_LOG_PAIR_CODE`（Kconfig 与宏）、开发版开机提示与 `fw` 提示；`code_pairing` 恒为 false（输码配对恒回 `unsupported_method`）。按用户要求，配对码打印两个版本都留着（`pair code NNNNNN`）。V1 开发版构建通过，已烧录（13:09，`main.bin` `831d32c4…`，只写 `main.bin@0x12020000`，回读 MATCH，`evidence/0069_v1_dev_name_only/`），已提交 `685cbc5`；`fw` 无开发版提示。用户双击电源键清配对后，原版 App 连上了（广播名前缀 App 认得，用户反馈，2026-11-20）；按键配对通过（`evidence/0077_v1_dev_pair_log/`）；串口没有 `pair code` 行，因为按键配对不生成码、输码配对已关，保留的打印代码走不到（是否删掉待用户定）。`scripts/ble_m2_check.py`、`ble_ota_check.py` 仍靠输码配对，已不能用。
- **V1 跑正式版，按键配对通过（2026-11-20，`main` `f6be3f5`，Weband `evidence/0065_v1_release_build/`、`0066_v1_release_pair/`，原待办2）**：main.bin `59b21ebc…f3f9db`，只写 `main.bin@0x12020000`，`--verify` 与回读通过；开机、录音正常，无配对码打印，广播名 `Weband-`。一开始配不上：板上留着开发版时期的配对令牌（只写 main.bin 不清），推断 App 收到 `already_bonded` 后放弃；双击电源键清配对后，App 第一次报"连接设备超时"，再连上并配对成功（令牌重新写入）。超时那一次的原因没查。夜间计划在正式版上未测。
- **配对 / 鉴权回复日志（2026-11-20，Weband `40661cb`，已合入 `main`；2026-11-23 核对已推送，板上 `5b192fd` 已包含）**：`pair_result` / `auth_result` 每条只带状态的回复都打 `reply … status=…`。主机单测 96/96，V1 正式版构建 `12782cbe…`（`evidence/0067_v1_pair_reply_log/`）。
- **App「清空设备内存」走通（2026-11-20 12:23，V1 `f6be3f5`，Weband `evidence/0064_v1_app_storage_clear/`）**：用户在原版 App 点清空并确认，`storage_info` → `storage_clear` 删除 5/5（含 1 个未送达），录音随即恢复；V1 现在只有清理后新录的当前小时文件。
- **V1 现跑 `main` `f6be3f5` 开发版（2026-11-20 12:14，Weband `evidence/0063_v1_main_f6be3f5/`，原待办1）**：main.bin `46818905…`，只写 `main.bin@0x12020000`，`--verify` 通过、回读 MATCH；开机正常（SD NAND、RTC 时钟、3 个小时文件排队、夜间计划关、约 3 s BLE 广播），录音在跑。App 核对电量补偿通过（用户看：充电 93 %、拔掉后 92 %，原待办14）。V1 开放模式。未测：夜间关机日志的 `%lu` 修正（见待办13）。
- **合并（2026-11-20）**：上述分支已全部快进 / 变基合入本地 `main`（`f6be3f5`，已推送（2026-11-20，`origin/main` = `f6be3f5`，含另一会话的 3 个提交））；电量补偿测试改号 S97。已清理已合入的工作树与分支，`transfer-skip`、`v1-skip-comp` 已删除（2026-11-20，内容已在 `main`；`0058` 烧的 `da4b666` 只能经 reflog 找回）；`app-interop` 工作树与 `dev-adv-name` 分支也已删除（2026-11-20，已合入 `main`），现在只剩主仓 `main`。板上跑 `732a08e` 开发版，`main` 另有 `f06899f`（日志格式）、`f6be3f5`（电量补偿，App 实测过但 `main` 版没再烧）。
- **能力三项与文件名真机通过（2026-11-20，V1，`evidence/0062_v1_name_clear_night/`）**：分支 `hour-name-local`（`f06899f`；链 `skip-on-hourly` → `storage-clear` → `night-schedule` → `hour-name-local`，`main` `6ce68e5` 之上）。`storage_clear` 12/12（删除 V1 上 16 个未同步录音，用户同意）；`night_schedule`：设 09:44–09:48 窗口，窗口开始后停止广播、结束后 10 s 内 RTC 唤醒、计划保留；`transfer_skip` 20/20（`0060`）；电量补偿 App 实测 95 → 96。小时文件名改为北京时间（UTC+8，App 用文件名按本地时区推起始时间）。板上跑 `732a08e` 开发版（`43a54f47…`）；`f06899f` 只改了一行日志格式，未烧录。
  - **V1 当时（2026-11-20，已过时，现状见顶部）**：不在充电器上，开放模式（手机未配对，要用按键重新配对），夜间计划已关，电量约 4.08 V。
  - **待办**：① 合并（建议按链依次快进到 `main`；`batt-pct-comp` 单独，S93 撞号要改；`main` 比 `origin/main` 多 3 个另一会话的提交，未推送）；② ~~开机慢~~ 已排除（2026-11-20：串口日志时间戳是 32768 Hz 计数，实测开机约 3 s 录音就绪、约 5 s BLE，见 Weband `evidence/digest.md` 同日一节）；③ 正式版交付构建；④ ~~`digest.md` 重复段清理~~ 已清理（2026-11-20，备份在 `/tmp/digest.before_dedup.md`，重启会丢）；⑤ 夜间关机的休眠功耗、跨午夜窗口未在真机测；⑥ 小时文件名固定 UTC+8、无年份。
- **`storage_clear`、`night_schedule`（2026-11-19 晚，用户定要做，顺序做完）**：已在分支链 `skip-on-hourly` → `storage-clear` → `night-schedule`（Weband，`main` `6ce68e5` 之上，**未合入、未上板**）实现，主机单测全过，V1 与 Nano 构建通过。细节与自有定义见 Weband `evidence/digest.md` 同日两节。台架脚本：`scripts/ble_storage_check.py`（`--really-clear` 才删录音）、`scripts/ble_night_check.py`（要 V1 不在充电器上）。
  - **下一步（要用户在场）**：烧录 `night-schedule` 开发版到 V1（含 `transfer_skip`、`storage_clear`、`night_schedule`；烧录前要确认）；先 `ble_storage_check.py`（非破坏），再按用户同意 `--really-clear`；再 `ble_night_check.py`（拔掉充电器、关手机蓝牙，约 8 分钟，RTC 闹钟唤醒是未验证的风险，唤醒失败按电源键）。
  - **`transfer_skip` 小时队列真机台架通过**（2026-11-19 19:10，V1，20/20，`evidence/0060_v1_skip_hourly_bench/`），V1 已回到开放模式（手机没有配对）。
  - 合并顺序建议：`skip-on-hourly` → `storage-clear` → `night-schedule` 依次快进；`batt-pct-comp` 单独，S93 撞号要改。`main` 比 `origin/main` 多 3 个另一会话的提交，未推送。
- **收工状态（2026-11-19 晚，用户下班）**：
  - V1 现跑 `skip-on-hourly` 开发版（Weband 分支 `skip-on-hourly`，`7819d40`，main.bin `8a5e07f9…`，`evidence/0059_v1_skip_hourly/`）：按小时录音首次上 V1，运行正常；旧 `NNNNNN.ogg` 2039 个已按用户要求删光（删前未统计，未同步的旧录音已丢）。V1 已用 App 按键配对，手机蓝牙由用户控制。
  - **待测（需要用户在场）**：`transfer_skip` 在小时队列上的台架。当前小时文件 19:00（北京）封口后队列才有文件，错 CRC 一步要两个已封口文件（20:00 以后）。V1 已配对手机，要先在 App 解绑并关 App/蓝牙，再用 `ble_m2_check.py --token-out`（令牌写 `/tmp` 权限 600）输码配对、`ble_skip_check.py --token ****`、主机 `unpair`，最后用户在 App 按键重新配对。步骤同 `0058`。
  - **未合入 `main`**：`skip-on-hourly`（transfer_skip，等台架）与 `batt-pct-comp`（电量补偿，App 实测 95 → 96 通过；合并时测试场景 S93 与 `main` 已有的 S93 撞号，要改号）。`main` 比 `origin/main` 多 3 个提交（`3ab1b65`、`01a195e`、`6ce68e5`，另一会话的，未推送）。`v1-skip-comp` 是旧上传路径的测试分支，可删。
  - **另一会话**在同一仓库工作（Nano、按小时录音、`0054`–`0057`），改 `main` 前先看 `git log main` 与 `git worktree list`。
  - 拔掉充电器后 App 的"充电中"约 4 s 消失，符合 5 s 轮询，不用修。回充阈值未测出（满电后充电器仍插着，5.8 h 电压 4192 → 4060 mV 未触发回充）。
  - 仍待用户定：`storage_clear`、`night_schedule` 是否做；正式版交付构建（V1 现为开发版）。
- **充电采样 `0051`（2026-11-18 18:24 起，中断）**：V1 插着充电器（开发版 `7c8be8e9…`），18:26 `charging` 1→0、`full` 0→1（4191→4170 mV），不用复位就能置位。采样计划到 23:30，18:55 电脑内存耗尽重启而中断（3 个 java 进程约 4 GB，来源未明；交换区已扩到 8 GB），只留 `batt.csv` 23 行；原始串口日志在 `/tmp`，已丢。19:16 读板：vbat 3811 mV、vbus=0、full=1，充电器已不在。回充行为未测。证据 `0051_v1_charge_full/`、`evidence/digest.md` 同日一节。
- **周边（团队级）**：cron 晚间盘点 11-17、11-18 两场失败，原因是 Kiro 月度用量用完，不是 Weband 问题（见 `projects/daily-patrol/digest.md`）。
- **回充阈值读回（2026-11-20，`evidence/0070_v1_rep_volt/`）**：`charger rep_volt 4065` 读回实际阈值 4057 mV，`0053` 末段 4060–4062 mV 高于它，所以没回充是正常的。回充动作与终止电流见待办18。
- **回充采样 `0053_v1_recharge/` 已收尾（2026-11-20，12:18–17:50，用户定 17:50 结束）**：V1 插着充电器，恒流 76 min（3854 → 4152 mV）、恒压 25 min（峰值 4193 mV），14:02:50 `full=1` 置位（`vbus=1`、`charging=0`），不用复位。之后 3.8 h 电压缓降到 4060 mV 未回充，回充阈值 4057 mV（`0070` 读回），回充动作未测（待办18）。`full` 要与 `vbus` 一起判断，已在电量补偿 `f6be3f5` 里用上。数据 `batt.csv` 与脱敏 `console.log` 入库，`raw_unredacted.log` 不入库。详见 `0053_v1_recharge/README.md`、`evidence/digest.md` 2026-11-20 一节。
- **`device-report` 已上板验证（2026-11-19，`0052_v1_device_report/`）**：已快进合入 `main` 并推送（`origin/main` = `1ea7860`）。开发版 main.bin `f183cf7a…`，用户用 App 1.4.0 验证重连鉴权、电量与充电状态显示、插拔充电器时状态刷新，三项正常（用户口述）。`device_diag` 未做。
- **电量百分比充电补偿（2026-11-19，未合入、未上板）**：用户观察充电时 App 41%、拔掉后 20%。原因：百分比由电池电压查放电曲线表，充电电流抬高端电压约 65–70 mV。分支 `batt-pct-comp`（`82f6139`，worktree `.worktrees/batt-pct-comp`）：充电时 `mv-65` 查表且封顶 99，充电器报 full 时 100。主机单测 92/92，V1 编译通过。补偿量来自一次恒流段观测，等回充全曲线核对后再合入烧录。
- **`transfer_skip` 已在 Nano 上台架通过（2026-11-19，`evidence/0054_nano_transfer_skip/`）**：分支 `transfer-skip`（已变基到新 main，`d12f469`），未合入。Nano main.bin `5d54c0ef…`，`scripts/ble_skip_check.py` 23/23 通过；第 8 步（已配对板上未鉴权回 `auth_required`）因板子未配对跳过。待办：已配对场景、原版 App 1.5.0 实测、V1 上板（回充采样结束后）；合并时注意与 `batt-pct-comp` 在 `test_main.c` 的场景登记行有小冲突。
- **Nano 上的 App 与固件检查（2026-11-19，`evidence/0055_nano_app_checks/`）**：App 1.4.0 与 1.5.0 都能在 Nano 上按键配对（一次单击）、同步录音（65 个 / 41 s，同一连接）；升级页「已是最新」，串口无 `arm_ota`，`denied` 路径未触发；App 没有发 `skip_add`（`skip_add` 路径只有台架脚本验证）；`ACKED.txt` 压缩正常路径通过（掉电中途分支未验证）；灵感录音立即超时 5/5 未复现（10 次单击 = 5 个来回，样本偏少）。App 解绑时若设备在线会把 `unpair` 发给设备（Nano 实测）；设备不在线时解绑只清 App 记录，设备仍是已配对（V1 现状）。
- **换绑时单击误开灵感录音（2026-11-19，用户定不改）**：Nano 换绑时一次窗口外的单击（App 还没发按键配对或窗口已过）开了灵感录音，配对窗口内的单击按设计只确认配对。用户决定不动代码。
- **Nano 启动断言已修（2026-11-19，Weband `3ab1b65`，已合入 `main`，2026-11-23 核对已推送）**：SD NAND 合入（`c8d54cc`）后 proj.conf 对所有板级开了 `spi_msd`（spi1），Nano 没有 spi1，开机断言。改为应用 Kconfig `WEBAND_SD_NAND`（depends on `BSP_USING_SPI1`）。V1 构建配置只多该符号，dfu/bootloader/lcpu 不变；V1 未烧录这一版。Nano 现跑 transfer-skip 开发版（`WEBAND_DEV_PAIR_CODE=1`，广播名用 App 认的前缀，main.bin `225eeec3…`，开发版台架 23/23 通过），录音在 NOR，开机迁移 65 段用了约 8.4 s（日志时间戳为 32768 Hz 计数，不是 ms）。
- **能力 `caps` 三项核对（2026-11-19）**：协议、状态串与工作量见仓库外 `refdevice-files/analysis/caps-night-storage-skip.md`。建议顺序 `transfer_skip`（小）→ `storage_clear`（中）→ `night_schedule`（大，需墙钟与 RTC 唤醒）。等用户定做哪几项。
- **能力上报 `device_settings` / `device_event`（实现说明；已合入、上板验证见上方）**：Weband 分支 `device-report`（`1ea7860`）。`status_request` 现回 `device_features`、`device_status`、`device_settings`；鉴权后（或未配对的开放链路）每 5 s 查一次电池，充电或充满状态翻转、百分比变化 ≥2 时发 `device_event`（`seq`、`charging`、`battery_percent`、`full`），每条新链路第一次只记基线不发。主机单测 91/91（新增 S90–S92），V1 正式版构建通过，无新警告。字段格式来自 V1 固件字符串；取值（夜间 0/0、`vad_gate`、`buzzer_level` 0）与 `full`（vbus 且 PMU full）是自有定义，代码里标了 `TODO(weband)`。`device_diag` 未做。App 即时刷新已上板验证；`full` 规则等回充采样验证。
- **阶段 1 原版 App 互通（2026-11-18）**：oppo 手机 + App 1.4.0 走通发现连接、输码配对、鉴权、状态显示（电量 23%、版本 1.15.35）、录音同步（50 多段）、解绑。证据 Weband `evidence/0046_v1_app_interop/` 与 `digest.md` 同日一节。
  - 修了三处才连得上：① 广播没带服务 UUID，App 扫描过滤掉了；② 缺 App 写命令用的控制特征 `…ef2`，App 连上后一条命令也不发、超时；③ 补 `status_request` → `device_status`（`hw`=1、`fw_version` 1.15.35，用户定），App 的 `arm_ota` 回 `denied`，升级包不装。
  - **V1 现跑台架版** main.bin `fcec5d93…`：配对码打到串口（本地 `CONFIG_WEBAND_LOG_PAIR_CODE`，未提交），广播名用参考设备名前缀（用户要求；值在仓库外 `~/.config/weband/adv_name`，构建时 `WEBAND_ADV_NAME=…`）。设备当前未配对。
  - "正在验证设备"循环（2026-11-18）：App 1.4.0 鉴权后等 `device_features`，没有时 9 s 探测先拆链。已改为 `status_request` 后补回 `device_features`（`caps:[]`），提交 `0d52b20`，已烧录；手机复测通过（关开蓝牙后约 1.4 s 发出 `ready`，无探测超时，`evidence/0046_v1_app_interop/app_logcat_after_features.txt`）。V1 现跑 main.bin `a9c680df…`（仍是台架版：打印配对码 + 本地广播名）。已推送 `origin/main` = `73447b6`（2026-11-18，普通推送）。caps 各项待办见 `goal.md` 遗留 2b。
  - 无屏配对已定（2026-11-18 用户）：产品用按键配对（`button_confirm`），开发阶段可从串口看配对码。Weband `948150c`：`WEBAND_DEV_PAIR_CODE=1` 编开发版（打印配对码），默认正式版不打印。`6db9588`：正式版收到输码配对回 `unsupported_method`（用户定）。**V1 现跑开发版** main.bin `a85f04e5…`（`evidence/0047_v1_dev_build/`，用户定）。Weband 本地 `main` 当时比 `origin/main` 多 5 个提交（2026-11-23 核对已全部推送）。正式版不能用原版 App 配对；差异分析发现原版 App 在 `hw=2` 且 `caps` 含 `button_pair` 时会走按键配对，是否这样做待用户定（`goal.md` 阶段 2）。
  - **原版 App 按键配对实测通过（2026-11-18 16:42）**：实验开发版（`hw=2`、`fw_version` 2.15.35、`caps:["button_pair"]`，main.bin `53320156…`，V1 现跑这一版）上，App 1.4.0 发 `button_confirm`，单击电源键后配对成功（`evidence/0048_v1_hw2_button_pair/`）。17:00 前后 `hw=2` 下其余步骤全部复测通过（`evidence/0049_v1_hw2_full_check/`）。用户随后定：正式版与开发版都默认 `hw=2` / `2.15.35`（`68a9010`）；灵感录音偶发立即超时已修（同提交，`elapsed_ge` 负差）；广播名开发版自动用 App 认的前缀（读仓库外 `~/.config/weband/adv_name`）、正式版 `Weband-`（`ba0eec3`）。**V1 现跑新开发版** main.bin `7c8be8e9…`（`evidence/0050_v1_dev_hw2_default/`），启动后手机自动重连鉴权。已推送 `origin/main` = `a2583d8`（2026-11-18，普通推送）。
  - 原版 App 差异分析（2026-11-18）：1.3.1 → 1.4.0 → 1.5.0，原生 BLE 模块部分，报告在 `/home/whole/data/reawork/refdevice-files/analysis/app-diff-1.3.1-1.4.0-1.5.0.md`（不入库）。1.4.0 安装包已从 `refdevice-v1/` 移到 `refdevice-files/`，1.5.0 在 `refdevice-files/`。
  - 主机 BlueZ 缓存旧 GATT 时 bleak 报 KeyError，`bluetoothctl remove <地址>` 后正常；手机同理要取消配对再连。
  - 台架脚本：`scripts/ble_status_check.py`（device_status、App 式 arm_ota 被拒）；台架 OTA 改发 `{"type":"arm_ota","dev":true}`。按名字过滤 `Weband-`，本地改名构建下要改前缀。
- **SD NAND 根目录满导致停录，已修复（2026-11-18）**：V1 从 11-17 傍晚（0037 之后）到 11-18 上午 0 次成功开段，整夜没录音。原因（0041 `sddiag` 证实）：卡是 FAT16，根目录固定 512 项，511 段录音 + `ACKED.txt` 占满；裁剪只看空间不触发。修复：录音改放 `/weband/rec/r/`（`ed5433d`），开机迁移 510 个、自动删最老已 ACK 的 `000001.ogg`（电脑有副本）腾项；裁剪加文件数上限 4000。V1 实测开段恢复、BLE 拉取 17/17（`0042_v1_rec_subdir/`）。已合入 `main` 并推送（`origin/main` = `87b2059`）。V1 现跑这一版（main.bin `f7b5da29…`）。未测：改名中途掉电、文件数裁剪、Nano 路径。SDK `dfs_elm_mkfs` 的 `MKFS_PARM opt` 未初始化（另记，未改）。
- **录音改存 SD NAND（2026-11-17 上板通过，已合入 Weband `main` 并推送，`origin/main` = `24fe09e`）**：原分支 `board-weband-v1` 变基后快进合入，worktree 与分支已删，变基前备份分支 `backup-board-weband-v1-pre-rebase`，V1 上跑 main.bin `e2c67fa3…`。SD NAND 挂到 `/weband/rec`，`df` 119.9 MB；重启后已关闭的段还在；BLE 拉取 25/25。证据：Weband `evidence/digest.md` 2026-11-17 一节、`evidence/0032_v1_sdnand/`。
  - 修了两处：板级打开 LDO3（推断 `VDD33_VOUT2` = `VDD33_SDCARD`）；DFS 挂载表从 2 改为 4。
  - **数据丢失**：第 2 次烧录时，挂载表满被误判成"卡上没有 FAT"，SD NAND 被格式化，原厂固件写在卡上的内容没有备份，已经清掉了。现在只在扇区 0 没有 0x55AA 签名时才格式化。
  - 遗留已处理（2026-11-17，`evidence/0033_v1_sd_migrate/`）：开机把 NOR `/weband/rec` 里的录音迁到卡上，203 个全部迁移，SHA-256 逐个核对无缺失，NOR 空闲回到 3.9 MB；休眠前封口录音并关 LDO3：2026-11-17 台架版实测通过（`evidence/0034_v1_hibernate_seal/`，封口后的段大小与日志一致、能解码，`ldo3_en=0`）；休眠时串口乱码已定位并修复（台架打印在 NOR 断电后从 NOR 执行；现先关 LDO3 再关 NOR 供电，复测无乱码、电源键唤醒，`evidence/0035_v1_hibernate_uart/`）。V1 上跑正式版 `77e824b8…`，正式版休眠尚未在实物上触发过。LDO3 对应关系仍无文档依据。
- **V1 实物整片备份（2026-11-16，上 Weband 固件分步方案第 1 步）**：V1 经 USB-C 转 TTL 转接板接 `/dev/ttyACM0`，用 `sftool read_flash` 只读读出 16 MB NOR，SHA-256 `db02fe1a…84acb917`，存仓库外 `/home/whole/data/reawork/refdevice-v1/flash_backup/v1_nor_full_16MB.bin`（不入库）。bootloader 与手头原厂镜像一致，main、dfu 不一致（V1 上是别的版本），还原只能用这份备份。读完 V1 自动重启，运行正常。记录在 Weband `evidence/digest.md`（未提交）。
  - 第 2 步已完成（只编译）：板级 `sf32lb52-weband-v1` 在 Weband worktree `.worktrees/board-weband-v1`，分支 `board-weband-v1` 提交 `1263e2a`，未合入 `main`。525、8 MB PSRAM `MPI1_MODE_3`、片内充电、引脚按 V1 网表核对；电池保护（自有定义）：4200/4350 mV、120 mA，开机 <3500 mV、运行中 <3400 mV 无充电器即休眠。PSRAM、VBAT 读数、充电、休眠都未上板验证。
  - 第 3、4 步已完成（2026-11-16，用户逐步确认后烧录）：先只写探测固件 main.bin（方案 B），V1 原 bootloader 能引导，PSRAM 8 MB 0 错，PA34 电源键可读，10 s 强制复位通过；再 4 个镜像全刷完整 Weband（方案 A，提交 `3934534` 构建）。V1 上实测：开机、V1 模拟麦录音、BLE 广播 `Weband-44D1`、按键配对 → 鉴权 → 拉 16 段录音 69/69 → 解绑回开放模式、单击录灵感和 60 s 超时关闭，全部通过。证据在 Weband `evidence/digest.md` 与 `evidence/0026_v1_ble/`、`evidence/v1_*.log`（未提交）。
  - V1 现在跑的是 Weband，原厂固件可用 `refdevice-v1/flash_backup/v1_nor_full_16MB.bin` 整片写回。
  - 已了结（2026-11-17）：600 ms–6 s 的按压已有日志（`main.c` 的 `MB_KEY_IGNORED` 分支打印按住时长）；录音改走 SD NAND 已完成；拔掉充电器测电池保护和续航已完成（见下方电池测试，`0027_v1_batt/`）。
  - 接法（2026-11-16 用户确认）：转接板接 V1 的 3 针调试口（网表 U7：GND / TXD / RXD，不供电）；Type-C 另插充电器在充电。V1 的 Type-C D+/D- 和 3 针口并在同一对串口线上（A6/B6=TXD，A7/B7=RXD），CC 各有下拉电阻。整片备份就是在这个接法下读成功的，说明这个充电器不干扰串口，换充电器前要重新确认。
  - 电池测试已完成（2026-11-16 至 17，正式版，证据 `0027_v1_batt/`）：放电 10.4 h 后低电休眠（3377 mV），电源键唤醒、开机低电保护、充电器唤醒都走通；平均电流约 37–41 mA（推算）；录音区清理触发 6 次，录音没停。充电恒流 3.1 h + 恒压 1.8 h，一直没报充满（待办已记 `goal.md`）。电池标签 502525、3.7 V、450 mAh，带保护板（充电截止 4.25 V，放电截止 2.75 V）。
- **硬件工程去屏幕（2026-11-16）**：新建本地仓库 `/home/whole/data/reawork/weband_hw`（独立 git，未设远端），`weband.eprj2` 是参考设备 V1 开源工程的副本，用 `lceda-pro` 命令行修改：删 LCD 页和 12 个器件，U1 的 15 个 LCD 引脚改 No Connect，PCB 导入变更并清掉屏幕走线、残线，重建铺铜。原理图 DRC 仍是原有 16 条 warn；PCB DRC 通过，飞线 0 条。存储（SD NAND、NOR）未动，**未在 dev nano 上调试**。证据：`weband_hw/evidence/`（`25_netlist_diff.txt`、`30_connectivity_check.txt`、`32_pcb_final.json`），提交 `95fbdfb`（历史已重写，见下）。
  - 红线处理（2026-11-16 用户决定）：① `weband_hw` **只在本地保存，不设远端、不推送**，因为工程派生自 V1 开源设计，授权未确认；② README、提交说明、`evidence/03_src_info.json` 改为中性写法，本地历史已用 `filter-branch` 重写，现 `main` = `5ba782a`。工程文件内部仍带参考设备名，属于设计内容本身，仓库不外传，所以不改。重写前的备份分支 `backup-before-neutral` 和 `refs/original` 已按用户确认删除并 gc，旧提交已不可达。
- **M4 电源键部分：已完成（2026-11-13）**，已快进合入 Weband `main` 并推送（`origin/main` = `868654a`），worktree 与分支已清理，不入库的镜像与升级包已移到主仓 `evidence/0021_m4_power_key/`。板上跑 build 3（BLE OTA 装上），开放模式。证据：Weband `evidence/digest.md` 2026-11-13 M4 一节、`evidence/0021_m4_power_key/`。
  - 单击灵感（默认 60 s，`idea_toggle` / `idea_config` 按 V1）、双击重新配对（清令牌和 BLE 绑定后重启，录灵感时延后）、长按 6 s 重启、延后遇长按先解绑，都已实测。
  - 实测中修了两处：延后的重新配对会被长按重启丢掉；全新配对后第一次连接 App 层配对被拒（SDK 不发加密事件）。
  - 台架脚本连接改为 `connect_live`（老 BlueZ 扫描停止即删未绑定设备）。
  - V1 原理图：电源键 PA34 高有效（SKRTLAE010）；无蜂鸣器；SD NAND 走 SPI，接 PA24/25/28/29，Nano J1 有这四个脚。
  - 无屏配对已定（2026-11-13）：**真实用户通过按键完成配对**（按 V1 的 `button_confirm`）。固件侧已真机通过（2026-11-14）：用户单击 KEY1 约 39 s 后配对成功并拿到令牌；不按则 60 s 后回 `expired`。已合入 Weband `main` 并推送（`726f78e`），worktree 已清理。原版 App 不发这种方式，需要我们自己的 App 配合。
  - 待办（2026-11-13 用户提出）：**用敲击或"敲击 + 划动"组成的莫斯码完成配对**；识别用什么传感器、码怎么生成和比对都待定，见 `goal.md`。
- **硬件范围（2026-11-13）**：对标 V1，但 **Weband 不要屏幕**。V1 器件按其开源硬件页更新：SF32LB525UC6、128 MB SD NAND 存录音、16 MB SPI NOR、502525 电池、IMU 在板但固件不用。M4 改为只做电源（电源键 + 充电）。
- **M3 录音已完成（2026-11-13）**：已快进合入 Weband `main` 并推送（`origin/main` = `f83c252`），worktree 与分支已清理；工作树外的录音文件（`.ogg` / `.wav` / `fs_region.img`，不入库）已移到主仓 `evidence/` 下。板上跑 `main.bin` `5c0c03cf…0fd9`，处于开放模式（未配对）。
  - 录音：WebRTC VAD 门控（余量 8 dB、触发 6 帧）+ Opus SILK 16 kHz 24 kbit/s，60 s 一段写 `/weband/rec/NNNNNN.ogg`。
  - 存储：已用超过 2/3 开始裁剪（用户定），先删已传到手机的（`ACKED.txt`），再删最旧的，删到剩余 1/3 + 256 KB；5 分钟 fsync（用户定）；开机删空文件。实测：先删 9 个已 ACK、再删 3 个最旧，丢帧 0。
  - BLE 传录音：按原版 App 1.3.1 的 `ready` / `ack` + MBF1 帧实现。台架脚本 `scripts/ble_pull_check.py` 实测：基本拉取、丢块重传、断线续传都通过，206 个积压文件一次拉完 829/829。
  - 鉴权改为与原版 App 一致：`{"type":"auth","mac"}`，key 为令牌 hex 解码的 16 字节（M2 原实现与 App 不兼容）。
  - 上板修过的问题：main 线程栈 2 KB 溢出（改 8 KB，开机裁剪移到录音线程）；这次崩溃把 fs_region 的 rec 目录扇区擦成 0xFF，已在主机上重建元数据写回（旧测试录音丢失，有用的早已取回）。
  - 敲击测试未达标：敲击 1 分钟开 4 段；拉长触发到 12 帧仍有 2 段。用户决定 M3 先收尾，单独立项。夜里 22:00–07:00 无人时只开 3 段。
- **对标改为参考设备 V1 圆屏**（2026-11-10 用户决定）。依据：V1 固件 `1.15.35-v1-round-serial`（板级 `sf32lb52-refboard-v1`）字符串里有 30 处 audcodec/audprc、0 处 PDM，显示为 `jdi387a`，充电走片内 PMU；V2 固件 `2.15.12` 则是 22 处 PDM、0 处 audcodec、JD7601、LGS4056。V1 原理图（`/home/whole/share/mic_imu.webp`）的模拟麦 `MIC_BIAS`/`MIC_ADC` 与 V1 固件一致。此前文档里的"PDM 麦"只适用于 V2。
  - 已更新：`AGENTS.md`、`goal.md`、Weband 仓库 `docs/hardware-inventory.md`（第 2 节改为 V1 外设，V2 移到 2b，待核实项 C5）、`firmware-port.md` 资料入口。Weband 仓库的改动尚未提交。
  - 原 V2 设计文档（`/home/whole/data/reawork/refdevice-files/v2-design.md`）是 V2 设计，外设部分不再适用。
- M0 已完成（2026-11-09）：hello_world 在 Nano 上编译、烧录、回读一致、串口启动正常。
- M1 已完成（2026-11-10）：
  - 树外板级 `boards/sf32lb52-weband`，编译通过；除板名与 LED 极性外与 SDK 的 Nano 板等价。
  - 分区表核对：16 MB NOR 原样放下参考设备的分区布局，不重排。
  - 外设清点 `docs/hardware-inventory.md`；真机核对：LED（PA31/PA32）低电平点亮，KEY1=PA34、KEY2=PA33 按下为高。
  - weband 版已烧录上板：三区回读一致，串口启动、`Hello world!`、`msh />` 正常。

- 首次提交已完成（2026-11-10）：`main` @ `a6f1c46`（两个提交已合并为一个），38 个文件；SDK、Flash 镜像、板图不入库。
- 远端：`origin` = `git@github.com:aadnapp/weband.git`（私有）。2026-11-10 已推送 `main`，远端与本地同为 `a6f1c46`。

- M2 开工（2026-11-11）：worktree `/home/whole/data/reawork/weband/.worktrees/m2-ble-protocol`，分支 `m2-ble-protocol`（基于 main `606e0fa`）。提交 `5998086`：把我们早先示例的协议核心（mb_proto / mb_frame / mb_hmac）和主机单测移到 `app/`，`make -C app/test/host check` 72/72 通过。GATT / 存储 / 平台胶水（原 b2074d76）尚未移植。
- **M2 已完成（2026-11-11）**：已快进合入 Weband `main` 并推送（`57d10b1`），worktree 与分支已清理。协议按 V1 对齐（只核对 M2 命令），主机单测 75/75；真机 BLE 联调 `scripts/ble_m2_check.py --reboot --unpair` 17/17：pair → auth → ok、未认证 arm_ota 回 auth_required、认证后 armed、令牌跨复位有效、远程 unpair。修了两处上板问题：TRNG 未播种导致 rng_error；BlueZ 的 Just Works 需要 agent 授权（脚本自带 D-Bus agent）。（板上现在跑的是 M3 固件，见上。）
- 联调用 UGREEN 蓝牙适配器（RTL8761B），靠补丁版 btusb + 手工放的 rtl8761bu 固件才能用，见操作手册 6.8；换内核要重做。
- 两仓 2026-11-11 均已推送：Weband `origin/main` = `57d10b1`；open-company `fork/main`。

## 待办清单
<!-- 进度报告「产品待办」只读这一节。格式：- 待办<编号> [高|中|低][状态] 标题：说明。编号一经分配不改、不复用，新条目取当前最大编号加 1（已用到 待办25），删掉的编号不再用；对话里可用「待办N」指代。状态写 进行中 / 等用户 / 待定 / 排期。做完的条目从这里移到「## 已完成功能」对应功能下（保留编号），结论也写进「现状」，不要留划掉的。每次更新 handoff 都回看这一节。 -->
- 待办5 [中][待定] 阶段 2 复现参考设备 App：范围、技术栈、代码仓库、与阶段 1 的先后都待用户定；启动时还要改 `AGENTS.md`「本阶段不做手机端 App」。
- 待办6 [中][待定] 无蜂鸣器（V2 有 MLT-5030，见待办19）：配对确认、录音开关、重新配对、低电量、OTA 的 LED（PA31/PA32）闪法和是否加振动。
- 待办19 [中][待定] 蜂鸣器出声传消息方案评估（2026-11-20 提出）：V2 的 MLT-5030 是 4 kHz 无源电磁式蜂鸣器，V1 没有蜂鸣器，Weband 要用得先决定是否加（与待办6 相关）。候选方案：① ggwave（设备作接收端可行；发送端宽频在该器件上不平，不推荐）；② 固定 4 kHz 开关键控（OOK/莫斯码，最简单）；③ 2-FSK（3.8/4.2 kHz 两个频点）；④ 窄带多频 FSK；⑤ 脉冲间隔编码。验证顺序：先在 V2 上做 1–6 kHz 扫频实测各频点音量，再试 OOK、2-FSK，接收端用手机麦克风加 Goertzel；ggwave 另在主机用 16 kHz 录音 WAV 先验解码率。速率与可靠性都是估算，未实测；是否放宽「对标 V1」约束待用户定。 主机仿真已做（`0082`，ggwave 窄带下掉解码率，见现状）。
- 待办7 [中][待定] 莫斯码配对：IMU + 麦克风识别已定，码由谁生成、谁比对、与按键确认的关系待定。
- 待办8 [中][进行中] 功耗偏高（平均约 37–41 mA，构建无 `RT_USING_PM`）：已查明 SDK 默认休眠模式为 IDLE、空闲≥30 ms 才进深睡，而主循环 10 ms 轮询进不了深睡；`pm-light-sleep` 分支只加了 `CONFIG_BSP_USING_PM=y`，V1 构建通过未烧录。V1 已写回原厂固件作基准（见「现状」），无电流表，基准只能用电池电压降速率；有电流表或 INA219 后再测各场景。
- 待办9 [中][排期] 主控降配评估：523UB6 与 525 只差 PSRAM 容量，改动最小；520U36 需核实启动与分区；不阻塞打样。 评估已写（`0083`：PSRAM 用量 0，523/520 够用，520 要外供 VDD18）。
- 待办10 [低][排期] M5 OTA 遗留：离线包不签名、板上 `rt_tick` 慢约 1%、安装器两条告警、安装中掉电续装未实测；量产前换自有签名密钥。
- 待办11 [低][排期] 掉电类未实测：`ACKED.txt` 原子替换掉电中途、迁移改名中途掉电、文件数裁剪、正式版休眠在实物上触发。
- 待办12 [低][排期] 小项：`device_diag` 未做；App 1.5.0 升级入口未实测；评审 4 条非阻塞（旧文件读失败后停传、时钟 stale 策略等）；门控遗留（单字召回无旧基准、嘈杂背景误开段）；`dfs_elm_mkfs` 的 `MKFS_PARM opt` 未初始化（SDK，未改）。 2026-11-20 核对：旧文件读失败后停传已在 `6ce68e5` 修掉；`mb_clock_set` 休眠超一天路径未分析。
- 待办13 [低][排期] 夜间关机遗留：休眠功耗没测（没有电流表）、跨午夜窗口和窗口内电源键早醒只在主机单测覆盖；小时文件名固定 UTC+8、没有年份；板上旧 UTC 名与新名可能撞名（撞名时叫 `REC_<n>.opus`）。
- 待办25 [低][排期] 录音传输 `transfer done ack timeout`：2026-11-23 重连鉴权后传 `11.23.10.opus`（2307152 B）出现一次，设备稍后重试（`0090/console.log`）；原因没查，和配对改动无关。
- 待办18 [低][排期] 回充动作与终止电流未实测：回充阈值已读回 4057 mV（`0070`，`0053` 末段 4060–4062 mV 未低于它）；还要让电压降到 4057 mV 以下，看充电器插着时 `full` 清零、回到恒流；终止电流只读了源码默认（CC 的 10%，约 12 mA），没测电池电流。
- 待办22 [低][排期] 充电时电量补偿对齐原厂：原厂按充电器状态减 70 / 30 / 10 mV（`FUN_1204f73c`，状态 0x10 / 0x20 / 0x08），Weband 固定减 65 mV；另原厂只在充电且充满时强制 100 %。充电中的显示可能与原厂差几个点，未实测。
- 待办4 [低][排期] 空小时文件的传输：夜间安静小时会生成 106 字节的小时文件（2026-11-20 早上看到），看 App 同步时能否正常收下、不报错。其余验证已通过，见「已完成功能 · 设备能力 `transfer_skip`」。
## 已完成功能
### 正式版收尾（2026-11-23，`origin/main` = `5b192fd`，`evidence/0091_v1_release_night/`）
- 待办16 正式版收尾剩余：`5b192fd` 已推送；正式版夜间计划台架 13/13 通过；"双击清配对后第一次连接超时"已查明是系统配对框没人确认，`5b192fd` 已修（2026-11-23，`0088`–`0091`）。
### 配对不再弹系统配对框 + 双击优先（2026-11-23，Weband `5b192fd`，`evidence/0090_v1_no_link_enc_repair_over_idea/`）
- 待办23 新手机配对超时：去掉 BLE 链路加密要求与连接时安全请求，与原厂 V1 一致（`0089`）；V1 实测新手机按键配对成功，系统配对框 0 次（2026-11-23，`0088`、`0090`）。
- 待办24 双击清配对优先于灵感录音（用户 2026-11-23 定）：双击时先结束并封好灵感录音段，再清令牌和绑定、重启；V1 实测通过（2026-11-23，`0090`）。
### 电量百分比对齐原厂（2026-11-23，`0087_v1_factory_batt_compare/`）
- 待办21 电量百分比与原厂不一致：原因是 Weband 用了 SDK 板级 `battery_table.c`，原厂主程序用自己的 13 点表（`FUN_120559cc`，0x120d71a6）。改用原厂表（`0521506`，单测 96/96），V1 已烧录；与原厂对比：原厂 App 28 %/7 h，Weband App 26 %/7 h，同电压两边百分比一致（2026-11-23，`0086_v1_batt_pct_ref/`、`0087_v1_factory_batt_compare/`）。
### 剩余时间显示（待办20）
- 待办20 剩余时间显示不对：App 直接显示 `device_status.runtime_hours`；原厂公式 `((pct*450+50)/100+9)/18`（约 pct/4）读自 V1 固件 1.15.31 反编译。已合入本地 `main`（`19bc729`），主机单测 96/96，V1 正式版已烧录、回读 MATCH、开机 `fw` 正常（2026-11-23，`0085_v1_runtime_hours_flash/`）；App 实测通过（2026-11-23，用户：电量 4% 显示预计还能用 1 小时，公式算得 1 小时）。`runtime-hours` 分支与工作树已清理。
<!-- 进度报告把这一节放在产品卡片最后。格式：### 功能名（完成日期，证据），其下 - 条目。待办做完时，不直接删：把它连同编号移到对应功能下，写成「- 待办N 标题：结论（日期，证据）」；没有对应功能就新建一个 ### 功能。新完成的功能写在最上面。 -->
### 日志 `%lu` 修正（2026-11-20，Weband `aadf1f0`，未烧录）
- 待办15 `storage snapshot` / `storage clear` 日志把 64 位字节数打成字面量 `%lu` 且后一个参数错位：改成 KiB 用 `%lu`，V1 构建通过，主机单测不覆盖日志行；已合入 `main`，2026-11-23 核对已推送；板上 `5b192fd` 已包含。
### 开发版只改广播名（2026-11-20，Weband 工作区改动未提交）
- 待办17 开发版只改设备名：代码改完并提交 `685cbc5`，V1 开发版已烧录（`0069`）；配对码打印两版保留；板上按键配对通过，已提交 `685cbc5`（2026-11-23 核对已推送）（2026-11-20）。
### 回充采样 `0053`（2026-11-20，Weband `evidence/0053_v1_recharge/`）
- 原待办3 收尾分析：恒流 76 min、恒压 25 min，`full` 在 14:02:50 置位且不用复位，要与 `vbus` 联合判断；回充阈值未测出，转待办18。
### 设备能力 `storage_clear`（2026-11-20，Weband `evidence/0062_v1_name_clear_night/`、`0064_v1_app_storage_clear/`）
- 台架 `ble_storage_check.py --really-clear` 12/12：删除 V1 上 16 个未同步录音（用户同意），录音随即恢复（2026-11-20，`0062`）。
- 原版 App「清空设备内存」走通：`storage_info` → `storage_clear` 删除 5/5（含 1 个未送达），录音恢复（2026-11-20，`0064`）。
- 原待办「`storage_clear`、`night_schedule` 做不做」：用户 2026-11-19 定要做，顺序做完。
### 设备能力 `night_schedule`（2026-11-20，Weband `evidence/0062_v1_name_clear_night/`）
- 原待办「`night_schedule` 真机台架」：V1 拔掉充电器后 `ble_night_check.py` 全部步骤通过，09:44 窗口开始关机、09:48 由 RTC 唤醒、10 s 内重新广播（2026-11-20）。
### 设备能力 `transfer_skip`（2026-11-19，Weband `evidence/0054_nano_transfer_skip/`、`0060_v1_skip_hourly_bench/`）
- 原待办「`transfer_skip` 上 V1」：Nano 台架 23/23（`0054`），V1 按小时队列台架 20/20（2026-11-19，`0060`）。
- 待办4 中已完成部分（2026-11-20，V1）：开放模式 19/19（`0068`）；错 CRC 23/23（`0075`，用两个灵感录音文件）；已配对 24/24，含未鉴权 `skip_add` 回 `auth_required`（`0076`，按键配对取令牌）；用户反馈 App 1.5.0 同步时状态没有大变化、已配对同步正常。台架脚本要加 `--name-prefix`（V1 用 App 认的广播名前缀，值在仓库外）；输码配对已在所有版本关闭（`685cbc5`），板子按键确认窗口 30 s。
### 电量百分比充电补偿（2026-11-20，Weband `f6be3f5`，`evidence/0063_v1_main_f6be3f5/`）
- 原待办「电量补偿合入、烧录 V1」：变基合入 `main`（测试改号 S97），已推送（2026-11-20）。
- 待办1 V1 烧录 `main`（`f6be3f5`）：开发版烧录，`--verify` 通过、回读 MATCH，开机与录音正常（2026-11-20，`0063`）。
- 待办14 App 核对电量补偿：充电 93 %、拔掉后 92 %（2026-11-20，用户在 App 上看）。
### 录音按小时一个文件 + 北京时间文件名（2026-11-20，Weband `01a195e`、`6ce68e5`、`732a08e`）
- Nano 实测：一次连接传完 217 个文件、跨整点、热重启续写（2026-11-19，`0057_nano_hourly_rec/`）；V1 首次上板运行正常（2026-11-19，`0059_v1_skip_hourly/`）。
- 文件名改为北京时间（UTC+8），V1 上板（2026-11-20，`0062`）。
### 合并与推送（2026-11-20，`origin/main` = `f6be3f5`）
- 原待办「分支链合入 `main`」：`skip-on-hourly` → `storage-clear` → `night-schedule` → `hour-name-local` 快进，`batt-pct-comp` 变基后合入（2026-11-20）。
- 原待办「推送 `main`」：普通推送 `1ea7860` → `f6be3f5`，推送前核对没有广播名前缀、令牌、配对码（2026-11-20）。
- 遗留分支与工作树已清理，只剩主仓 `main`（2026-11-20）。
### M5 OTA / DFU（2026-11-13，Weband `origin/main` = `d3b0d9b`，`evidence/0020_m5_ota/`）
- 不开窗被拒 5/5；A→B 11/11；断线续传 9/9；OTA 后回读与最终版一致；配对跨三次 OTA 保持。遗留见待办10。
## 等待项（等人）
1. ~~采购 P1 外设~~ 已定（2026-11-17 用户）：硬件直接采用参考设备 V1，固件刷 `sf32lb52-weband-v1` 板级；不再为 Nano 采购 SD 卡模块或锂电版开发板，也不单独打板。
4. ~~`MBWP` 壁纸帧处理~~ 已定（2026-11-17 用户）：照收丢弃，不回不支持。固件现状：`mb_proto.c` 对 MBWP 只记日志、不存储（stub），已等同照收丢弃，不需要改动。
3. ~~录音存储掉电安全方案~~ 已收尾（2026-11-17，`fsync` 保持 5 分钟）：复位实测两次（`0036_v1_power_cut/`），正在写的段整段丢失（≤60 s，无法靠文件系统找回），已关闭的段与 FAT 完好。`ACKED.txt` 压缩改为写临时文件再改名，已合入本地 `main`（`33729d2`），V1 构建通过，**未上板实测**。已推送 `origin/main` = `7babd9c`（SSH 恢复后普通推送，无强推）。sidecar、按小时文件不做。

## 下一步
- **明天继续（2026-11-17 收工）**：
  - ~~门控误触发~~ **已合入 main 并推送（2026-11-18，`origin/main` = `87b2059`）**：密度门 38 帧内 ≥15 说话帧 + 预录 60 帧（1.2 s）。V1 上板：敲击 0 段（0043，嘈杂背景、门槛 18 时测）、词头不切、单字 10 次录到 7 个（0044）。安静房间敲击复测已通过（0045：敲击单独开段 0 次，只有咳嗽开段）；遗留：单字召回没有旧门控基准；583 仍开 1 段；嘈杂背景误开段多。V1 现跑这一版（main.bin `350dc731…`）。
  - 回充采样（`0038_v1_recharge/`）：已停。V1 18:15 起拔着充电器在放电，`full` 拔掉后不清零。继续时：放电到 ~4.0 V → 插回 → `scripts/battery_log.py /dev/ttyACM0 … --slow 60` 后台全程采样、不复位，看 `full` 何时置位。
  - ~~上报 `hw` / `fw_version`~~ **已完成（2026-11-18）**：用户定 `hw`=1、`fw_version` 1.15.35、电量字段同参考设备；App 的 `arm_ota` 回 `denied`，不装原厂包。见上方「阶段 1 原版 App 互通」。
- 待办（2026-11-17 用户确认加入）：**主控降配评估**，详见 `goal.md`。要点：固件不用 PSRAM，SRAM 堆最高约 33%；要片内充电只能选 `SF32LB52x`（520/523/525/527）；523UB6 与 525 只差 PSRAM 容量，改动最小；520U36 无 PSRAM 但片内 1 MB 放不下固件，需核实启动和分区。当前 `weband_hw` 仍按 525，不阻塞打样。
- 待办（2026-11-16 用户提出）：**Weband 没有蜂鸣器**，用户提示只能靠 LED 等方式，各状态的闪法待定，见 `goal.md`。
- **M5 OTA / DFU：已完成（2026-11-13）**，已快进合入 Weband `main` 并推送（`origin/main` = `d3b0d9b`），worktree 与分支已清理；不入库的镜像、升级包与拉回的录音已移到主仓 `evidence/0020_m5_ota/`。板上跑最终版 `main.bin` `d706c012…`（构建 `Nov 13 2026 14:00:44`，经 BLE OTA 装上），开放模式。证据：Weband `evidence/digest.md` 2026-11-13 M5 一节、`evidence/0020_m5_ota/`。
  - 结果：不开窗被拒 5/5；A→B 11/11；断线续传 9/9；C→最终版 8/8（46 s，11.2 KB/s）；OTA 后回读主程序区与最终版逐字节一致；开窗过期被拒 6/6；OTA 后拉录音 17/17；配对跨三次 OTA 保持。
  - 记的 TODO：~~不上报 `hw` / `fw_version`~~（2026-11-18 已做）；离线包不签名，只靠 arm_ota 闸门；板上 rt_tick 慢约 1%；安装器有两条告警（结果正常，未深究）；安装中掉电续装未实测。
- （以下为开工前的调研记录）
  - V1 用 SiFli SDK 自带的 BLE DFU（`dfu_ctrl` / `ble_dfu`，固件字符串），走 SiFli 串口传输服务（App 里服务 UUID `00000000-0000-0000-6473-5f696c666973`）；App 自己实现 SiFli DFU 协议（START_REQ / PACKET / END_RSP）。V1 另加了一道：`dfu install denied: not armed by authenticated peer`，即 M2 的 `arm_ota` 窗口；OTA 前封口录音（`OTA recorder seal`）。
  - 我们的分区已就位：`dfu_flash_code` 0x720000（384 KB）、`dfu_download_region` 0x780000（1152 KB）。SDK 打包工具有 Python 版（`tools/secureboot/imgtoolv37.py`、`dfu_bin_generate37.py`），Linux 可用。M5 不缺硬件；刷坏了可以随时用 UART + sftool 恢复。
  - 待定：① App 按板型从自带资源里挑 OTA 包，并比较版本号；如果认成参考设备的板型，会把原厂固件推给我们（违反"不刷原厂镜像"）。设备上报什么板型 / 版本，需要定。② 签名密钥：开发阶段用 SDK 默认密钥，量产前换自有密钥（记 TODO）。③ 台架 OTA 工具：自己写 bleak 脚本走同一协议（与 `ble_pull_check.py` 同思路）。
- 新工作项「门控误触发」：独立 worktree；方向是较长窗口内的说话帧比例、或排除骤起骤落的帧；用 `evidence/0019_m3_knock/knocks_concat.wav` 与说话录音 950 / 806 在 `rec_sim` 里量化，再上板复测敲击。
- 然后 M5（OTA / DFU）。
- M3 记的 TODO(weband)：文件名 `.ogg` 与 V1 按小时 `.opus`（App 用 月.日.时 取开始时间）；`file_start` 未发 `start_ts` 等字段；`response` 别名；V1 的 VAD 设置持久化。

## 证据索引
- 每步实测记录：`/home/whole/data/reawork/weband/evidence/digest.md`
- M3：`evidence/0012_m3_night`、`m3_morning`、`m3_speech*`（门控调参）、`m3_xfer`（BLE 传输、fs 修复）、`m3_knock`（敲击测试、夜间分时统计）
- 构建日志：`evidence/0002_build_baseline/build_nano_n16r16.log`、`evidence/0007_m1_weband_board/build_weband.log`
- 烧录与回读：M0 `0005_m0_hello_world/flash_hello_world.log` / `0005_m0_hello_world/flash_readback.txt`；M1 `0007_m1_weband_board/flash_weband.log` / `0007_m1_weband_board/flash_readback_weband.txt`
- 串口：`evidence/0005_m0_hello_world/hello_world_boot_1000000.log`、`evidence/0007_m1_weband_board/weband_boot_1000000.log`、`evidence/0006_led_key_test/key_monitor.log`
- 出厂备份：`evidence/0003_factory_backup/factory_flash_first4MB.bin`（不入库）

## 卡点 / 风险
- V1 纸面核实已完成（2026-11-10，Weband `docs/hardware-inventory.md` C5，证据 `evidence/0008_nano_sch/`）：模拟麦可直接接 J1-4/5（板上有 2.2 µF 隔直，MIC_BIAS 1.4–2.8 V）；JDI 14 根信号都已引出；**Nano 芯片不带充电，M4 充电部分在 Nano 上 blocked**。
- IMU：V1 固件反汇编确认不访问 LSM6DS3TR-C（0x6A），不对标（证据 `/home/whole/data/reawork/refdevice-v1/analysis/imu_findings.txt` 及同目录脚本）。
- M3 硬件链路实测通过（2026-11-10）：板上烧了 SDK `audprc` 例程（非 hello_world），3037 模拟麦经 MIC_BIAS 供电能拾音，安静 −51 dBFS、出声 −31…−23 dBFS；导出的 8 kHz WAV 用户试听正常（Weband `evidence/digest.md`）。新增 `scripts/serial_capture.py`、`scripts/pcm_stats.py`，修了 `scripts/build.sh` 传参 bug，均未提交。
- 仍未核实：MIC_BIAS 电压值（没有万用表，只间接确认可用）；V1 电源键是否 PA34；Nano 是否引出 SD 接口引脚。
- V1 开源硬件页（2026-11-13，`oshwhub.com/eda_kqtkoxdx/project_bpeoomns`，CERN-OHL-W-2.0，禁止未授权转载）：器件型号已记进 Weband `docs/hardware-inventory.md` 第 2 节与本目录 `AGENTS.md`；设计文件只读不入库。
- BLE 协议逆向基于 V2 固件，M2 用到时要拿 V1 固件字符串（`/home/whole/data/reawork/refdevice-v1/v1_strings.txt`）复核命令与状态串。
- 参考设备长按电源键的时长没有证据；KEY1 按住 10 s 会硬件复位，长按动作必须在此之前触发。
- 参考设备的应用源码私有，M2 起按逆向协议净室重写；无证据的字段标 `TODO(weband)`。
