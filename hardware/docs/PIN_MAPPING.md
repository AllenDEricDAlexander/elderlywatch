# 引脚映射与证据边界

所有已绘制引脚列于 PIN_MAPPING.csv。EP 是手册的焊盘名称；尚未与实际封装编号绑定，不能擅自改为 9/17。未知 IC 用无引脚图框保留接口，绝非可布线符号。NC 只用于已确认的不使用引脚；TBD 不用 NC 掩盖。

ESP32 普通 GPIO 分配如下。MODEM 控制三路尚缺 GPIO，触摸未分配。GPIO0/3/45/46 保持启动用途；GPIO33–37、SPICS1 不用于外设。USB19/20、调试43/44独立保留。

| GPIO | Net |
|---|---|
| 1 | BTN_SOS |
| 2 | BTN_AI |
| 4 | I2C_SDA |
| 5 | I2C_SCL |
| 6 | IMU_INT1 |
| 7 | IMU_INT2 |
| 8 | RTC_INT |
| 9 | BAT_ALERT |
| 10 | LCD_CS |
| 11 | LCD_MOSI |
| 12 | LCD_SCLK |
| 13 | LCD_DC |
| 14 | I2S0_BCLK |
| 15 | I2S0_LRCK |
| 16 | I2S0_DOUT |
| 17 | I2S0_DIN |
| 18 | AUDIO_MCLK |
| 21 | MCU_MODEM_TX |
| 38 | MCU_MODEM_RX |
| 39 | MCU_PCM_CLK |
| 40 | MCU_PCM_SYNC |
| 41 | MCU_PCM_DIN |
| 42 | MCU_PCM_DOUT |
| 47 | LCD_BL |
| 48 | LCD_RST |

MODEM_TX/RX 是 modem 视角；MCU_MODEM_TX 应经翻译连接 MODEM_RX，反向同理。I2S0_DIN/DOUT 是 ESP32 视角。PCM 主从与方向待手册确认。

## 测试点位号与治具名称

为避免 KiCad annotation 错误，采用 TP1–TP21 标准位号。网名和原有功能名称未改变。

| Reference | Fixture name | Net |
|---|---|---|
| TP1 | TP_5V | VBUS_5V |
| TP2 | TP_VBAT | VBAT |
| TP3 | TP_VBAT_MODEM | VBAT_MODEM |
| TP4 | TP_3V3 | +3V3_SYS |
| TP5 | TP_1V8 | +1V8 |
| TP6 | TP_GND | GND |
| TP7 | TP_UART_TX | UART0_TX |
| TP8 | TP_UART_RX | UART0_RX |
| TP9 | TP_I2C_SCL | I2C_SCL |
| TP10 | TP_I2C_SDA | I2C_SDA |
| TP11 | TP_MODEM_TX | MODEM_TX |
| TP12 | TP_MODEM_RX | MODEM_RX |
| TP13 | TP_MODEM_PWRKEY | MODEM_PWRKEY |
| TP14 | TP_ESP_USB_DP | ESP_USB_DP |
| TP15 | TP_ESP_USB_DM | ESP_USB_DM |
| TP16 | TP_MODEM_USB_DP | MODEM_USB_DP |
| TP17 | TP_MODEM_USB_DM | MODEM_USB_DM |
| TP18 | TP_RESET | ESP_EN |
| TP19 | TP_BOOT | ESP_BOOT |
| TP20 | TP_CHG_STATUS | CHG_STATUS |
| TP21 | TP_PGOOD | PGOOD |
