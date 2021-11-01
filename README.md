# Enco X Downgrade Server

OPPO Enco X / W51 等 OPPO 系 TWS 降级代理服务器。

首先需要使用 mt 管理器或其他反编译工具制作降级版欢律，查找字符串 `https://smarthome.iot.oppomobile.com/v1/earphone/firmwareInfo` ，修改为 `http://smarthome.iot.oppomobile.com/v1/earphone/firmwareInfo` ，即将 `https` 改为 `http` ，并重新打包安装。

放置 `firmware.bin` 至程序同目录，运行程序后在手机上配置代理，使用降级版欢律刷入固件更新。

仅在 Enco X 上测试通过，虽已对其他型号做了支持，但不保证一定可用。
