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

### INPUT_BLOCK
- type: String
- required: 否
- default: true
- 未通过检查时是否显示为失败(返回码非0)，可选值：true，false。

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

### 质量门禁参数(当<=设定的指标值时，判定为通过):

代码检查指标参数:
- `INPUT_INCR_FATAL`: 选填，新增问题量(级别:致命), 推荐值: 0
- `INPUT_INCR_ERROR`: 选填，新增问题量(级别:致命+错误), 推荐值: 0
- `INPUT_INCR_WARNING`: 选填，新增问题量(级别:致命+错误+警告), 推荐值: 0
- `INPUT_INCR_INFO`: 选填，新增问题量(级别:致命+错误+警告+提示), 推荐值: 0
- `INPUT_TOTAL_FATAL`: 选填，存量问题量(级别:致命), 推荐值: 0
- `INPUT_TOTAL_ERROR`: 选填，存量问题量(级别:致命+错误), 推荐值: 0
- `INPUT_TOTAL_WARNING`: 选填，存量问题量(级别:致命+错误+警告), 推荐值: 0
- `INPUT_TOTAL_INFO`: 选填，存量问题量(级别:致命+错误+警告+提示), 推荐值: 0

代码度量指标参数:
- `INPUT_WORSE_CC_FILE_NUM`: 选填，圈复杂度恶化文件数,需要分析方案中开启了圈复杂度,填写一个整数, 推荐值: 0
> 某文件圈复杂度恶化,表示该文件超标圈复杂度函数个数或超标圈复杂度总和，相比上一扫描版本（MR场景与目标分支对比）增大。该指标计算恶化的文件个数，如果小于等于指标值，则通过。
- `INPUT_DUPLICATE_RATE`: 选填，代码重复率,需要分析方案中开启了重复代码检查,填写一个整数,单位:百分比(%),推荐值:3


## Outputs

查看日志，会展示结果链接，可跳转到server页面查看结果。

同时会在当前工作空间下输出结果文件`codedog_report.json`,该文件结构如下:

```
{
    "status":"success|failure|error",
    "url":"结果链接",
    "text":"通过|不通过|异常",
    "description":"结果详细描述",
    "scan_report":{
	    "lintscan":"代码检查结果",
	    "cyclomaticcomplexityscan":"圈复杂度结果",
	    "duplicatescan":"重复代码结果",
	    "clocscan":"代码统计结果"
    },
    "metrics": {                 # 质量门禁数据
	    "incr_fatal": {
	      "value": 0         # 本次扫描新增(致命)问题量
	    },
	    "incr_error": {      
	      "value": 0         # 本次扫描新增(致命+错误)问题量
	    },
	    "incr_warning": {
	      "value": 0         # 本次扫描新增(致命+错误+警告)问题量       
	    },
	    "incr_info": {
	      "value": 0         # 本次扫描新增所有(致命+错误+警告+提示)问题量  
	    },
	    "total_fatal": {
	      "value": 0         # 当前分支(致命)问题量
	    },
	    "total_error": {     
	      "value": 9         # 当前分支(致命+错误)问题量
	    },
	    "total_warning": {
	      "value": 9         # 当前分支(致命+错误+警告)问题量
	    },
	    "total_info": {
	      "value": 9         # 当前分支(致命+错误+警告+提示)问题量
	    },
	    "worse_cc_file_num": {
	      "value": 0         # 圈复杂度恶化文件数
	    },
	    "over_cc_sum": {
	      "value": 36        # 超标圈复杂度总数
	    },
	    "cc_func_average": {
	      "value": 2.947     # 代码平均圈复杂度
	    },
	    "over_cc_func_count": {
	      "value": 10        # 圈复杂度超标方法数
	    },
	    "diff_over_cc_func_count": {
	      "value": 0         # 变更圈复杂度超标方法数
	    },
	    "over_cc_func_average": {
	      "value": 8.6       # 超标方法平均圈复杂度   
	    },
	    "duplicate_rate": {
	      "value": 44.3      # 代码重复率
	    }
    }
}
```


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