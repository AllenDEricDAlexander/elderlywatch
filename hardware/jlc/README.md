# 嘉立创EDA 专业版适配工程

目标：把 `../kicad/` 的电气意图在嘉立创EDA专业版里重建成可制造、可贴片的工程，拿到真实封装、LCSC 料号和可下单 BOM。

**当前状态：KiCad → 嘉立创EDA 的迁移已经跑通，`aiot-kicad-import` 里有完整的 9 页原理图、位号、网络名与引脚；缺封装分配与结构整理。**

| 检查 | 结果 |
|---|---|
| `GET http://127.0.0.1:49620/health` | `{"service":"easyeda-bridge","status":"ok","edaConnected":true,"edaWindowCount":1}` |
| 活动窗口 | `3da7d43a-110b-43ab-a994-4173437fe381`（窗口 ID 会随重启变，每次重新取） |
| 客户端 | 嘉立创EDA专业版 v3.2.203，账号 `managerallen`，**在线模式**（`isOnlineMode()=true`） |
| `lib_Device.search()` | 10/10 个已核实 MPN 全部命中，22 个候选，`missing=0` |
| `sys_FileManager.importProjectByProjectFile(file,'KiCad',…)` | **成功** → 工程 `aiot-kicad-import`（uuid `ea905f22c789460e8404c7cb6b73ac04`） |
| 导入保真度 | 01_POWER 27 个部件 / 95 个 netport，02_ESP32 15 个部件，03_MODEM_SIM_RF 22 个部件；U6 引脚 `1-16,EP` 编号与名字齐全；导线带真实网络名（`VBAT`/`+3V3_SYS`/`I2C_SDA`…） |
| 图元写入 | `sch_PrimitiveComponent.create()` + `setState_Designator()` + `delete()` 全部验证通过（详见下方接口矩阵） |

### 接口能力矩阵（v3.2.203 实测，别再走弯路）

| 接口 | 状态 | 实测行为 |
|---|---|---|
| `dmt_Project.createProject()` | 可用（需在线） | 半离线模式下返回 `undefined`；在线能建 |
| `dmt_Board.createBoard()` / `dmt_Pcb.createPcb()` / `dmt_Schematic.createSchematic()` | **写成功但读不到** | 返回 `undefined`，可文档确实进了工程日志 |
| `dmt_Board.getAllBoardsInfo()` / `dmt_Schematic.getAllSchematicsInfo()` / `getAllSchematicPagesInfo()` / `dmt_Pcb.getAllPcbsInfo()` | **对 API 建的工程失效** | 一律返回 `[]`；重开工程也不能重建这棵树 |
| `dmt_Schematic.modifySchematicPageName()` | 失效（同上工程） | 返回 `false`；`getCurrentSchematicPageInfo()` 抛 `typeSymbols` of undefined |
| `sys_FileManager.getProjectFile(name,pw,'epro2')` | **可用** | 返回真 `.epro2`（zip：`project2.json` + `<工程名>.epru` + `IMAGE/`），是查真实文档树的唯一可靠手段 |
| `sys_FileManager.importProjectByProjectFile()` | **可用** | 支持 `'KiCad'`/`'JLCEDA Pro'`；导入出来的工程**文档树接口正常** |
| `dmt_EditorControl.openDocument(pageUuid)` | **可用** | 即使树接口为空也能打开并编辑 |
| `sch_PrimitiveComponent.create/getAll/get/delete/getAllPinsByPrimitiveId` | **可用** | `getAll(type, false)` 只读当前页；引脚对象是**普通属性**（`pinNumber/pinName/x/y/rotation/pinType/noConnected`），不是文档里写的 `getState_*()` |
| `lib_Device.copy()` | 不可用 | 抛 `[object Object]`，重试静默返回 `undefined` |
| — | **替代结论** | 放置系统库器件会**自动**把它的 SYMBOL/FOOTPRINT/DEVICE 复制进工程库，不需要 `lib_Device.copy()` |
| `sys_FileSystem.getProjectsPaths()/getLibrariesPaths()` | 仅离线可用 | 在线模式抛"非半、全离线客户端环境无法调用本接口" |

**遗留问题（我造成的，需要清理）**：`aiot-watch-jlc`（uuid `841edd9ce18749ccbccb95ec18a23a67`）里堆了 API 盲试留下的垃圾文档 —— 2 个板（`Board1`/`Board2`）、4 个 schematic（`Schematic1`/`_1`/`_2`/`_3`）、5 个页（P1×4 + P2）、2 个 PCB，以及测试用的 R0402 器件三件套。`aiot-import-test`（uuid `6897f433a0c44fb48524bf2bf84caa80`）是整工程导入的对照实验件。这些都该删，但删除是云端不可逆操作，等确认。


