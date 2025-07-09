#!/usr/bin/env python3
"""
添加 Git Submodule 的脚本
使用方法: python add_sub.py <repo_url>
功能: 将指定的仓库添加为 submodule 到 crates/reponame 路径下
"""

import sys
import os
import subprocess
import re
from urllib.parse import urlparse
from pathlib import Path


def extract_repo_name(repo_url):
    """从仓库URL中提取仓库名称"""
    # 移除.git后缀
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]

    # 提取最后一部分作为仓库名
    repo_name = repo_url.split("/")[-1]

    # 验证仓库名是否合法（只包含字母数字、下划线、连字符）
    if not re.match(r"^[a-zA-Z0-9_-]+$", repo_name):
        raise ValueError(f"无效的仓库名称: {repo_name}")

    return repo_name


def run_command(cmd, cwd=None):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {cmd}")
        print(f"错误信息: {e.stderr}")
        raise


def check_git_repo():
    """检查当前目录是否为git仓库"""
    try:
        run_command("git rev-parse --git-dir")
        return True
    except subprocess.CalledProcessError:
        return False


def add_submodule(repo_url, submodule_path):
    """添加submodule"""
    print(f"正在添加 submodule...")
    print(f"仓库URL: {repo_url}")
    print(f"路径: {submodule_path}")

    # 检查路径是否已存在
    if os.path.exists(submodule_path):
        raise FileExistsError(f"路径已存在: {submodule_path}")

    # 添加submodule
    cmd = f"git submodule add {repo_url} {submodule_path}"
    run_command(cmd)

    print(f"成功添加 submodule: {submodule_path}")


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python add_sub.py <repo_url>")
        print("示例: python add_sub.py https://github.com/example/my-driver.git")
        sys.exit(1)

    repo_url = sys.argv[1]

    # 验证URL格式
    try:
        parsed_url = urlparse(repo_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("无效的URL格式")
    except Exception as e:
        print(f"URL格式错误: {e}")
        sys.exit(1)

    try:
        # 检查是否在git仓库中
        if not check_git_repo():
            print("错误: 当前目录不是git仓库")
            sys.exit(1)

        # 提取仓库名称
        repo_name = extract_repo_name(repo_url)
        print(f"检测到仓库名称: {repo_name}")

        # 构建submodule路径
        submodule_path = f"crates/{repo_name}"

        # 确保crates目录存在
        crates_dir = "crates"
        if not os.path.exists(crates_dir):
            print(f"创建目录: {crates_dir}")
            os.makedirs(crates_dir)

        # 添加submodule
        add_submodule(repo_url, submodule_path)

        print("\n操作完成!")
        print(f"Submodule 已添加到: {submodule_path}")
        print("\n后续操作:")
        print("1. 使用 'git submodule init' 初始化submodule")
        print("2. 使用 'git submodule update' 更新submodule")
        print(
            "3. 或者使用 'git submodule update --init --recursive' 一次性完成初始化和更新"
        )

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
