import subprocess
import os
import shutil
import sys
import logging

logging.basicConfig(filename='analyzer.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def decompile_pyc(pyc_file, source_dir):
    try:
        pycdc_process = subprocess.Popen(['resources\pycdc.exe', pyc_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
        stdout, stderr = pycdc_process.communicate()
        decoded_code = stdout.decode('utf-8')
        pyc_filename = os.path.basename(pyc_file)
        py_filename = pyc_filename[:-4] + '.py'
        
        count = 2
        while os.path.exists(os.path.join(source_dir, py_filename)):
            py_filename = pyc_filename[:-4] + f'_{count}.py'
            count += 1

        py_filepath = os.path.join(source_dir, py_filename)
        with open(py_filepath, 'w') as py_file:
            py_file.write(decoded_code)
        logging.info(f"Decompiled {pyc_filename}")
        print(f"Decompiled {pyc_filename}")
    except Exception as e:
        logging.error(f"Error decompiling pyc: {e}")
        print(f"Error decompiling pyc: {e}")
        return

def main():
    logging.info("Starting analysis.")
    if len(sys.argv) != 2:
        logging.error("Usage: python script.py FILE_TO_ANALYZE.exe")
        print("Usage: python script.py FILE_TO_ANALYZE.exe")
        sys.exit(1)

    file_to_analyze = sys.argv[1]
    extracted_dir = file_to_analyze + '_extracted'
    source_dir = file_to_analyze + '_source'
    entry_points_dir = os.path.join(source_dir, 'entry_points')

    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(entry_points_dir, exist_ok=True)

    try:
        pycdc_process = subprocess.Popen(['python', 'resources\pyinstxtractor.py', file_to_analyze, '-w', extracted_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
        stdout, stderr = pycdc_process.communicate()
        output_lines = stdout.decode('utf-8').splitlines()

        entry_points = [line.split()[-1] for line in output_lines if 'Possible entry point' in line]
        logging.info(f"Possible entry points: {entry_points}")

        for root, dirs, files in os.walk(extracted_dir):
            for file in files:
                if file.endswith('.pyc'):
                    pyc_file = os.path.join(root, file)
                    pyc_filename = os.path.basename(pyc_file)
                    if pyc_filename in entry_points:
                        logging.info(f"Decompiling entry point: {pyc_filename}")
                        decompile_pyc(pyc_file, source_dir)
                        source_file = os.path.join(source_dir, pyc_filename[:-4] + '.py')
                        entry_point_dest = os.path.join(entry_points_dir, pyc_filename[:-4] + '.py')
                        shutil.move(source_file, entry_point_dest)

        continue_with_others = input("Do you want to continue with decompiling other files? (y/n): ").strip().lower()
        if continue_with_others != 'y':
            logging.info("Decompilation of other files cancelled.")
            print("Decompilation of other files cancelled.")
            shutil.rmtree(extracted_dir)
            logging.info("Analysis completed.")
            print("Analysis completed.")
            sys.exit(0)

        for root, dirs, files in os.walk(extracted_dir):
            for file in files:
                if file.endswith('.pyc'):
                    pyc_file = os.path.join(root, file)
                    pyc_filename = os.path.basename(pyc_file)
                    if pyc_filename not in entry_points:
                        logging.info(f"Decompiling: {pyc_filename}")
                        decompile_pyc(pyc_file, source_dir)

    except subprocess.CalledProcessError as e:
        logging.error(f"Error extracting bytecode: {e}")
        print(f"Error extracting bytecode: {e}")
        sys.exit(1)

    shutil.rmtree(extracted_dir)
    logging.info("Analysis completed.")
    print("Analysis completed.")

if __name__ == '__main__':
    main()