## 已有产物

- `tools/gen_jlc_part_map.py` → `JLC_PART_MAP.csv`：147 个位号的建库/选型工作表，从 `../kicad/bom/BOM.csv` 与 `../kicad/docs/design_inventory.json` 派生，不是第二份手工清单。`LCSC_ID / JLC_DEVICE_UUID / JLC_SYMBOL / JLC_SYMBOL_UUID / JLC_FOOTPRINT / JLC_FOOTPRINT_UUID / DECISION` 七列由库探测与人工填写，重生成时按位号保留。

| Tier | 行数 | 含义 |
|---|---|---|
| `IC_LCSC_BY_MPN` | 10 | 已核实引脚与 MPN，可直接按型号搜 LCSC（U1/U3–U11） |
| `PASSIVE_BY_VALUE` | 85 | 阻容等通用件，按值+封装搜；其中 8 行仍为待定 |
| `PCB_FEATURE` | 21 | TP1–TP21 是 1.0mm 铜盘，不是采购件 |
| `BLOCKED_VALUE` | 19 | 值本身未定（RF 匹配、天线、模组类） |
| `BLOCKED_PART` | 12 | 器件本体未选型（连接器、开关、ESD、麦克风等） |

`Verified_Pins` 只统计网表里真实编号的引脚：U1=57、U9=20、U6=17、U7=15、U3=14、U11=10、U5=9、U4=8、U10=8、U8=5；U2/U12/U13/J2/J3/MIC1 记 0，与 KiCad 侧"不猜引脚"的结论一致。J1（4 个 pogo 触点）与 SW1/SW2（各 2 个触点）有真实编号，阻断点在机械与焊盘（D11），不在引脚定义。

重新生成：

```bash
python3 hardware/jlc/tools/gen_jlc_part_map.py
```

- `tools/eda_run.py` + `build/lcsc_probe.js`：把代码下发到嘉立创客户端执行的通道。`eda_run.py` 自动扫描 `49620-49629` 找到 Bridge，把 `__PARTS__` 用 `JLC_PART_MAP.csv` 里 10 个已核实 MPN 展开，再 `POST /execute`；Bridge 起着但没有窗口时直接退出并给出可执行的提示，不会静默。`lcsc_probe.js` 只做只读查询（`lib_Device.search`），把每条命中的全部字段原样倒出来，用来确认真实 `uuid/libraryUuid/封装` —— 料号库的 UUID 必须来自客户端返回，不能凭文档或记忆填写。

```bash
python3 hardware/jlc/tools/eda_run.py --dry-run hardware/jlc/build/lcsc_probe.js   # 离线：看将要下发的代码
python3 hardware/jlc/tools/eda_run.py hardware/jlc/build/lcsc_probe.js             # 在线：查 10 个 IC 的库命中
```

校验：payload 离线展开为 10 条 `IC_LCSC_BY_MPN`（U1/U3/U4/U5/U6/U7/U8/U9/U10/U11）、`node --check` 通过；在线执行成功，原始回包存在 `build/lcsc_probe.result.json`（`wanted=10 / found=10 / missing=0 / 22 candidates`）。

- `tools/fill_part_map_from_probe.py`：把上面那份**真实回包**回填进 `JLC_PART_MAP.csv` 的 LCSC 列。只有"厂商料号自身唯一匹配"才填写，匹配不上或一对多的位置留空并在 `DECISION` 里列出候选，绝不代填料号。

```bash
python3 hardware/jlc/tools/fill_part_map_from_probe.py hardware/jlc/build/lcsc_probe.result.json
```

当前回填结果：**8 个已填 / 2 个待选型**。

| 位号 | LCSC | 封装 | 备注 |
|---|---|---|---|
| U3 BMI270 | C2836813 | LGA-14_L3.0-W2.5-P0.50-BR | 与 KiCad 的 LGA14/2.5x3 一致 |
| U4 RV-3028-C7 | C2829066 | DFN-8_L3.2-W1.5-P0.9-BL | 另有 ±1ppm 的 TA-QC/TA-QA 等级件（C3019759/C3304278） |
| U5 MAX17048G+ | C2682616 | TDFN-8_L2.0-W2.0-P0.50-BL-EP1.2 | 库内料号带卷带后缀 `+T10` |
| U6 BQ24074RGTR | C54313 | QFN-16_L3.0-W3.0-P0.50-TL-EP1.7 | 另有 `RGTRG4` 无铅后缀件（C3682481） |
| U7 TPS63070RNMR | C109322 | VQFN-15_L3.0-W2.5-P0.50-BL | 可调输出；`TPS630701RNMR` 是 5V 固定输出，不适用 |
| U8 TLV75518PDBVR | C2877863 | SOT-23-5 | 另有台舟二供 `TPTLV75518PDBVR`（C2940636），封装相同 |
| U9 ES8311 | C962342 | WQFN-20_L3.0-W3.0-P0.40-BL-EP1.7 | 库内封装带 EP1.7，正好对上 D15 的 die-attach 争议 |
| U11 DRV2605LDGSR | C527464 | VSSOP-10_L3.0-W3.0-P0.50-LS4.9-BL | 唯一命中 |

