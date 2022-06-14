# TCA-action

This action uses [Tencent Cloud Code Analysis (TCA for short, code-named CodeDog inside the company early)](https://github.com/Tencent/CodeAnalysis) to analyze code.

## Inputs

### block
- type: Boolean
- required: 否
- default: true
- 未通过检查时是否抛出错误阻塞流程。

### label
- type: String
- required: 否
- default: open-standard
- 规则标签，可选值: open-standard(开源合规检查), open-source(对外开源检查)。默认值：open-standard。

### from_file
- type: String
- required: 否
- 填写一个相对工作区的文件路径，文件内容：待扫描的文件列表，一行一个文件，采用相对路径格式。
如果不指定，则扫描整个工作区的代码文件。

### white_paths
- type: String
- required: 否
- 指定相对工作区的扫描路径正则表达式(白名单)，多个用英文逗号分割。

### ignore_paths
- type: String
- required: 否
- 指定相对工作区屏蔽路径正则表达式(黑名单)，多个用英文逗号分割。

## Outputs

output result in logs.



## Example usage
```
on: [push]

jobs:
  Code Analysis:
    runs-on: ubuntu-latest
    name: code analysis
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      - name: Tencent Cloud Code Analysis
        uses: TCATools/TCA-action@main
        with:
          block: true
          label: open-standard
```
