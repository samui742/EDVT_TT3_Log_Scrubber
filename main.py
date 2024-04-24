import re
import requests
import os
import pyautogui
from art import text2art
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
def extract_uut_list(html):
    uut_match = re.findall(r'UUT\d+ </span></td>', html)
    uut_list = []

    for match in uut_match:
        uut_id = re.search(r'\d+', match).group(0)
        if uut_id not in uut_list:
            uut_list.append(uut_id)
    return uut_list
def extract_corner_ids(html):
    # print(html)
    corner_match = re.findall(r'data-cornerid="\d+"', html)
    corner_list = []
    for match in corner_match:
        corner_id = re.search(r'\d+', match).group(0)
        if corner_id not in corner_list:
            corner_list.append(corner_id)

    corner_name_match = re.findall(r'data-cornername=".*', html)
    corner_name_list = []
    for match in corner_name_match:
        corner_name = re.search(r'"(.*?)"', match).group(1).strip("Test").strip(" ")
        # corner_name = corner_name.strip(" Test")
        if corner_name not in corner_name_list:
            corner_name_list.append(corner_name)

    # print("corner_list", *corner_list)
    # print("corner_name_list", *corner_name_list)
    corner_dict = {id: corner for id, corner in zip(corner_list, corner_name_list)}
    # print("corner_dict", corner_dict)

    return corner_list, corner_dict
def parse_jobids(jobids_input):
    jobid_list = []

    if "," in str(jobids_input):
        jobid_list.extend(jobids_input.split(','))
        # jobid_list = list(jobids_input)
        jobid_list = [item.strip() for item in jobid_list]
    else:
        jobid_list.append(str(jobids_input))

    # print(jobid_list)
    return jobid_list
def parse_keywords(keywords_input):
    keyword_list = []

    if "," in str(keywords_input):
        keyword_list = keywords_input.split(',')
        keyword_list = [item.strip() for item in keyword_list]
    else:
        keyword_list.append(str(keywords_input).strip())

    # Add to support comma search. User has to input as semicolon
    for i in range(len(keyword_list)):
        if ";" in keyword_list[i]:
            x = keyword_list[i].replace(";",",")
            # print(keyword_list[i])
            keyword_list[i] = x

    return keyword_list

def parse_corners(corners_list, corner_select):
    corner_map = []
    corner_select = corner_select.replace(",", "")

    for item in corner_select:
        corner_map.append(corners_list[int(item) - 1])

    return corner_map

def parse_uuts(uut_list, uut_select):
    uut_map = []
    uut_select = uut_select.replace(",", "")

    for item in uut_select:
        uut_map.append(uut_list[int(item) - 1])

    return uut_map

def grab_switch_logs(corner, uut, jobid, username, password):

    local_log = "no"
    url = f"https://wwwin-testtracker3.cisco.com/trackerApp/oneviewlog/switch{uut}.log?page=1&corner_id={corner}"

    response = requests.get(url, auth=(username, password))
    response.close()
    html_log = response.text

    # Create a local log file
    html_log_name = f"{jobid}_{corner}_uut{uut}_html_log.txt"
    # print(html_log_name)

    try:
        #content = html_log[html_log.index("TESTCASE START"):html_log.index("Corner - runSwitch")]
        content = html_log[html_log.index("Total testcases to execute"):html_log.index("Corner - runSwitch")]
    except ValueError:
        # print(f"no log found on uut{uut}. The unit might be the link partner")
        content = "unit " + str(uut) + (" has no log file or uncompleted. Must be a link partner unit or corner was aborted")

    # To add option if need a local html log
    if local_log == "yes":
        with open(html_log_name, "w") as local_log:
            # local_log.write(html_log)
            local_log.write(content)

    return content, url
