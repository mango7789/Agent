<h2 style="text-align: center;">简历匹配</h2>

### 数据表

- 参考 `template/` 下文件，现在使用 mongodb 作为数据库，备份在 `~/data/mongodb/backup` 下
- 主要包含
  - 简历表 (`resume.json`)
  - 岗位表 (`job.json`)
  - 打分表 (`score.json`)
  - 对话记录表 (`chat.json`)
  - 爬虫任务表 (`task.json`)
- 需要将各部分的输入输出与模板表对齐

### 运行项目
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```