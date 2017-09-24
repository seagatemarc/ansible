#!/usr/bin/env python
import smtplib
import subprocess
import filecmp
from email.mime.text import MIMEText
import MySQLdb
import sys


# # # # # # # # # # ITEMS TO CHANGE # # # # # # # # # #
host_file = '/home/backupmanager/hosts.conf.mysql'                # path to host file
ansible_playbook = '/home/backupmanager/manage_backups.yml'       # path to Ansible playbook
directory_to_backups = '/home/backupmanager/'                     # path to where backups are stored
section = 'ALLHOSTS'                                        # host group to target
emails_to_send_to = [‘someone@somewhere.com’]          # collect emails to send report
#emails_to_send_to = ['someone@somewhere.com']          # collect emails to send report

# # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # CREATE HOSTS FILE # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def write_into_hosts(file_name, category, list_of_items):
    """Writes into the  hosts file. Category is labeled first, then the list. New lines in between"""
    file_name.write(category + '\n')
    [file_name.write(elem + '\n') for elem in list_of_items]
    file_name.write('\n')
    return

# Open database connection
db = MySQLdb.connect(“db.company.com”, “user”, “password”, “db”)

# prepare a cursor object using cursor() method
cursor = db.cursor()

sql = "SELECT monitor_hosts.display_name, monitor_hosts.address, monitor_customvariables.varvalue FROM monitor_hosts LEFT JOIN monitor_customvariables ON monitor_hosts.host_object_id = monitor_customvariables.object_id"

hostDict = {}
nameList = []
addressList = []
regionList = []

try:
    # Execute the SQL command
    cursor.execute(sql)
    # Fetch all the rows in a list of lists.
    results = cursor.fetchall()
    for row in results:
        dname = row[0]
        ip = row[1]
        region = row[2]
        if (dname is not None and ip is not None and region is not None) and \
                ('db' not in dname) and ('nac' not in dname) and ('127.0.0.1' not in ip):
            hostDict[dname] = (ip, region)
            nameList.append(dname)
            addressList.append(ip)
            regionList.append(region)

except NameError:
    print "Error: unable to fetch data"

# disconnect from server
db.close()

badHostsDict = {}
wanDict = {}
wan1Dict = {}
wan2Dict = {}
inetDict = {}
inetSwDict = {}
inetRtrDict = {}
coreDict = {}
cubeDict = {}
voiceDict = {}
locationsDict = {}
regionsDict = {}
wan1reg = {}
wan2reg = {}
inetSwReg = {}
inetRtrReg = {}
wanReg = {}
inetReg = {}

for index in range(len(hostDict)):
    curName = nameList[index]
    curAddr = addressList[index]
    curRegion = regionList[index]
    # good host names have a dash as their fourth character
    if '-' != curName[3]:
        badHostsDict[curName] = curAddr
        sys.stderr.write('Warning: ' + curName + ' (' + curAddr + ') is not named using the standard convention.\n')
    else:
        if 'inet' in curName or 'int' in curName:
            inetDict[curName] = curAddr
            # classifying INETs
            if 'sw' in curName:
                inetSwDict[curName] = curAddr
                if curRegion in inetSwReg.keys():
                    inetSwReg[curRegion].append(curName)
                else:
                    inetSwReg[curRegion] = [curName]
            elif 'rtr' in curName:
                inetRtrDict[curName] = curAddr
                if curRegion in inetRtrReg.keys():
                    inetRtrReg[curRegion].append(curName)
                else:
                    inetRtrReg[curRegion] = [curName]
            if curRegion in inetReg.keys():
                inetReg[curRegion].append(curName)
            else:
                inetReg[curRegion] = [curName]
        # classifying cores
        elif 'core' in curName:
            coreDict[curName] = curAddr
        # classifying cubes
        elif 'cube' in curName:
            cubeDict[curName] = curAddr
        elif 'voice' in curName or 'sip' in curName or 'vgw' in curName:
            voiceDict[curName] = curAddr
        # classifying WANs
        elif 'wan' in curName or 'rtr' in curName:
            wanDict[curName] = curAddr
            if '2' not in curName:
                wan1Dict[curName] = curAddr
                if curRegion in wan1reg.keys():
                    wan1reg[curRegion].append(curName)
                else:
                    wan1reg[curRegion] = [curName]
            elif '2' in curName:
                wan2Dict[curName] = curAddr
                if curRegion in wan2reg.keys():
                    wan2reg[curRegion].append(curName)
                else:
                    wan2reg[curRegion] = [curName]
            if curRegion in wanReg.keys():
                wanReg[curRegion].append(curName)
            else:
                wanReg[curRegion] = [curName]
        # classifying locations
        if curName[:3] in locationsDict:
            locationsDict[curName[:3]].append(curName)
        else:
            locationsDict[curName[:3]] = [curName]
        # sorting hosts into regions
        if curRegion in regionsDict:
            regionsDict[curRegion].append(curName)
        else:
            regionsDict[curRegion] = [curName]