待选型的两个：

- **U1**：`C9900057109` 与 `C7545129` 两个 `ESP32-S3-PICO-1-N8R8` 条目，封装同为 `QFN-56_L7.0-W7.0-P0.40-TL-EP4.0`，前者厂商字段为空。符号 UUID 不同，需按引脚表挑一个。
- **U10**：库里全是带后缀的完整订货号 —— `PAM8302AADCR`=SOP-8（C112137）、`PAM8302AASCR`=MSOP-8（C113367）、`PAM8302AAYCR`=U-DFN3030-8（C4990730）与 PDFN-8（C9900017693）。这正是 D08 未决的封装选择，手表上 3x3 DFN 最省面积。

- `build/*.js`：一次性验证载荷，按用途分（库探测、图元写入验证、工程导出/导入）。这些是**探针不是流水线**，跑通过程见上面的能力矩阵。

- `tools/import_kicad.py`：把 `../kicad/` 打包 → base64 内嵌成载荷 → 交给 Bridge 用客户端自带的 KiCad 导入器重建工程。这是目前唯一值得重复执行的建工程路径。

```bash
python3 hardware/jlc/tools/import_kicad.py --dry-run                        # 离线：打包 + node --check
python3 hardware/jlc/tools/import_kicad.py --project-name aiot-watch-jlc    # 在线：导入成新工程
```

离线校验：91148 字节 zip → 122147 字节载荷，`node --check` 通过。在线实测见 `build/import_kicad.result.json`（工程 uuid `ea905f22c789460e8404c7cb6b73ac04`、10 页树、逐页部件数与三处已知缺口）。

### KiCad 导入结果的具体形态

导入把 KiCad 的每层次页拆成了独立 schematic，与我们的目标结构（1 板 + 1 多页原理图）不同：

| 对象 | uuid | 说明 |
|---|---|---|
| 板 `aiot-watch` | `3e4e5d87c113e90e` | 根页所在板，挂着 PCB `aiot-watch`（`52caa9452ee66dee`） |
| 板 `00_TOP` | `cd81ce9bbcc08faf` | importer 额外造的第二个板，不该存在 |
| schematic × 10 | 见 `dmt_Schematic.getAllSchematicsInfo()` | `aiot-watch`(根) + `00_top`…`08_debug_test`，除 `00_top` 外都不挂在板上 |
| 页 × 10 | 同上 | 名字保留大写：`01_POWER`…`08_DEBUG_TEST` |

导入丢失/未带过来的：所有 `footprint.uuid` 为空（器件进了工程库、命名 `project_U6_BQ24074RGTR` 这种形式，符号与引脚保住了，封装没有）；`03_MODEM_SIM_RF` 上 KiCad 里无引脚定义的 U2/J2 没有作为部件出现。这两点与 `../kicad/` 侧"不猜引脚"的结论一致，不是导入器的错。

## 封装绑定（阶段 1 的收尾）

- `tools/bind_lcsc_footprints.py`：逐页扫 `part` 图元 → 按位号定位器件 uuid → 用 `JLC_PART_MAP.csv` 记录的 LCSC 封装 `lib_Device.modify()` 上去；库内封装 UUID 与映射表不一致就跳过（不猜）。结果 `build/footprint_bind.result.json`。
- `tools/check_footprint_pin_parity.py`：**验收闸门**。不信任接口的 `true`，直接读 `build/aiot-kicad-import.epru` 里器件 META 的 `Symbol`/`Footprint` 指向，把符号引脚号与封装焊盘号对集合。结果 `build/footprint_pin_parity.txt`。

绑定本身成立：8/8 器件的封装已在磁盘上指向工程内副本，副本 `source` 可追到 LCSC 原封装。parity 闸门一度暴露 4 处引脚号↔焊盘号冲突，下面逐条给了事实依据：

