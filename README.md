# zhenxun_plugin_niuniu
真寻群内小游戏插件-牛牛大作战(误

# 本插件无需数据库！(因为我不会bushi)

## 使用方法
下载压缩包，解压并放入`extensive_plugin`文件夹或其他自定义文件夹中

## 指令
|指令|功能描述|
|---|---|
|注册牛子|注册你的牛子|
|jj [@user]|与注册牛子的人进行击剑，对战结果影响牛子长度|
|我的牛子|查看自己牛子长度|
|牛子长度排行|查看本群正数牛子长度排行|
|牛子深度排行|查看本群负数牛子深度排行|
|打胶|对自己的牛子进行操作，结果随机|

## 依赖

正常情况真寻的虚拟环境里附带此模块
```powershell
pip install ujson
```

## 说明
群友长度数据位于插件文件夹中的`data/long.json`中