def switch_log_request(jobids_input, keywords_input, username, password, option):

    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    allow_duplicate = "yes"
    jobid_list = parse_jobids(jobids_input)
    print("jobIDs to proceed = ", jobid_list)

    keyword_list = parse_keywords(keywords_input)
    print("Keywords to search = ", keyword_list)

    for jobid in jobid_list:
        #Send HTTP Request with TT3 credentials
        url = f"https://wwwin-testtracker3.cisco.com/trackerApp/cornerTest/{jobid}"
        response = requests.get(url, auth=(username, password))
        response.close()
        html = response.text

        # corner_list = extract_corner_ids(html)
        corner_list, corner_dict = extract_corner_ids(html)
        uut_list = extract_uut_list(html)
        len_corner = len(corner_list)
        print(f'JOBID# {jobid} has total {len(corner_list)} corners.' + 'Corner number: ', ','.join(map(str, range(1, len_corner + 1))))
        corner_select = input(f'Press enter to search all or specify corner number (using comma if there are multiples): ')
        print(f'There are total {len(uut_list)} units.' + 'Unit number: ', ','.join(map(str, uut_list)))
        uut_select = input(f'Press enter to search all or specify unit number (using comma if there are multiples): ')

        if len(corner_select) == 0:
            pass
        else:
            corner_list = parse_corners(corner_list, corner_select)

        if len(uut_select) == 0:
            pass
        else:
            uut_list = parse_uuts(uut_list, uut_select)

        for uut in uut_list:
            result_file = f"{jobid}_uut{uut}_{option}_result.txt"
            with open(result_file, "w") as result_file:
                for corner in corner_list:
                    content, url = grab_switch_logs(corner, uut, jobid, username, password)
                    # Process content starts from here
                    if len(keywords) != 0:
                        print("="*100)
                        print(f'jobid={jobid} cornerid={corner} uut={uut}')
                        # print(f'jobid= {jobid} cornerid= {corner} cornername= {corner_dict[corner]} uut= {uut}')
                        print("Keywords to search = ", keyword_list)
                        print(f'{url}')
                        print("="*100)
                        result_file.write("="*100 + "\n")
                        result_file.write(f'jobid={jobid} cornerid={corner} uut={uut}' + "\n")
                        # result_file.write(f'jobid={jobid} cornerid={corner} cornername= {corner_dict[corner]} uut={uut}' + "\n")
                        result_file.write(f"URL: {url}" + "\n")
                        result_file.write("="*100 + "\n")
                        lines = content.splitlines()
                        line_with_keyword_list = []

                        for line in lines:
                            # To handle crashed corner
                            if f'REMOVING switch{uut} FROM CURRENT CORNER - JOB' in line:
                                print(f'{bcolors.BOLD}{bcolors.WARNING} *** Corner is NOT completed, switch is removed from the current corner ***{bcolors.ENDC}')
                                result_file.write(
                                    '\nCorner is NOT completed, switch is removed from the current corner\n\n')
                            # To handle link partner unit which does not have log file
                            if 'has no log file or uncompleted. Must be a link partner unit or corner was aborted' in line:
                                # print(f'{bcolors.BOLD}{bcolors.WARNING} *** has no log file match. Could be a link partner unit ***{bcolors.ENDC}')
                                print(f'{bcolors.BOLD}{bcolors.WARNING}*** {line} ***{bcolors.ENDC}')
                                result_file.write(line + "\n")

                            for keyword in keyword_list:
                                if keyword in line:
                                    if allow_duplicate == "yes":
                                        line_with_keyword_list.append(line)
                                        # To display testcase names on the report
                                        if "TESTCASE START" in line:
                                            print("\t" + f'{bcolors.OKBLUE}{line}{bcolors.ENDC}')
                                            result_file.write("\t" + line + "\n")
                                        else:
                                            print("\t\t\t" + f'{bcolors.FAIL}{line}{bcolors.ENDC}')
                                            result_file.write("\t\t\t" + line + "\n")
                                    else:
                                        if line not in line_with_keyword_list:
                                            line_with_keyword_list.append(line)
                                            if "TESTCASE START" in line:
                                                print("\t" + f'{bcolors.OKBLUE}{line}{bcolors.ENDC}')
                                                result_file.write("\t" + line + "\n")
                                            else:
                                                print("\t\t\t" + f'{bcolors.FAIL}{line}{bcolors.ENDC}')
                                                result_file.write("\t\t\t" + line + "\n")
            result_file.close()