| 位号 | 冲突 | 事实（已查数据手册） |
|---|---|---|
| U5 MAX17048 | 符号引脚 `EP` vs 封装中心盘 `9`（0,0，47.2×31.5mil） | MAX17048 引脚表只写 "EP Exposed Pad (TDFN Only). Connect to GND"，**不给编号**（datasheet p6）。所以 `9` 是 LCSC 的编号约定，不是 TI/ADI 规定。功能上 EP 必须接 GND |
| U6 BQ24074 | 符号引脚 `EP`(名 `THERMAL_PAD`) vs 封装中心盘 `17`（POLYGON） | TI 手册明确 "**EXPOSED PAD 17**"，且"internal electrical connection between the exposed thermal pad and the VSS pin"，热盘必须与 pin 8 VSS 同电位。**LCSC 封装是对的，我们的符号编号是偏差方** |
| U9 ES8311 | 封装有盘 `21`（0,0，66.9×66.9mil），符号只有 1–20 | §2 引脚表只到 1–20，§8 封装图把中心盘写作 "EXPOSED DIE ATTACH PAD" **且不给编号**；编号 21 与网络都只来自 §3 典型应用图，图上标的是 **21 = PGND**（不是 AGND），在 10 (AGND) 与 11 (AVDD) 之间的下沿、接到同一条地轨。符号缺这个引脚 → 热盘在 PCB 上无网络。这正是 D15/D16，换工具不会让它消失 |
| U7 TPS63070 | 符号缺 8、13；封装 17 个盘里 `7` 出现 3 次、`12` 出现 3 次 | TI `RNM0015A` 封装图与 LAND PATTERN 是 **15 个独立焊盘 1–15**（VOUT=7,8；VIN=12,13；SM 细节分 "PADS 1-6,14&15" 与 "PADS 7-13"）。LCSC `VQFN-15`（30ffd733…）把 8 并进 7、13 并进 12，另把两条 (±48.2,28.1) 角上 0.25×0.75mm 的焊盘（对应 TI 图上 `2X (0.775)`）也标成 7 和 12。**LCSC 封装偏离 TI 编号**；因 7/8 与 12/13 本就同网络，网络不丢，但引脚-焊盘映射不再一一对应 |

U11/U3/U4/U8 四处 10/14/8/5 引脚与焊盘完全一一对应，无冲突。

**四处冲突已全部处理并通过闸门（2026-09-21）**：

| 位号 | 处置 | 落地方式 |
|---|---|---|
| U5 | 符号 `EP` → `9`（引脚名仍是 EP） | `tools/patch_symbol_pin.py --ref U5 --old EP --new 9 --name EP` |
| U6 | 符号 `EP` → `17`（名 `THERMAL_PAD`） | 同上 `--old EP --new 17 --name THERMAL_PAD` |
| U7 | 工程内封装副本按 TI `RNM0015A` 拆成 1–15 | `tools/patch_footprint_pad.py` |
| U9 | 符号补 `pin 21 = PGND`（Power）＋ 06_AUDIO 补走线与 GND 网络端口 | `tools/patch_u9_die_pad.py`，三步全幂等，已修完再跑一律打印 `ALREADY` |

闸门现状：`build/footprint_pin_parity.txt` → 8/8 器件 `0 missing / 0 extra`，`0 mismatch`，退出码 0。**阶段 1 的封装绑定判定为通过。**

## 网表核对（阶段 1 的第二道闸门）

- `tools/check_sch_netlist_parity.py`：在客户端里把原理图的连接重新解析出来（引脚尖端 → 压在其上的 `WIRE` 的 NET ＋ 压在其上的 `netport` 的 NET），再与 `../kicad/docs/aiot-watch.net.xml` 逐节点比对。结果 `build/sch_netlist_parity.txt`。默认扫九个功能页 ＋ 根页（10 页），**不扫生成的 `10_ALL`**（它重复全部位号，同一次运行里两份副本会互相覆盖）；要单独验合并页用 `--page 10_ALL`，证据写到 `build/sch_netlist_parity_10_ALL.txt`；`--include-merged` 只用于刻意对比。
- `tools/scan_wire_pin_offsets.py`：全工程量化"线端点几乎压着引脚但没精确重合"的偏差。结果 `build/wire_pin_offsets.txt`。

实测（10 页全跑）：KiCad 376 个节点里 **346 个逐引脚对上**；28 个 KiCad `unconnected-(…)` 空脚在嘉立创侧同样为空（没有多余网络误接上去）；3 处为已批准的编号变更（`U5.EP→U5.9`、`U6.EP→U6.17`、新增 `U9.21`，三者都正确落 GND）；`WRONG NET / MISSING / EXTRA / multi-net` 全为 0，退出码 0。未选型位置（U2/U12/U13/J2/J3/MIC1）本来就没有引脚，不参与比对，也不猜。

