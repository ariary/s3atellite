def Dim(str):
    return "\033[2m"+str+"\033[0m"

def Cyan(str):
    return "\033[1;96m"+str+"\033[0m"

def Green(str):
    return "\033[1;32m"+str+"\033[0m"

def Red(str):
    return "\033[1;31m"+str+"\033[0m"

def Yellow(str):
    return "\033[1;33m"+str+"\033[0m"

def Bold(str):
    return "\033[1m"+str+"\033[0m"

def print_conf(args,region,buckets,profile):
    print(Bold(Green("🐍 s3nake.py "+ args.mode+" mode:")))
    print(Green("  • 🌍 region: ")+region)
    print(Green("  • 🪣 buckets: ") + ', '.join(buckets))
    print(Green("  • 👤 profile: ") + profile)
    print()