def command_output_request(jobids_input, command_user, username, password, option):

    jobid_list = parse_jobids(jobids_input)
    print("User input these jobIDs = ", jobid_list)

    for jobid in jobid_list:
        #Send HTTP Request with TT3 credentials
        url = f"https://wwwin-testtracker3.cisco.com/trackerApp/cornerTest/{jobid}"
        response = requests.get(url, auth=(username, password))
        response.close()
        html = response.text
        # corner_list = extract_corner_ids(html)
        # corner_list, corner_dict = extract_corner_ids(html)
        # uut_list = extract_uut_list(html)
        # html = response.text
        # corner_list = extract_corner_ids(html)
        corner_list, corner_dict = extract_corner_ids(html)
        uut_list = extract_uut_list(html)

        len_corner = len(corner_list)
        print(f'JOBID#{jobid} has total {len(corner_list)} corners.' + 'Corner number: ',
              ','.join(map(str, range(1, len_corner + 1))))
        corner_select = input(
            f'Press enter to search all or specify corner number (using comma if there are multiples): ')
        print(f'There are total {len(uut_list)} units.' + 'Unit number: ', ','.join(map(str, uut_list)))
        uut_select = input(f'Press enter to search all or specify unit number (using comma if there are multiples): ')

        if len(corner_select) == 0:
            pass
        else:
            corner_list = parse_corners(corner_list, corner_select)

        if len(uut_select) == 0:
            pass
        else:
            uut_list = parse_uuts(uut_list, uut_select)

        # for uut in uut_list:
        #
        # corner_select = input(f'There are total {len(corner_list)} corners. Corner number: {corner_list}'
        #                       f'\nPress enter to search on all corners or specific corner by using comma: ')
        #
        # if len(corner_select) == 0:
        #     pass
        # else:
        #     corner_list = parse_corners(corner_list, corner_select)

        for uut in uut_list:
            output_file = f"{jobid}_uut{uut}_command_output_result.txt"
            with open(output_file, "w") as output_file:
                for corner in corner_list:
                    start_list = []
                    stop_list = []
                    content, url = grab_switch_logs(corner, uut, jobid, username, password)
                    print("="*100)
                    print(f'jobid={jobid} cornerid={corner} uut={uut}')
                    # print(f'jobid= {jobid} cornerid= {corner} cornername= {corner_dict[corner]} uut= {uut}')

                    print(f'{url}')
                    print("="*100)
                    output_file.write("="*100 + "\n")
                    output_file.write(f'jobid={jobid} cornerid={corner} uut={uut}' + "\n")
                    # output_file.write(f'jobid={jobid} cornerid={corner} cornername= {corner_dict[corner]} uut={uut}' + "\n")
                    output_file.write(f"URL: {url}" + "\n")
                    output_file.write("="*100 + "\n")

                    # To specify stop point of each command output
                    # TT3 might change the print out which will affect the code here
                    stop_keyword = "platform"  # old test effort
                    # stop_keyword = "*****************************************************************************************************************" # new test effort from Apr'24

                    lines = content.split('\n')
                    for i in range(len(lines)):
                        if command_user in lines[i]:
                            start_list.append(i)

                    # START SEARCHING FOR STOP POINT FROM WHERE THE COMMAND IS FOUND THEN BREAK ONCE FOUND
                    for item in start_list:
                        for i in range(item, len(lines)):
                            if stop_keyword in lines[i]:
                                stop_list.append(i)
                                break

                    # MAPPING BETWEEN START AND STOP POINT LIST
                    mapped = list(zip(start_list, stop_list))
                    # print(*mapped, sep="\n")

                    # WRITE RESULT INTO TEXT FILE
                    command_output = []
                    for (command_user_index, stop_keyword_index) in mapped:
                        for line in lines[command_user_index - 1:stop_keyword_index + 1]:
                            # if "Tune timeout on SerDes" not in line and "platform" not in line:
                            if "Tune timeout on SerDes" not in line:
                                command_output.append(line)
                                print(line)
                                output_file.write(line + '\n')
                output_file.close()