**已知缺口（按量化结论记录，不修）**：导入器写出的线端点带浮点尾巴 —— 全工程 807 个引脚尖端里 **446 个**与线/网络端点之间有 1.4e-14～3.2e-13 的偏差（另有 479 个引脚尖端自身不是整数）。这不是本轮改动造成的（本轮只动了 pin 21 与一条新线，那条新线端点是精确重合的）。因为嘉立创把网络**作为数据存在每条线和每个 netport 上**（06_AUDIO 页 63/63 条线都带显式 `NET`），上述逐引脚对账全部对上，所以连接在数据层没有丢东西。风险残留在几何层：无法验证嘉立创自己的"原理图→PCB 网表同步"是否用严格相等判连接 —— `sch_Drc.check()` 在 10 页（含未改动页）一律返回 `False`、`sch_Netlist.getNetlist()` 在 bridge 里抛 `TypeError: i is not iterable`，两条都当不了闸门；PCB 侧现有 21 个网络 / 25 个器件，与 `../kicad/pcb/aiot-watch.kicad_pcb` 自身的 25 个 footprint、92 个网络同源，是导入时的旧板壳而非从原理图几何推导，因此对它也不提供证据。定论留到阶段 2 真做网表同步时，拿 PCB 网络与 115 网络 / 376 节点对一次。

补充接口事实（踩过才记下来）：`lib_Symbol.updateDocumentSource()` 与 `sys_FileManager.setDocumentSource()` **只能原地改已有记录的字段值，任何追加记录的写入一律返回 `false`**，所以往符号/页面新增图元必须走 `sch_PrimitivePin.create()` / `sch_PrimitiveWire.create()` / `sch_PrimitiveComponent.create()` ＋ `sch_Document.save()`；坐标系为 API y = −(源文件 y)、API rotation = 源 rotation + 180。

另记：原理图页里的网络**不存储**逐引脚网络字段（`COMPONENT` 只带 `partId` + `Unique ID`，页内无 `PIN` 记录），连接由线/网络端点的 `NET` 属性加端点几何共同决定。所以改符号引脚编号不会断开已有走线，但改完仍要用这两道闸门复验。

数据手册来源：`../kicad/datasheets/`（`TPS63070RNMR.pdf` p39-40、`BQ24074RGTR.pdf` "EXPOSED PAD 17" 段、`MAX17048G+.pdf` p6 引脚表、`ES8311.pdf` Rev5.0 §2 引脚表 / §3 典型应用图 / §8 封装图 —— 后者是第三方镜像且标 Confidential，仅限内部评审使用，对外/认证前必须换成官方版本）。

## 单页总图 `10_ALL`（阶段 1 的合并产物，2026-09-21）

用户要"一张完整的原理图"，选定的方案是**功能分区重排**：保留九个源页里已验证的内部几何，把九个块按信号流搬到同一张页上（不是逐器件重新走线的真·重排，也不是把九块并排贴一起的拼贴 —— 拼贴版本已被否决，块标题横幅已去掉）。

- 生成器：`tools/merge_schematic_pages.py`。`10_ALL`（页 uuid `a7948021787444c3`）是**产物**，不手改；默认整页重建，`--incremental` 续跑，`--pages 05_DISPLAY` 只搬一块（会先把页清空，必须再跑一次全量收尾），`--target 10_NEW` 换一张空白页重建（见下文"僵尸图元"）。设计改动仍然只在九个源页上做，改完重 merge。
- 版面：3×3 功能图（`(row,col)`）—— 上排 `01_POWER / 02_ESP32 / 05_DISPLAY`，中排 `03_MODEM_SIM_RF / 06_AUDIO / 04_IMU_RTC`，下排 `07_HAPTIC_BUTTONS / 08_DEBUG_TEST / 00_TOP`；块间距 `GAP=400` API 单位（远大于对账容差 0.01，块间不可能误连），电路内容包络 7009.8 × 5502.7（x −40…6969.77，y −3964.55…1538.15）。每块只加一个常量偏移，所以"线端点压在引脚尖端上"这层关系原样保留。
- 图面元素（2026-09-21 三段补齐：图框 / 分区线 / 分区备注）：`part=126 port=428 wire=428 text=190 poly=60 flag=2 rect=12`，合计 **1246** 个图元，`sheet=0`。其中 12 个 `rect` 与 49 条 `text` 是生成器画上去的"家具"：
  - **外图框**：2 个矩形（`border` 7509.8 × 6707.7，左上 (-290, 1788.1)，即 API x −290…7219.8 / y −4919.6…1788.1；再内缩一圈 `border-inner`）。**页面不再挂任何库 `sheet` 符号** —— 导入器给每页都塞了 A4 框（1170 × 825），而块里已经画到 A2 量级，这正是"内容排在图纸外面"的根因；库里最大的 A0（4676 × 3304）也装不下，所以图框只能自绘。代价：这一页不再有真实纸张尺寸，PDF/打印分页交给嘉立创自己处理（用户已确认接受）。
  - **九张分区框**：琥珀色 `#FF9900`、线宽 12，几何取自 `build/merge/layout.json` 的 `frame` 字段（比电路包络四周各外扩 `FRAME_PAD`），标题居中在框顶与内容之间。
  - **每区 3 条备注**：27 条 `note:{页}:{序号}`，内容写死在 `BLOCK_META`（`NOTES_MAX=3` 是预算闸门，超标直接报错）；另有左上 banner 1 条、右下标题栏 7 行、左下图例 5 行。标题栏含工程名、页名、版本 `EVT-V1 REVIEW DRAFT`、日期、位号/网络计数、未选型统计，以及 **`发布闸门 HOLD：未布板、不出 Gerber —— NOT FOR FABRICATION`** 和"本页位号已全部排除出 BOM 与 PCB 转交"。
