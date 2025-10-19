import os
import time
import subprocess
import shutil
import re
from typing import List

SOURCE_FILE = "spy.cpp"
EXECUTABLE = "./spy"
OUTPUT_DIR = "results"
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
# Number of key bytes to attack — 
# can be changed together with the section of code that handles PLAINTEXT_BYTE_START
KEY_BYTES_TO_TEST = 4

def modify_source_code(key_type: str, target_byte_index: int):
    source_path = os.path.join(SCRIPT_DIR, SOURCE_FILE)
    
    with open(source_path, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    
    line_iter = iter(lines)
    for line in line_iter:
        
        if "KEY_REALISTIC_START" in line:
            new_lines.append(line)
            while "KEY_REALISTIC_END" not in (line := next(line_iter)):
                if "KEY_" in line and line.strip().startswith("//"):
                    new_lines.append(line)
                    continue
                    
                is_commented = line.strip().startswith("//")
                if key_type == "realistic" and is_commented:
                    new_lines.append(line.replace("//", "  ", 1))
                elif key_type == "profiling" and not is_commented:
                    new_lines.append(f"  //{line.strip()}\n")
                else:
                    new_lines.append(line)
            new_lines.append(line)
            continue
            
        if "KEY_PROFILING_START" in line:
            new_lines.append(line)
            while "KEY_PROFILING_END" not in (line := next(line_iter)):
                if "KEY_" in line and line.strip().startswith("//"):
                    new_lines.append(line)
                    continue
                    
                is_commented = line.strip().startswith("//")
                if key_type == "profiling" and is_commented:
                    new_lines.append(line.replace("//", "  ", 1))
                elif key_type == "realistic" and not is_commented:
                    new_lines.append(f"  //{line.strip()}\n")
                else:
                    new_lines.append(line)
            new_lines.append(line)
            continue
            
        if "PLAINTEXT_BYTE_START" in line:
            new_lines.append(line)
            while "PLAINTEXT_BYTE_END" not in (line := next(line_iter)):
                match = re.search(r'^\s*(//\s*)?plaintext\[(\d+)\]\s*=\s*byte;', line)
                if match:
                    byte_index = int(match.group(2))
                    if byte_index == target_byte_index:
                        new_lines.append(f"    plaintext[{byte_index}] = byte;\n")
                    else:
                        new_lines.append(f"    //plaintext[{byte_index}] = byte;\n")
                else:
                    new_lines.append(line)
            continue

        if "RANDOMIZE_LOOP_START" in line:
            new_lines.append(line)
            new_lines.append(f"        for (size_t j = 0; j < 16; ++j) {{\n")
            new_lines.append(f"          if (j == {target_byte_index}) continue;\n")
            new_lines.append(f"          plaintext[j] = rand() % 256;\n")
            new_lines.append(f"        }}\n")
            while "RANDOMIZE_LOOP_END" not in (line := next(line_iter)):
                pass
            new_lines.append(line)
            continue
        
        if "plaintext[0] |= 0xF;" in line:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(f"{indent}plaintext[{target_byte_index}] |= 0xF;\n")
            continue
            
        new_lines.append(line)

    with open(source_path, 'w') as f:
        f.writelines(new_lines)
Before starting the Cache Temp
def run_command(command: List[str], env_overrides: dict = None, retry: bool = False) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.pop("MAKEFLAGS", None)
    env["MAKEFLAGS"] = "-j1"
    
    libcrypto_path = os.path.join(SCRIPT_DIR, "libcrypto.so.1.0.0")
    if os.path.exists(libcrypto_path):
        env["LD_LIBRARY_PATH"] = SCRIPT_DIR
        env["LD_PRELOAD"] = libcrypto_path
    
    if env_overrides:
        env.update(env_overrides)

    cmd_str = " ".join(command)
    print(f"Command or executable/binary run: {cmd_str} \npath = {SCRIPT_DIR}")
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR,
        env=env
    )

    return result

if __name__ == "__main__":
    output_path = os.path.join(SCRIPT_DIR, OUTPUT_DIR)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"Output directory created: {output_path}")

    source_path = os.path.join(SCRIPT_DIR, SOURCE_FILE)
    backup_path = f"{source_path}.bak"

    shutil.copy(source_path, backup_path)
    print("Temporary backup file created.")

    key_bytes_to_test = list(range(KEY_BYTES_TO_TEST))
    print(f"Target key byte: {key_bytes_to_test}")

    try:
        for key_type in ["profiling", "realistic"]:
            for i in key_bytes_to_test:
                print(f"\n{'='*60}")
                print(f"Test start: [Key type: {key_type.upper()}, Key byte: {i}]")
                print(f"{'='*60}")

                shutil.copy(backup_path, source_path)

                modify_source_code(key_type=key_type, target_byte_index=i)

                run_command(["make", "clean"], retry=True)
                try:
                    os.sync()
                except AttributeError:
                    pass
                time.sleep(0.1)

                run_command(["make"], retry=True)

                executable_path = os.path.join(SCRIPT_DIR, EXECUTABLE.lstrip('./'))
                result = run_command([executable_path])

                output_filename = os.path.join(output_path, f"{key_type}_keybyte_{i}")
                with open(output_filename, "w") as f:
                    f.write(result.stdout)
                print(f"Results saved in: {output_filename}")
                if key_type == "profiling":
                    print(f"This file contains the range of offsets containing the target pattern of key byte {i} (profiling key)")
                else:
                    print(f"This file contains the data to deduce the bits of key byte {i} (realistic key)")

    finally:
        shutil.copy(backup_path, source_path)
        os.remove(backup_path)
        print("\n" + "="*60)
        print("Original source file restored.")
        print(f"Tests completed for {KEY_BYTES_TO_TEST} key byte.")
        print("="*60)