def statshow_diag_scrub(jobids_input, command_user, username, password, option):

    jobid_list = parse_jobids(jobids_input)
    print("User input these jobIDs = ", jobid_list)

    for jobid in jobid_list:
        #Send HTTP Request with TT3 credentials
        url = f"https://wwwin-testtracker3.cisco.com/trackerApp/cornerTest/{jobid}"
        response = requests.get(url, auth=(username, password))
        response.close()
        html = response.text
        # corner_list = extract_corner_ids(html)
        # uut_list = extract_uut_list(html)

        # html = response.text

        # corner_list = extract_corner_ids(html)
        corner_list, corner_dict = extract_corner_ids(html)
        uut_list = extract_uut_list(html)
        len_corner = len(corner_list)
        print(f'JOBID# {jobid} has total {len(corner_list)} corners.' + 'Corner number: ',
              ','.join(map(str, range(1, len_corner + 1))))
        corner_select = input(
            f'Press enter to search all or specify corner number (using comma if there are multiples): ')
        print(f'There are total {len(uut_list)} units.' + 'Unit number: ', ','.join(map(str, uut_list)))
        uut_select = input(f'Press enter to search all or specify unit number (using comma if there are multiples): ')

        if len(corner_select) == 0:
            pass
        else:
            corner_list = parse_corners(corner_list, corner_select)

        if len(uut_select) == 0:
            pass
        else:
            uut_list = parse_uuts(uut_list, uut_select)

        # for uut in uut_list:
        #
        #
        # corner_select = input(f'There are total {len(corner_list)} corners. Corner number: {corner_list}'
        #                       f'\nPress enter to search on all corners or specific corner by using comma: ')
        #
        # if len(corner_select) == 0:
        #     pass
        # else:
        #     corner_list = parse_corners(corner_list, corner_select)

        for uut in uut_list:
            output_file = f"{jobid}_uut{uut}_command_output_result.txt"
            with open(output_file, "w") as output_file:

                for corner in corner_list:
                    start_list = []
                    stop_list = []

                    content, url = grab_switch_logs(corner, uut, jobid, username, password)
                    print("="*100)
                    print(f'jobid={jobid} cornerid={corner} uut={uut}')
                    # print(f'jobid={jobid} cornerid={corner} cornername={corner_dict[corner]} uut={uut}')
                    print(f'{url}')
                    print("="*100)
                    output_file.write("="*100 + "\n")
                    output_file.write(f'jobid={jobid} cornerid={corner} uut={uut}' + "\n")
                    output_file.write(f"URL: {url}" + "\n")
                    output_file.write("="*100 + "\n")

                    # IN THE FUTURE COULD ASK TT3 TO ADD A BETTER MESSAGE
                    stop_keyword = "platform"
                    # stop_keyword = "*****************************************************************************************************************" # new test effort from Apr'24


                    # COVERT STRING INTO LIST
                    lines = content.split('\n')
                    # RETURN LIST INDEX WHEN COMMAND IS FOUND
                    for i in range(len(lines)):
                        if command_user in lines[i]:
                            start_list.append(i)

                    # START SEARCHING FOR STOP POINT FROM WHERE THE COMMAND IS FOUND THEN BREAK ONCE FOUND
                    for item in start_list:
                        for i in range(item, len(lines)):
                            if stop_keyword in lines[i]:
                                stop_list.append(i)
                                break

                    # MAPPING BETWEEN START AND STOP POINT LIST
                    mapped = list(zip(start_list, stop_list))
                    # print(*mapped, sep="\n")

                    # WRITE RESULT INTO TEXT FILE
                    command_output = []
                    for (command_user_index, stop_keyword_index) in mapped:
                        statshow_list = lines[command_user_index - 1:stop_keyword_index + 1]
                        # print(statshow_list)
                        statshow_error(statshow_list)
                        for line in lines[command_user_index - 1:stop_keyword_index + 1]:
                            # if "Tune timeout on SerDes" not in line and "platform" not in line:
                            if "Tune timeout on SerDes" not in line:
                                command_output.append(line)
                                # print(line)
                                output_file.write(line + '\n')
                output_file.close()
