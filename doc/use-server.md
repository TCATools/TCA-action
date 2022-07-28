# TCA-action 完整模式

说明:
- 当前为完整模式，需要先[搭建TCA Server](https://github.com/Tencent/CodeAnalysis) ，并配置对应的server ip和token。
- 可以在server上创建分析方案，体验更多分析规则包。
- 结果会上报到server，可在页面查看，并可追踪扫描结果。

## Inputs

通过环境变量输入参数，支持以下环境变量：

### INPUT_QUICK_SCAN
- type: String
- required: 是
- default: false
- 设置为false，才能开启完整模式。

### INPUT_SERVER_IP
- type: String
- required: 是
- 已经搭建好的TCA Server IP。

### INPUT_ORG_SID
- type: String
- required: 是
- 团队编号。

### INPUT_TEAM_NAME
- type: String
- required: 是
- 项目名称。

### INPUT_SCHEME_ID
- type: String
- required: 否
- 分析方案ID，不指定会使用默认分析方案。

### INPUT_TOTAL_SCAN
- type: String
- required: 否
- default: false
- 是否全量分析，默认为增量分析。

### INPUT_LANGUAGE
- type: String
- required: 否
- 可选，扫描语言，多个可以用英文逗号分隔，不填会自动识别语言。

### INPUT_COMPARE_BRANCH
- type: String
- required: 否
- 可选，对比分支，过滤掉从对比分支引入的历史代码问题，常用于MR场景，一般设置为MR目标分支。


## Outputs

查看日志，会展示结果链接，可跳转到server页面查看结果。


## Example usage
在github仓库的工作流目录（如果`.github/workflows`目录不存在，先创建）下增加以下`tca.yml`文件，并提交即可。每次代码提交操作，都将触发一次TCA代码分析。

`.github/workflows/tca.yml`

### 1. push触发配置示例
```
name: TCA

on: [push]

jobs:
  TCA:
    name: Tencent Cloud Code Analysis
    runs-on: ubuntu-latest
    env:
      INPUT_QUICK_SCAN: false
      INPUT_SERVER_IP: 按实际填写
      INPUT_TOKEN: 按实际填写
      INPUT_ORG_SID: 按实际填写
      INPUT_TEAM_NAME: 按实际填写
      INPUT_SCHEME_ID: 按实际填写
      INPUT_TOTAL_SCAN: false
    container:
      image: bensonhome/tca-action
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      - name: Tencent Cloud Code Analysis
        run: /tca_action/entrypoint.sh
```

### 2. pull_request触发配置示例

- 需要配置`INPUT_COMPARE_BARNCH`为`$GITHUB_BASE_REF`，也就是将对比分支设置为pull_request的目标分支。
- checkout拉代码步骤，需要配置`ref`参数，指定拉取pull_request的源分支代码。（否则默认会进行预合入操作，产生临时版本号）。
- checkout参数`fetch-depth`设置为`0`，需要拉取所有分支，否则无法进行pull_request源分支与目标分支间的对比。

```
name: TCA

on:
  pull_request:
    branches:
      - main

jobs:
  TCA:
    name: Tencent Cloud Code Analysis
    runs-on: ubuntu-latest
    env:
      INPUT_QUICK_SCAN: false
      INPUT_SERVER_IP: 按实际填写
      INPUT_TOKEN: 按实际填写
      INPUT_ORG_SID: 按实际填写
      INPUT_TEAM_NAME: 按实际填写
      INPUT_SCHEME_ID: 按实际填写
      INPUT_TOTAL_SCAN: false
      INPUT_COMPARE_BRANCH: ${{ github.event.pull_request.base.ref }}
    container:
      image: bensonhome/tca-action
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          ref: ${{ github.event.pull_request.head.ref }}
          fetch-depth: 0
      - name: Tencent Cloud Code Analysis
        run: /tca_action/entrypoint.sh
```