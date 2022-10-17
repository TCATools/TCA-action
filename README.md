# TCA-action

This action uses [Tencent Cloud Code Analysis (TCA for short, code-named CodeDog inside the company early)](https://github.com/Tencent/CodeAnalysis) to analyze code.

- 说明：当前为快速扫描模式，只在日志中展示结果。更多功能（比如问题提交到自己搭建的server、问题追踪、体验更多分析规则包）可参考[完整模式用法](doc/use-server.md)

## Inputs

通过环境变量输入参数，支持以下环境变量：

### INPUT_BLOCK
- type: String
- required: 否
- default: true
- 未通过检查时是否显示为失败(返回码非0)，可选值：true，false。

### INPUT_LABEL
- type: String
- required: 否
- default: open_source_check
- 规则标签，可选值: open_source_check(开源合规检查), safety(安全检查), sensitive(敏感信息检查)。默认值：open_source_check。

### INPUT_FROM_FILE
- type: String
- required: 否
- 填写一个相对工作区的文件路径，文件内容：待扫描的文件列表，一行一个文件，采用相对路径格式。
如果不指定，则扫描整个工作区的代码文件。

### INPUT_WHITE_PATHS
- type: String
- required: 否
- 指定相对工作区的扫描路径正则表达式(白名单)，多个用英文逗号分割。

### INPUT_IGNORE_PATHS
- type: String
- required: 否
- 指定相对工作区屏蔽路径正则表达式(黑名单)，多个用英文逗号分割。

## Outputs

output result in logs.



## Example usage
在github仓库的工作流目录（如果`.github/workflows`目录不存在，先创建）下增加以下`tca.yml`文件，并提交即可。每次代码提交操作，都将触发一次TCA代码分析。

### 1. 增量分析示例

- 分析本次push提交的变更代码文件。通过git命令获取到变更文件列表，写入到`changed.txt`，传递给`from_file`参数。
- `ignore_paths`设置为过滤掉`.git/`和`.github/workflows/`目录。
- 注意：Checkout拉代码步骤，需要设置参数`fetch-depth: 2`，拉取至少2层深度的git记录，否则无法获取到变更文件。

`.github/workflows/tca.yml`
```
name: TCA

on: [push]

jobs:
  TCA:
    name: Tencent Cloud Code Analysis
    runs-on: ubuntu-latest
    env:
      INPUT_BLOCK: true
      INPUT_LABEL: open_source_check
      INPUT_IGNORE_PATHS: .git/.*,.github/workflows/.*
      INPUT_FROM_FILE: changed.txt
    container:
      image: bensonhome/tca-action
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          fetch-depth: 2
      - name: get git diff files
        run: git config --global core.quotepath false && git diff ${{ github.sha }} ${{ github.sha }}^ --name-only > changed.txt  && cat changed.txt
      - name: Tencent Cloud Code Analysis
        run: /tca_action/entrypoint.sh
```

### 2.全量分析示例

- 不传递`from_file`参数，默认扫描工作空间下的全量代码文件。
- `ignore_paths`设置为过滤掉`.git/`和`.github/workflows/`目录。

`.github/workflows/tca.yml`
```
name: TCA

on: [push]

jobs:
  TCA:
    name: Tencent Cloud Code Analysis
    runs-on: ubuntu-latest
    env:
      INPUT_BLOCK: true
      INPUT_LABEL: open_source_check
      INPUT_IGNORE_PATHS: .git/.*,.github/workflows/.*
    container:
      image: bensonhome/tca-action
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      - name: Tencent Cloud Code Analysis
        run: /tca_action/entrypoint.sh
```