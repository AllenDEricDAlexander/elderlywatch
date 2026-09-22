# 封装状态

`TestPad_1mm.kicad_mod` 已定义：项目自身设计的 1mm 圆形测试焊盘，开阻焊、不印锡膏，Pin 1 是唯一触点。单焊盘无需伪造额外 pin-1 marker；为避免覆盖触点不画焊盘内丝印。仍需治具接触/ENIG/探针间距审核。

四个1.4mm NPTH现在使用NPTH_1.4mm.kicad_mod统一库定义，由用户指定机械尺寸生成。没有任何 SIM8230C/ESP32 或其他 IC 的猜测焊盘。外形矩形在 Dwgs.User/Cmts.User，不是 footprint，也不是 courtyard。

取得推荐 land pattern 后逐项核对 pin 1、top/bottom view、EP、Fab、courtyard、silkscreen、paste、mask 和 assembly outline，再发布 IC 封装；不能直接将产品本体尺寸当作焊盘尺寸。