def statshow_error(statshow_list):

    start_index = statshow_list.index("   P#   Transmit      TxBytes     TxErr  Receive      RxBytes     RxFcs RxIpg RxCol OvrSz UndSz RxSym OvRun\r")
    # stop_index = statshow_list.index("Traf&gt; platform : 9300")
    stop_index = statshow_list.index("*************")
    lines = statshow_list[start_index:stop_index - 1]

    for line in lines:
        line.strip('\r')
        line.lstrip(' ')

    for line in lines:
        if "----" in line:
            lines.remove(line)

    for line in lines:
        if "P#   Transmit" in line:
            lines.remove(line)

    list_of_dict = []
    non_zero_error_portlist = []
    for line in lines:
        data = {}
        (data['P#'], data['Transmit'], data['TxBytes'], data['TxErr'], data['Receive'], data['RxBytes'], data['RxFcs'],
         data['RxIpg'], data['RxCol'], data['OvrSz'], data['UndSz'], data['RxSym'], data['OvRun']) = line.split()

        list_of_dict.append(data)

    for item in list_of_dict:
        if item["RxFcs"] != '00000' or item["RxIpg"] != '00000' or item["RxCol"] != '00000' or item["OvrSz"] != '00000' or item["UndSz"] != '00000' or item["RxSym"] != '00000' or item["OvRun"] != '00000':
            print(
                f'{bcolors.WARNING}{item["P#"]:<10} {item["Transmit"]:<10} {item["TxBytes"]:<10} {item["TxErr"]:<10} {item["Receive"]:<10} {item["RxBytes"]:<10} {item["RxFcs"]:<10} {item["RxIpg"]:<10} {item["RxCol"]:<10} {item["OvrSz"]:<10} {item["UndSz"]:<10} {item["RxSym"]:<10} {item["OvRun"]:<10} {bcolors.ENDC}')
            non_zero_error_portlist.append(item["P#"])

    print("non_zero_error_portlist", non_zero_error_portlist)
    if len(non_zero_error_portlist) == 0:
        print('all error counters are zero'.upper())
        print(f'{bcolors.BOLD}{bcolors.OKBLUE}{"P#":<10} {"Transmit":<10} {"TxBytes":<10} {"TxErr":<10} {"Receive":<10} {"RxBytes":<10} {"RxFcs":<10} {"RxIpg":<10} {"RxCol":<10} {"OvrSz":<10} {"UndSz":<10} {"RxSym":<10} {"OvRun":<10} {bcolors.ENDC}')

        for item in list_of_dict:
            print(
                f'{bcolors.OKGREEN}{item["P#"]:<10} {item["Transmit"]:<10} {item["TxBytes"]:<10} {item["TxErr"]:<10} {item["Receive"]:<10} {item["RxBytes"]:<10} {item["RxFcs"]:<10} {item["RxIpg"]:<10} {item["RxCol"]:<10} {item["OvrSz"]:<10} {item["UndSz"]:<10} {item["RxSym"]:<10} {item["OvRun"]:<10} {bcolors.ENDC}')
    else:
        print(f'{bcolors.BOLD}{bcolors.OKBLUE}{"P#":<10} {"Transmit":<10} {"TxBytes":<10} {"TxErr":<10} {"Receive":<10} {"RxBytes":<10} {"RxFcs":<10} {"RxIpg":<10} {"RxCol":<10} {"OvrSz":<10} {"UndSz":<10} {"RxSym":<10} {"OvRun":<10} {bcolors.ENDC}')
        for port in non_zero_error_portlist:
            print(port)
            if item in list_of_dict:
                print(f'{bcolors.WARNING}{item["P#"]:<10} {item["Transmit"]:<10} {item["TxBytes"]:<10} {item["TxErr"]:<10} {item["Receive"]:<10} {item["RxBytes"]:<10} {item["RxFcs"]:<10} {item["RxIpg"]:<10} {item["RxCol"]:<10} {item["OvrSz"]:<10} {item["UndSz"]:<10} {item["RxSym"]:<10} {item["OvRun"]:<10} {bcolors.ENDC}')


