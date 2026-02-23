# Buff Parser Implementation Summary

## 已完成的功能

### 1. 核心解析器 (`src/parser/buff/`)

- ✅ **types.ts** - TypeScript 类型定义
  - `BuffTreeNode` - 树节点结构
  - `FieldSchema` - 字段 schema 定义
  - `ParseConfig` - 解析配置（literal/fn/expr/schema）
  - `MappingCache` - 缓存结构

- ✅ **loader.ts** - YML 配置加载器
  - `loadMappings()` - 加载所有映射文件
  - `getActionFieldSchema()` - 按优先级获取字段 schema
  - `getActionSubSchema()` - 加载复杂字段子 schema
  - `getBaseFieldSchema()` - 获取基础字段 schema
  - `getEventSchema()` - 获取事件 schema

- ✅ **parser.ts** - 核心解析逻辑
  - `parseBuffToTree()` - 解析单个 buff
  - `parseBuffsToTree()` - 批量解析 buff
  - `parseAction()` - 解析 action
  - `parseEvent()` - 解析 event
  - 支持 literal/fn/expr/schema 四种解析类型
  - 递归处理 buff → events → actions → fields

- ✅ **examples.ts** - 使用示例
  - `loadAllBuffs()` - 加载所有 buff
  - `loadSingleBuff()` - 加载单个 buff
  - `searchBuffs()` - 搜索功能
  - `getNodeMetadata()` - 获取元数据
  - `findNodeByPath()` - 路径导航
  - `flattenTree()` - 展平树结构
  - `getLeafNodes()` - 获取叶子节点

- ✅ **README.md** - 完整文档

### 2. 构建脚本

- ✅ **scripts/generate_mapping_yml.ts**
  - 动态识别复杂字段（96个）
  - 生成 index.yml
  - 生成 event_list.yml（带 parse.type: literal）
  - 生成 action_keys.yml
  - 生成 action_keys_template.yml（boolean/number 自动添加 default.parse）
  - 生成 action_nodes.yml
  - 生成 actions/*.yml（1009个文件）
  - 生成 action_subschema/*.yml（96个文件）

- ✅ **scripts/copy_mappings.ts**
  - 自动复制 mappings 到 public 目录

- ✅ **package.json scripts**
  - `generate:mappings` - 生成映射文件
  - `copy:mappings` - 复制到 public
  - `build:mappings` - 完整构建流程

### 3. 测试组件

- ✅ **src/components/BuffParserTest.vue**
  - 加载并显示前10个 buff
  - 搜索功能
  - 点击节点查看详情
  - 虚拟滚动支持

## 优先级规则

解析器严格按照以下优先级查找字段配置：

1. **action_subschema/{fieldName}.yml** = **actions/action_{ActionType}.yml** (最高)
2. **action_keys.yml**
3. **action_keys_template.yml** = **action_nodes.yml** = **event_list.yml** = **index.yml** (最低)

## 解析类型支持

### 1. Literal（字面值）
```yaml
parse:
  type: literal
  return: true
```
直接返回配置的值。

### 2. Function（函数调用）
```yaml
parse:
  type: fn
  name: parseBoolean
  args:
    - $input
    - $ctx
```
调用指定函数，传入参数。

### 3. Expression（表达式）
```yaml
parse:
  type: expr
  return: $input * 2
```
计算表达式结果。

### 4. Schema（引用）
```yaml
schema: action_subschema/_targetOptions.yml
```
引用其他 schema 文件获取详细配置。

## 数据流程

```
buff_template_data.json
    ↓
parseBuffToTree()
    ↓
遍历基础字段 → 使用 index.yml
    ↓
遍历 eventToActions → 使用 event_list.yml
    ↓
遍历 actions → 使用 action_nodes.yml
    ↓
遍历 action 字段 → 优先级查找:
    1. actions/action_{type}.yml
    2. action_keys.yml
    3. action_keys_template.yml
    ↓
如果有 schema 引用 → 加载 action_subschema/*.yml
    ↓
构建 BuffTreeNode 树结构
    ↓
返回给 n-tree 组件显示
```

## 文件统计

- **基础配置**: 6 个文件（index, event_list, action_keys, action_keys_template, action_nodes）
- **Action schemas**: 1009 个文件（每个 action 类型一个）
- **Subschemas**: 96 个文件（复杂字段）
- **总计**: 1111 个 YML 文件

## 使用方法

### 基础用法
```typescript
import { parseBuffsToTree } from '@/parser/buff';

const buffData = await fetch('/gamedata/battle/buff_template_data.json')
  .then(r => r.json());
const trees = await parseBuffsToTree(buffData);
```

### Vue 组件
```vue
<script setup>
import { ref, onMounted } from 'vue';
import { NTree } from 'naive-ui';
import { parseBuffsToTree } from '@/parser/buff';

const treeData = ref([]);

onMounted(async () => {
  const buffData = await fetch('/gamedata/battle/buff_template_data.json')
    .then(r => r.json());
  treeData.value = await parseBuffsToTree(buffData);
});
</script>

<template>
  <n-tree :data="treeData" virtual-scroll />
</template>
```

## 性能特性

- ✅ 懒加载：仅在需要时加载 action/subschema 文件
- ✅ 缓存：使用 Map 缓存已加载的 schema
- ✅ 虚拟滚动：支持大量节点的高效渲染
- ✅ 类型安全：完整的 TypeScript 类型定义

## 下一步优化建议

1. **性能优化**
   - 实现 worker 线程解析
   - 添加分页加载
   - 优化大对象序列化

2. **功能增强**
   - 添加节点编辑功能
   - 支持导出为其他格式
   - 添加可视化比较功能

3. **用户体验**
   - 添加加载进度条
   - 支持键盘导航
   - 添加节点高亮

## 依赖

- `yaml` - YAML 解析
- `naive-ui` - UI 组件
- `vue` - 框架
- `typescript` - 类型系统
