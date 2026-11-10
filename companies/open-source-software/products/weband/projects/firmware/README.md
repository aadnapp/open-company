# SF32LB52 固件复刻
本项目负责 `Weband` 固件从零基线到功能对齐的研发与真机验收。

## 值班任务与分工
1. **`firmware-build-flash.md`（按需）**：在目标板上完成 SDK 构建、烧录和串口验证，产出可复现的证据。M0 的验收入口，之后每次换板或升级 SDK 都要重跑。
2. **`firmware-port.md`（按需）**：按 brief 指定的里程碑（M1–M5）移植一项功能，先单测后上板。

## 连接串口
开发板 SF32LB52-DevKit-Nano（`sf32lb52-nano_n16r16`）经 USB Type-C 接入，控制台为 `uart1`，波特率 1000000：
```bash
python3 -m serial.tools.miniterm --rts 0 --dtr 0 --eol CR /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 1000000
```
- 连上后按回车出现 `msh />` 提示符；输入 `help` 列出命令。退出按 `Ctrl+]`。
- 连上时板子通常已经启动完，看不到启动日志。板上**没有独立的复位键**（只有 KEY1 / KEY2），要看启动日志可以在 shell 里输入 `reboot`，或在 miniterm 里按两次 `Ctrl+T` `Ctrl+R`（第一次拉住 RTS 按住复位，第二次松开，芯片随即重启）。长按 KEY1 10 秒也会硬件复位。
- 依赖 pyserial 3.5（`python3 -m pip install --user pyserial==3.5`）。
- 用 `--eol CR`，不要用 `CRLF`：`CRLF` 会让一次回车发成 `\r\n`，shell 当成两次回车，出现 `msh />msh />`。
- 命令一条一条打，不要一次粘贴多行；多行粘贴时字符会丢，命令被截断。脚本发命令时要写后回读确认，打开串口后的第一条命令偶尔不生效。
- **不要用 `screen`**：本板 RTS 接复位，`screen` 会把芯片一直按在复位里，表现为回车没反应。直接关掉终端窗口也不会退出 `screen`，它会在后台继续占着串口，用 `screen -ls` 查看、`screen -S <id> -X quit` 退出。
- 同一时间只能有一个程序占用串口，烧录前先退出终端。

## 运行边界
- 两条任务都需要真实开发板，手动触发，不挂 cron。
- 参考资料目录 `/home/whole/data/reawork/refdevice` 只读；不要在里面改文件，也不要把里面的原厂二进制、APK、反编译代码复制进产品仓库。
- 烧录会改写设备 Flash，执行前必须先向用户确认端口与板型。