- 搬运的是 1185 个源页图元（`part=126 port=428 wire=428 text=141 poly=60 flag=2`）；源页的 `sheet` 外框与 `00_TOP` 的 `block_symbol`（层次块引用）不搬 —— 合并页是平的，留着等于让设计指向自己。
- 独立验收（不接受生成器自证）：
  - **连通性**：`python3 hardware/jlc/tools/check_sch_netlist_parity.py --page 10_ALL` → **只看这一张页**也拿到与十页全跑同一组数字：346/376 节点对上、28 个 KiCad 空脚仍为空、`U5.EP→U5.9`、`U6.EP→U6.17`、新增 `U9.21` 三处编号变更正确落 GND、`WRONG NET / MISSING / EXTRA / multi-net` 全 0，退出码 0。证据 `build/sch_netlist_parity_10_ALL.txt`；图元计数由 `build/merge/count_all.js`（独立读页）复核，含 0 条零长度残根。
  - **图面**（这一轮新增，因为"图元在模型里"不等于"图上看得见"）：`tools/render_schematic_page.py --format SVG` 走客户端导出，再用 `build/merge/svg_check.py` 离线复核 —— 九个分区框与 `layout.json` 逐一吻合（±1.5，容的是矩形 0.1 单位吸附）、9 个标题 + 27 条备注逐字命中、固定文案（banner/图例/HOLD/BOM 排除/闸门路径/U2 警告）全在、0 条探针或僵尸文字、1975 个内容图元**全部**在图框内、框外文字 0、任何一条装饰文案都不溢出自己所属的分区框。证据 `build/merge/svg_check_final.log`；PNG 导出 `preview_10_ALL.png`（8212×7340，缩到 1700 px 后肉眼复核通过）。

八条实测客户端行为（这一阶段全靠它们才收敛，已同步进项目记忆）：

