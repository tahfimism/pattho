
import os
import time

def count_lines_in_file(file_path):
    """Counts total and non-empty lines in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            total_lines = len(lines)
            non_empty_lines = sum(1 for line in lines if line.strip())
            return total_lines, non_empty_lines
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return 0, 0

def count_code_lines(directory="."):
    """Counts lines of code in .py, .html, .css, and .js files."""
    start_time = time.time()
    total_lines_count = 0
    code_lines_count = 0
    file_extensions = ('.py', '.html', '.css', '.js')
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(file_extensions):
                file_path = os.path.join(root, file)
                total, code = count_lines_in_file(file_path)
                total_lines_count += total
                code_lines_count += code

    end_time = time.time()
    print(f"Total lines (including empty): {total_lines_count}")
    print(f"Total lines of code (excluding empty): {code_lines_count}")
    print(f"Execution time: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    count_code_lines()
