#!/bin/python3

import sys, shutil, os, json, readline
import subprocess as sp
from os import path as pt
from lib.yesno import yesno_choice

LOCAL   = pt.realpath(pt.join(pt.expanduser("~"), ".local"))
HERE    = pt.dirname(pt.realpath(__file__))
BIN     = pt.join(LOCAL, "bin")
DIRS    = pt.join(HERE, "dirs")
CONN    = pt.join(HERE, "connect.txt")


# functions


def seek_line(file_path: str, target: str, n = 0) -> int:
    with open(file_path, 'r') as file:
        for line_number, line in enumerate(file, 1):
            if n == -1 and line[:-1] == target : return line_number
            if n != -1 and line.split(" ")[n] == target : return line_number
    return 0

def get_line(file_path: str, n: int) -> str or None:
    with open(file_path, 'r') as file:
        t = enumerate(file, 1)
        if len(t) >= n and t[n]:
            return t[n]
    return None

def seek_lines(file_path: str, target: str, n = 0):
    res = []
    with open(file_path, 'r') as file:
        for _, line in enumerate(file, 1):
            if line.split(" ")[n] == target : res.append(line)
    return res

def destroy_line(file_path: str, line_number: int) -> bool:
    lines = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
    if 1 <= line_number <= len(lines):
        del lines[line_number - 1]
        with open(file_path, 'w') as file:
            file.writelines(lines)
        return True
    else : return False

def connect(bin, dir, rel) -> bool:
    HERE = pt.realpath(pt.join(LOCAL, "src"))
    CONN = pt.join(HERE, "connect.txt")
    if not pt.exists(CONN):
        return False
    with open(CONN, "a+") as f:
        str = "{} {} {}\n".format(bin, dir, rel)
        f.write(str)
    return True

def try_install(func):
    def wrapper():
        if pt.realpath(pt.dirname(HERE)) != LOCAL:
            if pt.exists(pt.join(BIN, "src")):
                os.remove(pt.join(BIN, "src"))
            shutil.move(HERE, LOCAL)
            os.system("ln -s {} {}".format(
                pt.realpath(pt.join(pt.join(LOCAL, "src"), "src.py")),
                pt.join(BIN, "src"))
            )
        func()
    return wrapper

def execute_srcmak(file: str, packageName: str, allowSudo = True, secured = False):
    index = seek_line(file, "define " + packageName, n = -1)
    if index == 0 : return print("Warn: The package doesnt exists")
    with open(file, 'r') as f:
        lines = f.readlines()
        readRes = f.read()
        print(lines, readRes)
        assert not ("sudo" in readRes and not allowSudo
                    ), "Sudo is not allowed in some src.mak, you need to use a flag\nHint: Use --sudoer to execute the src.mak anyway"
        
        if secured:
            print("Most srcmak files are not long, and shouldn't be compilcated to understand, please read them to avoid hack.")
            print("Hint: Use the flag --non-strict to hide these messages\n")
            if yesno_choice("Do you want to exit for reading the srcmak file to avoid malicious programs ?") : return

        if all(w in readRes for w in ["curl", "wget", "git", "nc", "ncat", "netcat", "scp", "lynx", "fetch", "scp"]):
            print("Warning: trying to get packages from internet, it can be dangerous!")
            if not yesno_choice("Continue anyway ?") : return
        lines = [l[:-1] for l in lines]
        whereami = DIRS

        for i in range(index, len(lines)):
            if lines[i] == "endef" : break
            if len(lines[i]) == 0 : continue
            cmdArgs = lines[i].split(' ')
            if cmdArgs[0][0] == '\t':
                cmdArgs[0] = cmdArgs[0][1:]
            if cmdArgs[0] == '[CD]':
                whereami = pt.realpath(pt.join(whereami, cmdArgs[1]))
                continue
            if cmdArgs[0] == '[INSTALL]':
                res = sp.Popen(["which dnf || which apt"], shell=True, stderr=sp.PIPE, stdout=sp.PIPE)
                out, _ = res.communicate()
                out = out.decode("utf-8")[:-1]
                installs = " ".join([cmdArgs[i] for i in range(1, len(cmdArgs))])
                print("Requires sudo to install: {}".format(installs))
                os.system(f"sudo {out} install {installs}")
                continue
            if cmdArgs[0] == "[LINK]" and len(cmdArgs) >= 4 and cmdArgs[2] == "->":
                print("Creating link...")
                exepath = pt.realpath(pt.join(whereami, cmdArgs[3]))
                assert connect(cmdArgs[1], pt.basename(whereami), cmdArgs[3]), "Cant write in connect"
                os.system("ln -s {} {}".format(exepath, pt.join(BIN, cmdArgs[1])))
                continue
            os.system(f"cd {whereami}; " + lines[i])
    print("Successfuly executed the src.mak!")