1. **`create()` 的返回值不可信**：对已经落盘的图元返回失败（线尤其呈严格交替成功/失败），一个被噎住的批次也会在 30 s 超时*之后*写进去。于是整个工具是 verify 环而不是 retry 环 —— 每轮把页面读回来按几何匹配，只对真缺的下发；批次自己的失败清单只记日志，照它重试会在页面上堆出第二个 `U3`，同时毁掉网表和 BOM。
2. **网络端口站在端点上时 `sch_PrimitiveWire.create()` 直接拒绝**：删掉端点上的 3 个端口，被拒了三轮的 5 根线一次全成功。所以重试轮要先降下挡路的端口、画完线再立回去（只动真正挡路的那些）。
3. **重度增删后客户端会假死，而且窗口会自己重启**：所有写操作瞬时返回 falsy、`sch_Document.save()` 返回 `false`，而读接口和 `openDocument()` 一切正常。这是窗口级状态（弹窗/只读），API 侧救不回来；实测会自行恢复，恢复后先把探针图元删干净再继续。本轮（重建 `10_ALL` 期间）窗口**断线并重连 4 次**，每次 `windowId` 都变，所以长批量任务必须能从中断点续跑（`--incremental` + 小 `--chunk`），并且**管道尾部的 `exit=0` 不算通过** —— 有一次 parity 闸门崩在断线上，而 `| tail` 让 shell 报了 0。
4. **网络名会被大小写归一**：源页 `power_PWR_FLAG` 在合并页读回是 `POWER_PWR_FLAG`。跨页搬运后拿网络名做等值断言要先归一大小写，否则会把改名当缺陷。
5. **客户端会持有"API 打不到的僵尸图元"**：`f0706db0ae88edcc` 那一页上，3 个探针文字被删掉、`save()` 成功，但客户端**导出**里仍留着 38 条探针文字（`getAll()` 不列、`get([id])` 回 0 行、`delete([ids])` 回 `false`）。唯一解法是新页面重建 —— 这就是 `--target` 的用途：本次以 `10_NEW` 重建 → 全闸门通过 → 删掉旧页 → `modifySchematicPageName()` 改名回 `10_ALL`，页 uuid 因此从 `f0706db0ae88edcc` 变成 `a7948021787444c3`。**任何"这张页干净"的结论都必须来自导出，不能来自 `getAll()`。**
6. **`getCurrentRenderedAreaImage()` 不能当证据**：它是**陈旧位图** —— 新建三个图元并 `save()` 之后，截帧 md5 与之前**逐字节相同**，`zoomToAllPrimitives()` / `zoomToRegion()` 也换不来新画面。所以这一轮之前所有"渲染出来的样子"的证据一律作废。可用的渲染路径是 `sch_ManufactureData.getExportDocumentFile(name, 'SVG'|'PNG'|'PDF', {theme:'Black on White', lineWidth:'Default'}, 'Current Schematic Page')` → `File`，它确实按页取内容（拿 05_DISPLAY 与根页对照验证过）；该接口标了"DEPRECATED since EDA v4.1"，在 v3.2.203 上正常。
7. **导出图的坐标映射**：SVG x = API x，**SVG y = −API y**；每个导出图元带 `id="<primitiveId>"`，所以能拿 SVG 反查到具体图元。矩形角点会**吸附到 0.1 单位网格**（几何断言容差必须 ≥0.1，别把吸附当偏差）。文字 `alignMode` 读回与创建参数不一致（建 1 读 5、建 4 读 14，原因未查明；导出画面里的居中视觉正确，暂时按"只信导出"处置）。
8. **页面名在存储层被小写归一**（`modifySchematicPageName('…','10_ALL')` 返回 `true`、`getSchematicPageInfo` 回 `name:"10_all"`），且 `getAllSchematicPagesInfo()` 在改名后短时间内是**旧快照**。按名字找页会误判"改名失败"，一律用 uuid。

**位号重复的处置（2026-09-21 决定：`10_ALL` 当纯阅读视图）**：`10_ALL` 与九个源页持有同一批位号的两份副本，而嘉立创的"原理图→PCB 网表同步 / BOM 导出"是按整个原理图文档汇总的。所以合并页上**全部 126 个器件都带 `addIntoBom=false` + `addIntoPcb=false`**，从数据层排除在 BOM 与 PCB 转交之外；源页才是网表与 BOM 的唯一来源。生成器把这条写死在 `items()` 里（不是照抄源页标志），并让 `attrs()` 读回这两个标志 —— 所以重建或 `--incremental` 都会自动补回排除标志，漏掉就报 `attr-repair`，不会静默回归。

实测证据：`--incremental` 首轮识别出 126 处属性不符并全部修好，之后 `repair=0`；**换页重建后的当前这一张（`a7948021787444c3`）在 1246 图元的收尾轮里 `attr-repair=0`**，并逐页读回复核：`10_ALL` = 126 个器件 / 126 个排除，九个源页 0 个排除、126 个位号各只归属一页且无跨页重复（`build/merge/run_viewonly.log`、`build/merge/resume_10_NEW.log`、`build/merge/bom_flags_by_page.js`）。

还没被证明的部分（诚实记录）：这两个旗标是否真的被嘉立创的"转到PCB"逻辑尊重，只能等阶段 2 真做一次同步才能验；API 侧 `pcb_Document.importChanges()` 只回 boolean、无预览，跑一次就会改 PCB，所以现在不动。届时的判据是：同步后 PCB 上的器件必须正好是源页那 126 个位号、网络数从现有 21 涨到原理图侧的 115；如果器件变成 252 个实例，就说明旗标不被尊重，那时改成"同步前删掉 `10_ALL`、同步后再 merge 回来"。

顺带订正一条接口事实（先前记错过一次，本轮实测推翻）：`dmt_EditorControl.openDocument()` **只认裸页 uuid**，传 `uuid@工程uuid` 会返回 `undefined` 并且**不切换文档** —— 之后所有 `zoomTo*` / 截帧 / `sch_Primitive*.getAll()` 都还在操作"上一个活动画布"，看起来像接口在说谎（本轮"家具画不上去"的假象有一半来自这里）。传页面**名字**同样不报错、也不切换。`getAll(componentType, true)` 的第二参数是"读整个原理图所有页"。合并/校验/导出脚本一律用裸 uuid，并且先检查 `openDocument()` 的返回值非空。


