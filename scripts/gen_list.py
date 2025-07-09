#!/usr/bin/env python3
"""
脚本用于遍历 .gitmodules 文件，生成 crates 表格并更新 README.md
"""

import os
import re
import toml
import requests
from pathlib import Path


def parse_gitmodules(gitmodules_path):
    """解析 .gitmodules 文件"""
    submodules = []

    with open(gitmodules_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配子模块块
    pattern = (
        r'\[submodule "([^"]+)"\]\s*\n\s*path\s*=\s*([^\n]+)\s*\n\s*url\s*=\s*([^\n]+)'
    )
    matches = re.findall(pattern, content)

    for match in matches:
        submodule_name = match[0]
        path = match[1].strip()
        url = match[2].strip()
        submodules.append({"name": submodule_name, "path": path, "url": url})

    return submodules


def check_crate_exists_on_cratesio(crate_name):
    """检查 crate 是否存在于 crates.io"""
    try:
        url = f"https://crates.io/api/v1/crates/{crate_name}"
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def get_crate_info(crate_path):
    """从 Cargo.toml 文件获取 crate 信息"""
    # 查找主要的 Cargo.toml 文件
    cargo_toml_paths = []

    # 如果是 workspace，查找具体的 crate
    workspace_cargo = os.path.join(crate_path, "Cargo.toml")
    if os.path.exists(workspace_cargo):
        with open(workspace_cargo, "r", encoding="utf-8") as f:
            try:
                cargo_data = toml.load(f)
                if "workspace" in cargo_data:
                    # 这是一个 workspace，查找主要的 crate
                    crate_name = os.path.basename(crate_path)
                    main_crate_path = os.path.join(crate_path, crate_name, "Cargo.toml")
                    if os.path.exists(main_crate_path):
                        cargo_toml_paths.append(main_crate_path)
                    else:
                        # 查找其他可能的主 crate
                        for item in os.listdir(crate_path):
                            item_path = os.path.join(crate_path, item)
                            if (
                                os.path.isdir(item_path)
                                and item != "interface"
                                and item != "examples"
                            ):
                                potential_cargo = os.path.join(item_path, "Cargo.toml")
                                if os.path.exists(potential_cargo):
                                    cargo_toml_paths.append(potential_cargo)
                                    break
                else:
                    cargo_toml_paths.append(workspace_cargo)
            except Exception:
                cargo_toml_paths.append(workspace_cargo)

    if not cargo_toml_paths:
        return None

    # 读取第一个找到的 Cargo.toml
    try:
        with open(cargo_toml_paths[0], "r", encoding="utf-8") as f:
            cargo_data = toml.load(f)

        package = cargo_data.get("package", {})
        name = package.get("name", "")
        description = package.get("description", "")
        version = package.get("version", "")
        repository = package.get("repository", "")

        return {
            "name": name,
            "description": description,
            "version": version,
            "repository": repository,
        }
    except Exception as e:
        print(f"Error reading {cargo_toml_paths[0]}: {e}")
        return None


def generate_crates_table(submodules, base_path):
    """生成 crates 表格"""
    table_lines = [
        "| Crate | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[crates.io](crates.io)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Documentation | Description |",
        "|----|:--:|:--:|----|",
    ]

    for submodule in submodules:
        crate_path = os.path.join(base_path, submodule["path"])
        crate_info = get_crate_info(crate_path)

        if crate_info and crate_info["name"]:
            name = crate_info["name"]
            description = crate_info["description"]

            # 检查是否发布到 crates.io
            print(f"Checking {name} on crates.io...")
            is_on_cratesio = check_crate_exists_on_cratesio(name)

            if is_on_cratesio:
                # 在 crates.io 上
                crates_io_link = f"[![Crates.io](https://img.shields.io/crates/v/{name}.svg)](https://crates.io/crates/{name})"
                docs_link = f"[![Documentation](https://docs.rs/{name}/badge.svg)](https://docs.rs/{name})"
            else:
                # 不在 crates.io 上
                crates_io_link = "N/A"
                # 使用 GitHub Pages 文档链接
                repo_name = submodule["url"].split("/")[-1].replace(".git", "")
                doc_url = f"https://drivercraft.github.io/{repo_name}"
                docs_link = f"[![Docs.rs](https://img.shields.io/badge/docs-pages-green)]({doc_url})"

            # 添加表格行
            table_lines.append(
                f"| [{name}]({submodule['url']}) | {crates_io_link} | {docs_link} | {description} |"
            )

    return table_lines


def update_readme(readme_path, crates_table):
    """更新 README.md 文件中的 Crates 部分"""
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 查找 ## Crates 部分
    pattern = r"(## Crates\s*\n)(.*?)(?=\n##|\n#|$)"

    # 生成新的内容
    new_section = "## Crates\n\n" + "\n".join(crates_table) + "\n"

    if re.search(pattern, content, re.DOTALL):
        # 替换现有的 Crates 部分
        new_content = re.sub(pattern, new_section, content, flags=re.DOTALL)
    else:
        # 如果没有找到 Crates 部分，在文件末尾添加
        new_content = content.rstrip() + "\n\n" + new_section

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    gitmodules_path = project_root / ".gitmodules"
    readme_path = project_root / "README.md"

    if not gitmodules_path.exists():
        print(f"Error: .gitmodules file not found at {gitmodules_path}")
        return

    if not readme_path.exists():
        print(f"Error: README.md file not found at {readme_path}")
        return

    # 解析 .gitmodules
    print("Parsing .gitmodules...")
    submodules = parse_gitmodules(gitmodules_path)
    print(f"Found {len(submodules)} submodules")

    # 生成 crates 表格
    print("Generating crates table...")
    crates_table = generate_crates_table(submodules, project_root)

    # 更新 README.md
    print("Updating README.md...")
    update_readme(readme_path, crates_table)

    print("Done! README.md has been updated.")


if __name__ == "__main__":
    main()
