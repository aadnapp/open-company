---
inclusion: manual
---

# 值班任务:晚间进度盘点与经验总结

在对话中输入 `#task-daily-patrol` 触发。原定每晚 21:00 运行,Kiro 无定时调度,改为手动触发。

执行约定:
- 工作目录:`companies/open-source-software/projects/daily-patrol`
- 原任务引用的 `goal.md`、`handoff.md`、`.munk/now.md`、`goals/index.md`、`.opencode/skills/`、`toolchains/tabs.json` 是 Munk 运行时生成的文件,本仓库不一定存在。只在原路径各检查一次;不存在就记为「无数据」,不要全仓搜索、不要去别的目录找,也不要编造进度。
- 不需要读取其它产品仓库的源码;能读到什么就汇总什么,全部缺失就直接写「无数据」收工。
- `products/open-compare` 只是参考模板,不运营:不对账、不列入督办清单,也不从它的 AGENTS.md 提炼"当日经验"。
- 进度以各产品目录下的 `goal.md`(当前目标与结案条件)和 `handoff.md`(现状、等待项、证据索引)为准。`.munk/now.md` 与 `goals/index.md` 是 Munk 运行时文件,Kiro 下不维护,缺失不算卡点。
- 判断"长期无进展"时看 `handoff.md` 的「最近更新」日期;超过 3 天未更新的产品列入督办清单。
- 各角色当天做了什么,先读 `~/.local/state/open-company/digests/<当天日期>/*.md`(每个角色一份,含预检次数、出错时段、Agent 运行与结论),不要再自己去翻原始日志。
- 对公司级 `AGENTS.md` 的修改只作为候选写进 digest,由用户确认后再改。
- `digest.md` 当普通文件写在工作目录下。

#[[file:companies/open-source-software/projects/daily-patrol/tasks/daily-patrol.md]]
