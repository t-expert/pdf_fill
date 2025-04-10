# Sandbox CLI 工具

## 安装

```bash
# 进入 sandbox 目录下的虚拟环境
cd sandbox && pipenv shell
pipenv install --dev
pipenv run sbx --help
```

### 可用命令
在 sandbox 目录下执行

```bash
# update
pipenv run sbx update --dev/--test/--prod/--prod-backup
```
```bash
# rollback
pipenv run sbx rollback --dev/--test/--prod/--prod-backup
```
```bash
# spawn
pipenv run sbx spawn --dev/--test/--prod/--prod-backup --long
```
```bash
# connect
pipenv run sbx connect --sid "sandbox id"
```
```bash
# logs
pipenv run sbx logs --sid "sandbox id"
```