# create hosts.conf
confFile = open(directory_to_backups + 'hosts.conf.mysql', 'w')
# write all hosts with their IP addresses
confFile.write('[ALLHOSTS]\n')
[confFile.write(host + '\t' + 'ansible_host=' + hostDict[host][0] + '\n') for host in hostDict.keys()]
confFile.write('\n')

# write all INETs
write_into_hosts(confFile, '[ALLINET]', inetDict.keys())
write_into_hosts(confFile, '[INETSW]', inetSwDict.keys())
write_into_hosts(confFile, '[INETRTR]', inetRtrDict.keys())

# write all locations
for location in locationsDict.keys():
    write_into_hosts(confFile, '[' + location.upper() + ']', locationsDict[location])

# write all regions
for region in regionsDict.keys():
    write_into_hosts(confFile, '[' + region.upper() + ']', regionsDict[region])

# write all WANs
write_into_hosts(confFile, '[ALLWAN]', wanDict.keys())
write_into_hosts(confFile, '[ALLWAN1]', wan1Dict.keys())
write_into_hosts(confFile, '[ALLWAN2]', wan2Dict.keys())

# write all cores
write_into_hosts(confFile, '[ALLCORE]', coreDict.keys())
# write all cubes
write_into_hosts(confFile, '[ALLCUBE]', cubeDict.keys())
# write all voice
write_into_hosts(confFile, '[ALLVGW]', voiceDict.keys())

for region in wanReg.keys():
    write_into_hosts(confFile, '[' + region + 'ALLWAN]', wanReg[region])
for region in wan1reg.keys():
    write_into_hosts(confFile, '[' + region + 'ALLWAN1]', wan1reg[region])
for region in wan2reg.keys():
    write_into_hosts(confFile, '[' + region + 'ALLWAN2]', wan2reg[region])
for region in inetReg.keys():
    write_into_hosts(confFile, '[' + region + 'ALLINET]', inetReg[region])
for region in inetSwReg.keys():
    write_into_hosts(confFile, '[' + region + 'INETSW]', inetSwReg[region])
for region in inetRtrReg.keys():
    write_into_hosts(confFile, '[' + region + 'INETRTR]', inetRtrReg[region])

confFile.close()

# create file with nonstandard host names
badHostsFile = open(directory_to_backups + 'nonstandardHosts.conf', 'w')
write_into_hosts(badHostsFile, '[NONSTANDARDNAMES]', badHostsDict.keys())


# # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # MANAGE BACKUPS  # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Ansible call
subprocess.call('ansible-playbook ' + ansible_playbook + ' -i ' + host_file + ' --extra-vars "user_hosts=' + section + ' backup_directory=' + directory_to_backups + '"',
                shell=True)

# read host file
with open(host_file) as f:
    host_content = f.readlines()
host_list = [line.strip() for line in host_content]

# build a dictionary from the host file, to look up for the hosts under the desired category
host_dictionary = {}
is_first_item = False
current_category = ''
current_hosts = []

# build the dictionary based on the information in the host file
for item in host_list:
    if '[' in item:                     # a new category
        current_category = item
        is_first_item = True
    elif is_first_item:                 # first line of hosts
        current_hosts = [item.split('\t')[0]]
        is_first_item = False
    elif not item:                      # reached end of category
        host_dictionary[current_category] = current_hosts
        is_first_item = False
    else:                               # not first line of hosts
        current_hosts.append(item.split('\t')[0])


# # # # # # # # # # GET DATES AND FILES FOR FILE COMPARISON # # # # # # # # # #
today = subprocess.check_output('date +%Y%m%d', shell=True)
today = today.split('\n')[0]


# # # # # # # # # # COMPARE FILES WITH 'DIFF' IN COMMAND LINE # # # # # # # # #
changed_hosts_dict = {'fs': [], 'ntp': [], 'diff': [], 'nc': [], 'fs.ntp': []}