############ MAIN ################

if __name__ == '__main__':

    banner = text2art("EDVT \nLog Scrubber", space=1)
    print("\n" + banner + "\n")

    jobids = input("Enter JOBID (separate by comma for multiples): ")
    print('Enter CEC username and password in the popup window')
    username = pyautogui.prompt('input your cec username: ')
    password = pyautogui.password('input your password: ')
    if len(username) == 0 or len(password) == 0:
        print("Username and Password can't be blank. Please restart the program")
        quit()

    options = input(f'\nSelect from options below \n\
    \n\
    1 - search by keywords \n\
    2 - filter specific command output \n\
    3 - ixia diag failure \n\
    4 - istardust diag traffic failure \n\
    5 - istardust poe diag traffic failure \n\
    6 - diag traffic failure \n\
    7 - arcadecr vdd_avs check \n\
    8 - pwrcycle diag suite \n\
    \n\
    Please enter the number: ')

    if options == "1":
        # keywords = " MODEL_NUM,  SYSTEM_SERIAL, Test(s) failed:, test(s) failed"
        option = "keyword_search"
        keywords = input("Enter keywords separate by comma: ")
        switch_log_request(jobids, keywords, username, password, option)

    elif options == "2":
        option = "command_output"
        command = input("Enter the command: ")
        command = "command is : {" + command
        command_output_request(jobids, command, username, password, option)

    elif options == "3":
        option = "ixia_diag"
        command = "statshow"
        command = "command is : {" + command
        statshow_diag_scrub(jobids, command, username, password, option)

    elif options == "4":
        option = "istardust_traffic"
        keywords = "TESTCASE START -, FAILED VALIDATION -, Pass Fail, Fail Pass, Fail Fail, Status: Failed, ERROR DOYLE_FPGA, FAILED: Timeout,  ERROR: Leaba_Err"
        switch_log_request(jobids, keywords, username, password, option)

    elif options == "5":
        option = "istardust_poe_traffic"
        # keywords = "TESTCASE START -, FAILED VALIDATION -, 0W; 0W; 0W,Pass Fail, Fail Pass, Fail Fail, Status: Failed, ERROR DOYLE_FPGA, FAILED: Timeout,  ERROR: Leaba_Err"
        keywords = "TESTCASE START -, FAILED VALIDATION -, FAILED VALIDATION while, Pass Fail, Fail Pass, Fail Fail, Status: Failed, ERROR DOYLE_FPGA, FAILED: Timeout,  ERROR: Leaba_Err"
        switch_log_request(jobids, keywords, username, password, option)

    elif options == "6":
        option = "diag_traffic"
        keywords = "FAILED VALIDATION while, FAILED VALIDATION -, FAIL**  E, FAIL**  P, TESTCASE START -"
        switch_log_request(jobids, keywords, username, password, option)

    elif options == "7":
        option = "vdd_avs_search"
        keywords = "SYSTEM_SERIAL_NUM, VDD_AVS |"
        switch_log_request(jobids, keywords, username, password, option)

    elif options == "8":
        option = "pwrcycle_diag_suite"
        keywords = "Test(s) failed:,  FAILED VALIDATION -, FAILED: Timeout, TESTCASE START -, FAIL*"
        switch_log_request(jobids, keywords, username, password, option)