本 README 说明 mappings（YAML）与原始 buff JSON 之间的约定、扩展点与使用方法。

目标：
- 让 mappings 对前端解析器与编辑器友好、可读并便于扩展；
- 说明各个 YML 文件的语义、解析流程与常见扩展场景；
- 指出生成/同步脚本以及如何添加自定义解析函数。

目录（快速导航）
- 概览（文件角色）
- 关键文件说明（index.yml / event_list.yml / action_nodes.yml / action_keys_template.yml / action_keys.yml / action_subschema / actions）
- 解析类型（literal / fn / expr / schema）
- 扩展指南（新增字段 / 新增 action / 添加 fn）
- 生成与部署（如何生成并复制 buff/mappings）
- 示例（最小示例与常见模式）

概览（文件角色）
- index.yml：入口，定义全局字段类型、Record 映射关系（例如 eventToActions 指向事件->动作映射来源）。
- event_list.yml：事件枚举（作为 record 的 key 列表来源）。
- action_nodes.yml：基础节点元数据（描述、icon 等），为动作渲染提供默认信息。
- action_keys_template.yml：所有可能字段的模板定义（类型、默认 parse、schema 引用），用于覆盖与继承。
- action_keys.yml：字段在动作体中可能的取值（用于渲染下拉、提示、匹配）。
- action_subschema/*.yml：针对复杂字段（object/array）按字段生成的子 schema，可包含每个 action 的 values 与解析器映射。
- actions/*.yml：每个 action 的特定字段定义，优先级高于 action_keys_template 与 action_keys（用于动作级别覆盖）。

解析类型简介
- literal：直接返回固定值或布尔/字符串/数字，用于枚举项。示例：

```yml
parse:
    type: literal
    return: true
```

- fn：调用运行时函数以处理输入（见 fn registry），常用于复杂 object/array 的友好显示或计算。示例：

```yml
parse:
    type: fn
    name: parseTemplateKey
    args:
    - $input
    - $ctx
```

- expr：表达式或小型模板（保留扩展点，当前解析器可按需实现）。
- schema：通过 `schema: action_subschema/_xxx.yml` 将字段指向更详细的子 schema 解析。

如何组合 Record（例：eventToActions）
- 在 `index.yml` 中可声明一个 `type: record`，并用 `key.file` 与 `value.file` 指向对应的 YML 文件或通配符：

```yml
eventToActions:
    type: record
    key:
    file: event_list.yml
    value:
    file:
        - action_keys.yml
        - actions/*.yml
```

这表示：Record 的 key 来自 `event_list.yml`，value 的 schema 从 `action_keys.yml` 与匹配的 `actions/*.yml` 合并获得（后者优先）。

action_subschema 样例（复杂字段）
- 每个复杂字段文件以 `field` 与 `actions` 映射描述不同 action 的取值及解析器：

```yml
field: _additionalBuff
type: object
description: additional Buff
actions:
    SummonEnemiesFollowMyRouteWithBuff:
    type: array
    values:
        -
        value: "[]"
        display: true
        parse:
            type: fn
            name: parseadditionalBuff
            args:
            - $input
            - $ctx
```

扩展指南（常见操作）
- 添加/修改字段映射：更新 `action_keys_template.yml`（模板）或 `action_keys.yml`（字段值枚举），必要时为复杂字段添加 `action_subschema/_xxx.yml`。
- 新增 action 特定定义：在 `actions/` 下新增 `YourActionName.yml`，指定 `actionType` 与 `fields`。该文件会覆盖通用模板。
- 添加自定义解析函数：在解析器的 fn 注册表（parser 层）加入对应函数名（例如 `parseadditionalBuff`），函数签名接收 `$input` 与 `$ctx` 并返回要在 UI 上展示或在树节点中存放的值。