for host in host_dictionary['[' + section + ']']:
    # compare today's backup with the most recent found backup
    file_found = False
    files_equivalent = False
    counter = 1     # number of days to look back into

    new_date = subprocess.check_output('date --date="yesterday" +%Y%m%d', shell=True)
    new_date = new_date.split('\n')[0]

    file1 = directory_to_backups + 'configs_' + today + '/' + host + '_' + today + '.config'
    file2 = directory_to_backups + 'configs_' + new_date + '/' + host + '_' + new_date + '.config'

    # increment the number of days until a file has been found or a year has passed
    while not file_found and counter <= 365:
        try:                        # if file exists
            files_equivalent = filecmp.cmp(file1, file2)
            file_found = True

        # if file does not exist
        except OSError:
            counter += 1            # did not find file, so increment by another day
            new_date = subprocess.check_output('date --date="' + str(counter) + ' day(s) ago" +%Y%m%d', shell=True)
            new_date = new_date.split('\n')[0]
            file2 = directory_to_backups + 'configs_' + new_date + '/' + host + '_' + new_date + '.config'

    # if no backup has been found in the previous year
    if counter > 365:
        print 'No backups found in previous year for ' + str(host)
        file2 = file1
        files_equivalent = True

    # if the two compared files have ANY difference, then it will fall into this block of code
    if not files_equivalent:    # write differences into new file
        linux_output_diff = subprocess.Popen('diff -u ' + file2 + ' ' + file1, shell=True, stdout=subprocess.PIPE)
        output, error = linux_output_diff.communicate()

        diff_identifier = '@@ '     # the diff command generates '@@ ' per difference, use it to our advantage
        output_list = output.split(diff_identifier)         # itemize each difference

        # variables that keep track whether or not NAC or NTP have added lines into the config
        has_NAC = False
        has_ntp = False

        # iterate through each difference, get rid of automagically generated lines (i.e. ntp-clock and NAC)
        for difference in output_list:
            difference_deleted = False                      # a boolean value to check if the entry is deleted

            # inspect each line of the difference
            for line in difference.split('\n'):

                # if the difference has not be deleted, then we keep looking for NAC and NTP
                if not difference_deleted:

                    # check for changes that NAC added
                    if '+' in line and ('NAC_RW' in line or 'NAC_RW' in line):
                        output_list.remove(difference)      # remove the line
                        difference_deleted = True           # notify that the difference is deleted
                        has_NAC = True                # note that NAC was involved

                    # check for changes that NTP added
                    elif '+' in line and 'ntp clock-period' in line:
                        output_list.remove(difference)      # remove the line
                        difference_deleted = True           # notify that the difference is deleted
                        has_ntp = True                      # note that NTP was involved

        # output = diff_identifier.join(output_list)          # join the non-automagic stuff back together

        # if there are still differences after removing the automagically generated lines, create a .diff file. Use
        # different extensions for different purposes, which can then tell us what type of changes are involved
        if len(output_list) > 1:
            # if NAC but not NTP has made a change, use the .config.diff.fs extension
            if has_NAC and not has_ntp:
                change_file = open(
                    directory_to_backups + 'configs_' + today + '/' + host + '_' + today + '.config.diff.fs',
                    'w')
                changed_hosts_dict['fs'].append(host)

            # if NTP but not NAC has made a change, use the .config.diff.ntp extension
            elif not has_NAC and has_ntp:
                change_file = open(
                    directory_to_backups + 'configs_' + today + '/' + host + '_' + today + '.config.diff.ntp',
                    'w')
                changed_hosts_dict['ntp'].append(host)

            # if both NAC and NTP made changes, use the .config.diff.fs.ntp extension
            elif has_NAC and has_ntp:
                change_file = open(
                    directory_to_backups + 'configs_' + today + '/' + host + '_' + today + '.config.diff.fs.ntp',
                    'w')
                changed_hosts_dict['fs.ntp'].append(host)

            # if neither NAC nor NTP has made a change, use the .config.diff extension  (a user made all changes)
            else:
                change_file = open(
                    directory_to_backups + 'configs_' + today + '/' + host + '_' + today + '.config.diff',
                    'w')
                changed_hosts_dict['diff'].append(host)

        # if the only change is found in the header ("Last configuration change..."), we want to kep track of this
        # and use the .config.diff.nc extension
        else:
            change_file = open(
                directory_to_backups + 'configs_' + today + '/' + host + '_' + today + '.config.diff.nc',
                'w')
            changed_hosts_dict['nc'].append(host)

        # write the message of the email, which consists of the raw output that is created by calling 'diff'
        change_file.write(host + ' ' + today + ' ' + new_date + '\n' + output + '\n')
        change_file.close()


# # # # # # # # # # WRITE AND SEND EMAIL # # # # # # # # # #
# write body of email
message_text = ''
for category in changed_hosts_dict.keys():
    if changed_hosts_dict[category]:
        message_text += str.upper(category) + '\n'
        for host in changed_hosts_dict[category]:
            message_text += host + '\n'
        message_text += '\n'

if message_text == '':          # if there are no differences across all hosts
    message_text = 'no differences'

message = MIMEText(message_text)

# fields for email
message['Subject'] = 'Changelog for ' + today
message['From'] = 'noreply@somewhere.com'
message['To'] = ', '.join(emails_to_send_to)

# send email
s = smtplib.SMTP('mailhost.company.com', 25)
s.set_debuglevel(False)
s.sendmail('noreply@company.com', emails_to_send_to, message.as_string())
s.quit()
print 'Emails sent to ' + ', '.join(emails_to_send_to)
