#!/bin/bash

# 获取当前日期和时间
current_datetime=$(date +'%Y-%m-%d %H-%M-%S')

# 删除文件
rm -rf ./markdown/.obsidian/plugins/obsidian-spaced-repetition/data.json
rm -rf ./markdown/.obsidian/workspace-mobile.json

# 添加所有更改
git add -A

# Check if additional message was provided as argument
if [ $# -eq 0 ]; then
    # If no argument, use datetime as commit message
    git commit -a -m "backup: $current_datetime"
else
    # If argument provided, use it as commit message
    git commit -a -m "$1"
fi

# 继续 rebase
git rebase --continue

# 拉取最新更改
git pull

# 推送更改
git push

# 输出当前日期和时间
echo "Current date and time: $current_datetime"%
