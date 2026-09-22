# AIoT 老人智能手表 — 硬件目录

同一块板子目前维护两套 EDA 表达：

| 目录 | 工具 | 状态 |
|---|---|---|
| `kicad/` | KiCad 10.0.6 | 进行中的评审草稿。原理图 126 器件已网表化，PCB 只有 21 个测试焊盘和 4 个安装孔，105 个器件未绑封装。不可打样。 |
| `jlc/` | 嘉立创EDA 专业版 | 目标适配版。用嘉立创/LCSC 元件库重建原理图与 PCB，取得真实封装、料号和可下单 BOM。已由 `kicad/` 经客户端 KiCad 导入器迁移出 10 页原理图（位号、网络、引脚齐全，缺封装分配）；工程目前在嘉立创云端 Personal 空间，尚未落成本地文件。 |

两套不是自动同步的副本。`kicad/` 是电气意图与设计约束的权威来源（网表、电源树、引脚分配、评审结论）；`jlc/` 是面向嘉立创制造与贴片装配的落地实现。任何电气决策先在 `kicad/` 记录，再在 `jlc/` 实现，避免两边各说一套。

## 为什么做 jlc 版本

`kicad/` 的审核长期卡在缺封装和缺料号：36 个唯一 BOM 行里只有 10 个带 MPN，D06/D07 的推荐 land pattern 一直拿不到官方 CAD。嘉立创EDA 自带 LCSC 库与封装，正好补这块，同时直接对齐嘉立创的板厂工艺和贴片坐标要求。

## 查看方式

- KiCad：打开 `kicad/aiot-watch.kicad_pro`，原理图入口 `kicad/aiot-watch.kicad_sch`。
- 嘉立创EDA：打开 `jlc/` 下的工程文件（生成后）。
- 评审证据统一在 `kicad/docs/`，其中 `ERC_DRC_REPORT.md`、`KICAD_HAPPY_REVIEW.md`、`TODO_DATASHEET_VERIFY.md` 是入口。

## 复现检查

仓库根目录：

```bash
python3 hardware/kicad/tools/validate_draft.py   # 仅结构不变量
python3 hardware/kicad/tools/check_kicad.py      # 原生 ERC / DRC / parity / 网表
```

`check_kicad.py` 保留 `--exit-code-violations`，当前退出码为 5，表示仍有违规，不允许改成忽略。
