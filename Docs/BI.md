# Yonghong BI 项目文档

## 一、项目概览

| 属性 | 值 |
|------|-----|
| GroupId | `g5` |
| ArtifactId | `main` |
| Version | `develop` |
| JDK | 1.8 |
| 构建工具 | Maven |
| 最终产物 | `bi.war`（部署到 Tomcat） |
| 代码风格 | Checkstyle（`checkstyle.xml`） |
| 测试框架 | JUnit 4 / Spock（Groovy）/ PowerMock |
| 代码覆盖率 | JaCoCo |

## 二、项目结构

```
bi/
├── pom.xml                  # 父 POM，聚合所有模块
├── checkstyle.xml           # 代码风格检查规则
├── .gitlab-ci.yml           # GitLab CI（引用外部 review 流水线）
├── .gitignore
├── support/                 # 支撑模块（pom 聚合）
│   ├── audit/               #   审计
│   ├── bc/                  #   基础通用
│   ├── bihome/              #   BI Home
│   ├── dep/                 #   依赖管理
│   ├── tool/                #   工具类
│   └── localization/        #   国际化
├── biz/                     # 业务模块（pom 聚合）
│   ├── act/                 #   行为/活动
│   ├── aqry/                #   高级查询
│   ├── chart/               #   图表
│   ├── cmd/                 #   命令
│   ├── console/             #   控制台
│   ├── db/                  #   数据库
│   ├── flow/                #   流程
│   ├── form/                #   表单
│   ├── ga/                  #   通用分析
│   ├── gab/                 #   通用分析基础
│   ├── jdbc/                #   JDBC 连接
│   ├── mapdata/             #   地图数据
│   ├── ml/                  #   机器学习
│   ├── plugin/              #   插件
│   ├── pubasset/            #   公共资产
│   ├── py/                  #   Python 集成
│   ├── r/                   #   R 集成
│   ├── recycler/            #   回收站
│   ├── report/              #   报表
│   ├── sched/               #   调度
│   ├── script/              #   脚本
│   └── secure/              #   安全
├── access/                  # 访问/接口模块（pom 聚合）
│   ├── api/                 #   API 接口
│   ├── sv/                  #   服务
│   ├── wf/                  #   工作流（包含 Activiti 重写类）
│   └── fabric/              #   Fabric 集成
├── front/                   # 前端模块（pom 聚合，需 Profile 激活）
│   └── h5/                  #   H5 前端（3 个 Profile：h5 / h5_perf / h5_security）
├── website/                 # Web 入口模块（war，最终部署包）
├── yonghongapi/             # 对外开放 API（com.yonghong group）
├── mixup/                   # 可选模块（默认不参与构建）
└── gitHooks/                # Git 钩子脚本
```

## 三、子模块详细说明

### 3.1 website（war 模块）

- **packaging**: `war`
- **finalName**: `bi`（最终产物 `bi.war`）
- **作用**: Web 入口，聚合所有模块依赖，部署到 Tomcat
- **运行测试需设置**: `-Dbi.home=<BI_HOME路径>`
- **特殊处理**: `truezip-maven-plugin` 在 package 阶段自动剔除 `workflow-2.6.8.4.jar` 中与 `access/wf` 模块重写的同名类，防止类冲突

### 3.2 front/h5（H5 前端模块）

- **构建方式**: `maven-antrun-plugin` 调用 npm 脚本
- **前端子项目**（位于 `src/main/resources/g5/` 下）:

| 目录 | 说明 | 安装命令 | 构建命令 |
|------|------|---------|---------|
| `h5/` | 主 BI 前端 | `npm run smart-ci` | `npm run build-p-all` |
| `newReport/` | 报表模块 | `npm run smart-ci` | `npm run release` |
| `flow/` | 工作流 | `npm ci` | - |

- **三个构建 Profile**:

| Profile | Ant Target | npm Script |
|---------|------------|------------|
| `h5` | `h5_build` | `build-p-all` |
| `h5_perf` | `h5_build_perf` | `build-p-all-perf` |
| `h5_security` | `h5_build_security` | `build-p-all-security` |

### 3.3 yonghongapi

- **groupId**: `com.yonghong`
- **作用**: 对外提供 BI 平台 API
- **依赖**: `g5:sv`（服务模块）

### 3.4 mixup（可选模块）

