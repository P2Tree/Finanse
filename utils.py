def info(info):
    print("\033[1;32m", end='')
    print("[Info] \033[0m", end='')
    print(info)

def warning(info):
    print("\033[1;33m", end='')
    print("[Warn] \033[0m", end='')
    print(info)

def error(info):
    print("\033[1;31m", end='')
    print("[Erro] \033[0m", end='')
    print(info)

def ask(info):
    print("\033[1;36m[Input] \033[0m", end='')
    ins = input(info)

    return ins



