# Bena Protractor

## 配置

安装: Node.js, Rust, pnpm

## 脚本
```shell
pnpm run copy-json

```
## 使用

```shell
pnpm install
pnpm dev
pnpm tauri dev
pnpm tauri icon
git submodule add https://github.com/Kengxxiao/ArknightsGameData.git include/stb
git submodule update --init --recursive
```

## 编辑
根据git日志观察有哪些新增, 移除`generated`, 实现`fn`, 填充`public/buff/...`

可以直接构建`parseNode{type}`, 作为最高优先级处理