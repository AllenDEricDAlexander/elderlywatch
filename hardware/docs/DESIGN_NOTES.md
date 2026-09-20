# 设计记录

本次在原空 `hardware/` 下新增评审草稿，未动 `.idea/` 和其他软件目录。保留用户“不猜引脚、不立即布线、先评审”的要求。

1. 用九页层次结构承载功能分区。跨页已实现电路使用明确的 global net labels。顶层是模块与网络关系说明；没有增加软件式抽象或外部依赖。
2. 已知引脚采用完整自定义符号，不借用相似芯片。未知模块用无引脚图框和网络标签，不能冒充已接通的器件。全部 NC/Reserved 的最终核对仍受 D01 等资料限制。
3. BQ24074/TPS63070/BMI270/RTC/MAX17048/TLV75518/DRV2605L 与 ESP32 为**电气草稿**。引脚表已参照官方资料，但封装、供电时序、热/信号完整性、工艺等未全部审定，未宣称可制造。
4. 两个实体按键各自直连 MCU，外部上拉、1k 串阻与 100nF 滤波。实际开关封装未知，符号端子 1/2 是逻辑触点而非已核对的量产开关 pin map。
5. GPIO 分配避免内部 PSRAM 和启动配置脚。三路 modem 控制不足是待决事项，未偷偷共享 UART/按键或添加 GPIO 扩展器。U12 仅为尚未选型的电平转换功能占位。
6. I2C 只有一对公共上拉；RTC_INT/BAT_ALERT 等开漏信号另有自身上拉。所有电压域仍需结合掉电和上电顺序复核。
7. RTC 当前用于系统有电时的离线计时，不宣称主电池拔除后仍保持时间；备用脚依官方建议经 10k 接地。
8. BOM 包括尚未实现的 D4/D5 USB ESD、U13 背光、FB1、eSIM 等占位；它与当前可导出的原理图 BOM 不同。不能将其标为“完整已选型 BOM”。
9. 初步板宽限制和 SIM 卡座冲突已公开，不通过缩小假封装、挪动射频引脚或放宽 clearance 隐藏问题。
10. 并未实现天线/RF/蜂窝启动时序/电话音频桥接/跌倒算法/OTA 等功能验证。这些目标不因画出模块图而成为已验收功能。

## 停止边界

不生成 Gerber、钻孔或坐标文件，不自动启动 KiCad GUI，不打开浏览器，不安装 KiCad，不运行硬件、服务或外部集成。不能把自定义结构检查当成 ERC/DRC。没有 blanket waiver 或 ignored error。

## 来源

- 官方器件文档：SOURCES.json。
- 文件结构参考 [KiCad schematic format](https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/) 与 [PCB format](https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/)。文件格式目标为 KiCad 8；现已由KiCad 10.0.6原生加载、导出并运行检查，结果见ERC_DRC_REPORT.md。

## kicad-happy辅助审核

已按用户提供仓库安装相关技能，版本commit a6bba1add1e18b89e3aa0824b9769ed1d9d79174。本次实际运行和误报处理见KICAD_HAPPY_REVIEW.md。原生资料与技能输出均未当作可制造承诺。
