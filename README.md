# ansible
We have begun our Ansible journey and beleive some of the code is mature enough to share for consumption to others. Opening the solutions to broader community and paying forward any assitance maturing the code. 

It is a significant pivot from traditional deployments using commercial vendor tools and siloed custom scripts not availble nor compatible globally. Keep in mind we are still crawling but first steps are on their way. This is an attempt at that. Hoping to get some candid feedback but please no trolls!

The first solution presented is a backup manager. It combines both Python and Ansible to collect cofigurations on a schedule, analyze differences in configurations, write differences into a .diff file, and send email for hosts where changes were observed. 

The Ansible host file is dynamically generated from a Nagios DB in the script , hosts are categorized by name 