# methods

def _add(av) -> int:
    assert len(av) >= 2, ("Add takes at least one argument")
    for i in range(1, len(av)):
        assert pt.exists(av[i]), (av[i] + " doesnt exists")
        assert pt.isdir(av[i]), (av[i] + " needs to be a folder")
    for i in range(1, len(av)):
        print("Adding", av[i], "...")
        shutil.move(av[i], DIRS)
        print("Checking for a src.mak file...")
        dir = pt.join(DIRS, av[i])
        files = os.listdir(dir)
        srcmak = None
        for f in files:
            if f.endswith("src.mak"):
                srcmak = pt.join(dir, f)
                break
        if srcmak:
            print("Founded!")
            print(srcmak)
            execute_srcmak(srcmak, av[i], allowSudo=False, secured=True)
        else:
            print("Not founded, continue")
    print("Success!")


@try_install
def _help():
    HERE = pt.realpath(pt.join(LOCAL, "src"))
    with open(pt.join(HERE, "usage.txt"), 'r') as f:
        print(f.read())

def _git(av):
    assert (len(av) >= 2), ("The git command needs another argument: the repository.")
    split = av[1].split('/')
    assert (len(split) == 2) and (not ("" in split)), ("Please give the user and the repo, 'src git paulogarithm/src' for example.")
    res = sp.Popen(['curl -s -o /dev/null -w "%{http_code}" https://api.github.com/repos/' + av[1]],
                   stderr=sp.PIPE, stdout=sp.PIPE, shell=True)
    out, err = res.communicate()
    out = out.decode('utf-8')
    err = err.decode('utf-8')
    assert err == "", (err[:-1] + "\nHint: Have you curl installed ?")
    assert out == "200", av[1] + " not found"
    
    res = sp.Popen(['curl https://api.github.com/repos/' + av[1]], stderr=sp.PIPE, stdout=sp.PIPE, shell=True)
    out = res.communicate()[0]
    out = out.decode('utf-8')
    infos = json.loads(out)
    print(av[1] + " has been found, coded in {}, with {} stars.\n".format(infos['language'], infos['stargazers_count']))
    if not yesno_choice("Download an additionnal {} kB program ?".format(infos['size'])) : return

    print("Cloning github.com/" + av[1] + ' in dirs...')
    res = sp.Popen(['git clone https://github.com/' + av[1] + " " + pt.join(DIRS, split[1])],
                    stderr=sp.PIPE, stdout=sp.PIPE, shell=True)
    err = res.communicate()[1]
    err = err.decode("utf-8")
    assert res.returncode == 0, "$" + err[:-1] + "\nHint: A folder have the same name in dirs, consider 'src rm' it !"

    print("Checking for a src.mak file...")
    dir = pt.join(DIRS, split[1])
    files = os.listdir(dir)
    srcmak = None
    for f in files:
        if f.endswith("src.mak"):
            srcmak = pt.join(dir, f)
            break
    if srcmak:
        print("Founded!")
        execute_srcmak(srcmak, split[1], allowSudo=False, secured=True)
    else:
        print("Not founded, continue")
    print('Success!')

def _link(av):
    assert len(av) >= 2, "Needs at least 3 arguments!"
    
    dir = pt.join(DIRS, av[1])
    assert pt.exists(dir), "dirs/" + av[1] + " doesnt exists\nHint: do 'src view dirs' to see the folder"
    
    name = ""
    while True:
        print()
        name = input("> What would you want the binary to be named ? ")
        res = sp.Popen(['which ' + name], shell=True, stdout=sp.PIPE)
        msg = res.communicate()[0]
        if name == "":
            print("Quit")
            return
        if res.returncode == 0:
            print("\nThis binary already exists in {}.".format(msg.decode("utf-8")[:-1]))
            if not yesno_choice("Do you want to replace it ?", False) : continue
            index = seek_line(CONN, name)
            if index != 0:
                destroy_line(CONN, index)
            os.system("rm {}".format(msg.decode("utf-8")[:-1]))
        break
    exe = ""
    exepath = ""
    while True:
        print()
        exe = input("> What is the binary in dirs/{} that will be linked ? ".format(av[1]))
        if exe == "":
            print("Quit")
            return
        exepath = pt.join(dir, exe)
        if not pt.exists(exepath) or not pt.isfile(exepath):
            print("\nFile doesnt exists")
            continue
        if not os.access(exepath, os.X_OK):
            print("\nFile is not an executable")
            if not yesno_choice('Want to give the right permissions ?') : print(); continue
            os.system("chmod +x " + exepath)
        break
    assert connect(name, av[1], exe), "Cant write in connect"
    os.system("ln -s {} {}".format(exepath, pt.join(BIN, name)))
    print("\nSuccess!")