**工程名与清理**：`dmt_Project` 只有 `createProject/getAllProjectsUuid/getCurrentProjectInfo/getProjectInfo/moveProjectToFolder/openProject` —— **既没有删除也没有重命名接口**。云端 Personal 空间实测就三个工程（`aiot-kicad-import` `ea905f22…`＝正在用的、`aiot-import-test` `6897f433…`＝对照件、`aiot-watch-jlc` `841edd9c…`＝API 盲试留下的垃圾），清理只能在客户端 UI 里手工删。绑定做在 `aiot-kicad-import` 上，若按原名重建，`bind_lcsc_footprints.py` + parity 闸门可整段重跑，成本是一个脚本周期。



## 工具链

通过三个官方 skill 驱动，安装位置在用户级 skills 目录：

| skill | 用途 |
|---|---|
| `easyeda-api-skill` | 提供 `eda.*` API 文档、源文件格式说明，以及连接客户端的 WebSocket Bridge |
| `extension-dev-skill` | 按当前安装 SDK 的类型定义查 API，写插件时用 |
| `easyeda-enhanced-schematic-skill` | 在活文档里批量取器件、画模块框、放元件、生成网络标签并连线 |

Bridge 工作方式：本机起 Node 服务监听 `49620-49629`，嘉立创EDA 里装 `run-api-gateway` 插件并开启外部交互，插件自动扫描端口握手，之后 AI 通过 `POST /execute` 向客户端下发代码。

## 输入来源

- `../kicad/docs/aiot-watch.net.xml`：原生网表，器件与网络连接的事实来源。
- `../kicad/docs/PIN_MAPPING.csv`、`NET_MATRIX.md`、`POWER_TREE.md`：引脚分配与电源树。
- `../kicad/bom/BOM.csv`：设计清单，其中 10 个 IC 已带核实过的 MPN。
- `../kicad/docs/TODO_DATASHEET_VERIFY.md`：D01–D16 阻断项，决定哪些部分还不能在嘉立创侧画实。

## 已知不能凭空解决的部分

嘉立创库能给出封装和料号，但给不出我们缺的设计输入。以下在 `jlc/` 里同样是阻断项，不能因为换了工具就当作已定：

- D01 SIM8230C 引脚表与 land pattern（模块本体）
- D02 LCD 模组与 FPC 连接器
- D03 Nano SIM 卡座
- D05 麦克风料号与声孔
- D09 电池包 NTC 与 2.5A 脉冲条件
- D10 板厂介质层叠
- D11 表壳结构
- D12 UART/PCM 电平转换器选型与三路 modem 控制的 GPIO 缺口
- D13 ESD/TVS、RF 接头、电感磁珠与全部 R/C/L 的完整料号
- D15/D16 音频 die-attach 编号与模拟地策略

## 阶段

0. 工具链 + 器件清单 + 下发通道 + LCSC 库探测 —— **已完成**。
1. 迁移出可读写的嘉立创工程 —— **已完成**（KiCad 导入，10 页原理图 + 位号 + 网络 + 引脚齐全，`build/import_kicad.result.json`）。
2. 给导入的器件逐个绑上真实 LCSC 封装（`lib_Device.modify` / `setState_SupplierId`），并把 8 个已核实 IC 与 KiCad 侧位号一一对上；未选型位置按 D01–D16 留空，不猜封装。 —— **通过（2026-09-21）**：绑定 8/8 落盘，parity 闸门查出的 U5/U6 `EP` 编号约定冲突、U7 封装合并焊盘、U9 缺 die-attach 引脚（＝D15）四处已全部处置，`build/footprint_pin_parity.txt` 为 8/8 `0 missing / 0 extra`、退出码 0；网表侧另加 `tools/check_sch_netlist_parity.py`，346/346 对上、0 缺陷。详见「封装绑定」与「网表核对」两节。
3. 整理结构：合并成 1 板 + 1 多页原理图，删掉 importer 造的多余板子。**原理图侧已定稿读法**：`10_ALL` 单页总图＝纯阅读视图（器件全部排除出 BOM/转PCB，见上一节），网表与 BOM 只从九个源页出；剩下的是 importer 冗余板子（`Board1`/`Board2`）的清理。
4. 布局：先做 placement 与机械核对，再按用户确认的顺序布线。
5. 对齐嘉立创工艺：板层、阻抗、拼板、坐标与 BOM 导出。

每阶段都要有独立验证，不接受"工具能打开"当作设计正确。
