import os
import subprocess
import sys
from tree_sitter import Language
from typing import List
from os import PathLike, fspath, path
from tempfile import TemporaryDirectory
from platform import system

repos = []
with open("repos.txt", "r") as file:
    for line in file:
        url, commit = line.split()
        clone_directory = os.path.join("vendor", url.rstrip("/").split("/")[-1])
        repos.append((url, commit, clone_directory))

# During the build, this script runs several times, and only needs to download
# repositories on first time.
if os.path.isdir("vendor") and len(os.listdir("vendor")) == len(repos):
    print(f"{sys.argv[0]}: Language repositories have been cloned already.")
else:
    os.makedirs("vendor", exist_ok=True)
    for url, commit, clone_directory in repos:
        print()
        print(f"{sys.argv[0]}: Cloning: {url} (commit {commit}) --> {clone_directory}")
        print()

        if os.path.exists(clone_directory):
            continue

        # https://serverfault.com/a/713065
        os.mkdir(clone_directory)
        subprocess.check_call(["git", "init"], cwd=clone_directory)
        subprocess.check_call(["git", "remote", "add", "origin", url], cwd=clone_directory)
        subprocess.check_call(["git", "fetch", "--depth=1", "origin", commit], cwd=clone_directory)
        subprocess.check_call(["git", "checkout", commit], cwd=clone_directory)

print()

if sys.platform == "win32":
    languages_filename = "tree_sitter_languages\\languages.dll"
else:
    languages_filename = "tree_sitter_languages/languages.so"

def build_library(output_path: str, repo_paths: List[str]) -> bool:
    """
    Build a dynamic library at the given path, based on the parser
    repositories at the given paths.

    Returns `True` if the dynamic library was compiled and `False` if
    the library already existed and was modified more recently than
    any of the source files.
    """
    output_mtime = path.getmtime(output_path) if path.exists(output_path) else 0

    if not repo_paths:
        raise ValueError("Must provide at least one language folder")

    cpp = False
    source_paths = []
    for repo_path in repo_paths:
        src_path = path.join(repo_path, "src")
        source_paths.append(path.join(src_path, "parser.c"))
        if path.exists(path.join(src_path, "scanner.cc")):
            cpp = True
            source_paths.append(path.join(src_path, "scanner.cc"))
        elif path.exists(path.join(src_path, "scanner.c")):
            source_paths.append(path.join(src_path, "scanner.c"))
    source_mtimes = [path.getmtime(__file__)] + [path.getmtime(path_) for path_ in source_paths]

    if max(source_mtimes) <= output_mtime:
        return False

    # local import saves import time in the common case that nothing is compiled
    try:
        from distutils.ccompiler import new_compiler
        from distutils.unixccompiler import UnixCCompiler
    except ImportError as err:
        raise RuntimeError(
            "Failed to import distutils. You may need to install setuptools."
        ) from err

    compiler = new_compiler()
    if isinstance(compiler, UnixCCompiler):
        compiler.set_executables(compiler_cxx="c++")

    with TemporaryDirectory(suffix="tree_sitter_language") as out_dir:
        object_paths = []
        for source_path in source_paths:
            if system() == "Windows":
                flags = None
            else:
                flags = ["-fPIC"]
                if source_path.endswith(".c"):
                    flags.append("-std=c11")
                else:
                    flags.append("-std=c++11")
            object_paths.append(
                compiler.compile(
                    [source_path],
                    output_dir=out_dir,
                    include_dirs=[path.dirname(source_path)],
                    extra_preargs=flags,
                )[0]
            )
        compiler.link_shared_object(
            object_paths,
            output_path,
            target_lang="c++" if cpp else "c",
        )
    return True


print(f"{sys.argv[0]}: Building", languages_filename)
build_library(
    languages_filename,
    [
        'vendor/tree-sitter-bash',
        'vendor/tree-sitter-c',
        'vendor/tree-sitter-c-sharp',
        'vendor/tree-sitter-commonlisp',
        'vendor/tree-sitter-cpp',
        'vendor/tree-sitter-css',
        'vendor/tree-sitter-dockerfile',
        'vendor/tree-sitter-dot',
        'vendor/tree-sitter-elisp',
        'vendor/tree-sitter-elixir',
        'vendor/tree-sitter-elm',
        'vendor/tree-sitter-embedded-template',
        'vendor/tree-sitter-erlang',
        'vendor/tree-sitter-fixed-form-fortran',
        'vendor/tree-sitter-fortran',
        'vendor/tree-sitter-go',
        'vendor/tree-sitter-go-mod',
        'vendor/tree-sitter-hack',
        'vendor/tree-sitter-haskell',
        'vendor/tree-sitter-hcl',
        'vendor/tree-sitter-html',
        'vendor/tree-sitter-java',
        'vendor/tree-sitter-javascript',
        'vendor/tree-sitter-jsdoc',
        'vendor/tree-sitter-json',
        'vendor/tree-sitter-julia',
        'vendor/tree-sitter-kotlin',
        'vendor/tree-sitter-lua',
        'vendor/tree-sitter-make',
        'vendor/tree-sitter-markdown',
        'vendor/tree-sitter-objc',
        'vendor/tree-sitter-ocaml/ocaml',
        'vendor/tree-sitter-perl',
        'vendor/tree-sitter-php',
        'vendor/tree-sitter-python',
        'vendor/tree-sitter-ql',
        'vendor/tree-sitter-r',
        'vendor/tree-sitter-regex',
        'vendor/tree-sitter-rst',
        'vendor/tree-sitter-ruby',
        'vendor/tree-sitter-rust',
        'vendor/tree-sitter-scala',
        'vendor/tree-sitter-sql',
        'vendor/tree-sitter-sqlite',
        'vendor/tree-sitter-toml',
        'vendor/tree-sitter-tsq',
        'vendor/tree-sitter-typescript/tsx',
        'vendor/tree-sitter-typescript/typescript',
        'vendor/tree-sitter-verilog',
        'vendor/tree-sitter-yaml',
    ]
)