def _rmlink(av):
    assert len(av) >= 2, "You need to give the link name as an argument"
    for i in range(1, len(av)):
        if i != 1 : print()
        binfile = pt.join(BIN, av[i])
        index = seek_line(CONN, av[i])
        assert index != 0, "File not found from src, it may be another program !\nHint: use 'src see' to see all the binaries from src"

        if not yesno_choice("Do you want to remove the {} link ?".format(av[i])) : return
        destroy_line(CONN, index)
        if pt.exists(binfile):
            os.system("rm {}".format(binfile))
        print(f"Successfully removed {av[i]}!")

def _rm(av):
    assert len(av) >= 2, "Needs at least 2 arguments"
    for i in range(1, len(av)):
        if i != 1 : print()
        folder = pt.join(DIRS, av[i])
        assert pt.exists(folder), "Source not found\nHint: do 'src see dirs' or 'src see' to see the sources"
        assert pt.isdir(folder), "Source is not a directory"
        all_lines = seek_lines(CONN, av[i], n = 1)
        all_lines = [n.split(' ')[0] for n in all_lines]
        
        l = len(all_lines)
        if l > 0:
            print(f"Removing {av[i]} will destroy {l} links:")
            print(*all_lines, end='\n\n')
        print("You will also need to reinstall and rebuild from scratch")
        if not yesno_choice("Are you sure you want to destroy the folder ?".format(av[i]), default=False) : return
        [os.system("rm {}".format(BIN + "/" + x)) for x in all_lines]
        [destroy_line(CONN, seek_line(CONN, x)) for x in all_lines]
        shutil.rmtree(folder)
        print("Success!")

def _do(av):
    assert len(av) >= 3, "Needs at least 3 arguments!"
    assert av[1] == "in", "Needs 'in dir' for the do command, do src help"

    dir = pt.join(DIRS, av[2])
    assert pt.exists(dir), "dirs/" + av[2] + " doesnt exists\nHint: do 'src see dirs' to see the folders"

    if len(av) == 3:
        print("Type q, nothing or exit to leave the terminal\n")
        while True:
            try : action = input("dirs/" + av[2] + "$ ")
            except : print(); break
            if action in ["", "exit", "q"]:
                break
            os.system("cd {} && {}".format(dir, action))
    else:
        command_str = av[3:len(av) + 1]
        command_str = " ".join(command_str)
        commands = command_str.split('+')
        for c in commands:
            if c == "" : continue
            os.system("cd {} && {}".format(dir, c))

def _see(av) -> int:
    HERE = pt.realpath(pt.join(LOCAL, "src"))
    with open(pt.join(HERE, "connect.txt"), 'r') as f:
        print(f.read())

def _install(av):
    assert len(av) >= 2, "You need to precise the package"
    CFG = pt.realpath(pt.join(HERE, "src.mak"))
    assert pt.exists(CFG), "The config file is missing in the src"
    for i in range(1, len(av)):
        execute_srcmak(CFG, av[i])


def main():
    av = sys.argv
    av.pop(0)
    if len(av) == 0 : return _help()
    if av[0] == "help" : return _help()
    if av[0] == "add" : return _add(av)
    if av[0] == "git" : return _git(av)
    if av[0] == "link" : return _link(av)
    if av[0] == "rmlink" : return _rmlink(av)
    if av[0] == "rm" : return _rm(av)
    if av[0] == "do" : return _do(av)
    if av[0] == "see" : return _see(av)
    if av[0] == "install" : return _install(av)

if __name__ == "__main__":
    try : main()
    except AssertionError as e:
        msg = e.args[0]
        nl = msg[0] == "$"
        if nl : msg = msg[1:]
        print("{}[E]".format("\n" if nl else ""), msg, file=sys.stderr)
        exit(1)
    exit(0)