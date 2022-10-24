# Firmware Update Checker

一个 OPPO 系 TWS 更新固件获取的简单实现。  
模拟欢律对指定设备 ID 进行固件更新检查，若检测到有新固件，将会自动下载，并将更新记录写入 `devices_id.json` 中。  

## 用法

```
python update_checker.py devices_id
```

初次使用，可以不指定参数，将会自动抓取并显示最新的设备 ID.