- **默认不参与构建**（在主 pom.xml 的 `<modules>` 中被注释）
- 包含 PDF/图表混排相关功能（依赖 Batik、POI 等）
- 若需启用，取消主 POM 中的注释，或通过 `-Pmixup` Profile 激活

## 四、打包流程

### 4.1 标准构建命令

```bash
# 完整构建（跳过测试）
mvn clean package -DskipTests=true

# 完整构建并运行测试
mvn clean package -DskipTests=false -Dbi.home=<BI_HOME路径>

# 激活 H5 前端一起构建（默认不激活）
mvn clean package -DskipTests=true -Ph5
```

### 4.2 构建产物

执行 `mvn clean package` 后，各模块产出：

| 模块 | 产物 |
|------|------|
| website | `website/target/bi.war` |
| yonghongapi | `yonghongapi/target/yonghongapi-develop.jar` |
| biz 各子模块 | `biz/<子模块>/target/<子模块>-develop.jar` |
| support 各子模块 | `support/<子模块>/target/<子模块>-develop.jar` |
| access 各子模块 | `access/<子模块>/target/<子模块>-develop.jar` |

### 4.3 Assembly 分包（`assemble` Profile）

在 `website` 模块中，`assemble` Profile 使用 `maven-assembly-plugin` 将依赖拆分为多个独立 jar 包：

```bash
mvn clean package -Passemble
```

| 产物 | Assembly 描述文件 | 内容说明 |
|------|------------------|---------|
| `product.jar` | `assembly-product.xml` | 所有 `g5:*` 业务代码（排除 tool、mapdata、APICopilotProc） |
| `thirds.jar` | `assembly-thirds.xml` | 所有第三方依赖（排除 g5、com.yonghong、测试框架等） |
| `api.jar` | `assembly-api.xml` | `com.yonghong:*` API 代码 |
| `base.jar` | `assembly-earth.xml` | 地图基础数据（不含百度/高德数据） |
| `baidu.jar` | `assembly-baidu.xml` | 百度地图数据 |
| `autoNavi.jar` | `assembly-autoNavi.xml` | 高德地图数据 |
| `chatAPI.jar` | `assembly-chat-copilot.xml` | Chat/Copilot API（仅提取 APICopilotProc 类） |

### 4.4 Security 分包（`assemble-security` Profile）

```bash
mvn clean package -Passemble-security
```

| 产物 | 说明 |
|------|------|
| `product.jar` | 排除 wf、WhiteBoxEnvInitCore、DefMD5UserPWDVerifier |
| `thirds.jar` | 排除 yh 组的 Spring 相关 jar（spring-aop/beans/context 等）和 workflow |
| `api.jar` / `base.jar` / `baidu.jar` / `autoNavi.jar` | 同 assemble Profile |

### 4.5 代码混淆

在 `assemble` 和 `assemble-security` Profile 中，`proguard-maven-plugin` 会对 `product.jar` 进行混淆：
- 输入: `product.jar`
- 输出: `product_confuse.jar`
- 混淆规则: [website/proguard-keep-rules.pro](website/proguard-keep-rules.pro)
- 字典: [website/special_dict.txt](website/special_dict.txt)
- 映射: [website/mapping.txt](website/mapping.txt)

## 五、CI/CD

### 5.1 GitLab CI

`.gitlab-ci.yml` 引用外部项目 `Project/ci-test` 的 `/review.yml` 流水线模板。

### 5.2 GitHub

`.github/` 目录下为 Java 升级工具链（`java-upgrade` / `modernize`），非 CI 流水线配置。

## 六、技术栈摘要

| 层级 | 技术 |
|------|------|
| 后端框架 | Spring 5.3.39（定制 yh group）、Spring Data JPA 2.5.12 |
| Web 容器 | Tomcat（Servlet 4.0.1） |
| 工作流引擎 | Activiti（定制版 workflow-2.6.8.4） |
| 数据库 | Derby（测试）/ MySQL 5.1.49（测试） |
| 前端构建 | npm + Ant（maven-antrun-plugin） |
| 代码混淆 | ProGuard 6.2.2 |
| 测试 | JUnit 4.12 / Spock 1.3 / PowerMock 1.6.5 |
| 代码覆盖率 | JaCoCo 0.8.2 |
| 代码风格 | Checkstyle 2.15 |
| Maven 仓库 | 内网 Nexus（192.168.1.131:8781） |
