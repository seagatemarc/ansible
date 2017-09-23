# ansible
We have begun our Ansible journey and beleive some of the code is mature enough to share for consumption by others. By contributing the solution for a broader community we hope to pay forward assitance maturing the code. 

It is a significant pivot from traditional deployments using commercial vendor tools and siloed custom scripts not availble nor compatible globally. Keep in mind we are still crawling but first steps are on their way! Hoping to get some candid feedback and contributinos but please no trolls!

The first solution presented is a backup manager. It combines both Python and Ansible to collect cofigurations on a schedule, analyze differences in configurations, write differences into a .diff file, and send email for hosts where changes were observed. 

The Ansible host file is dynamically generated from a Nagios DB in the script for groupings. The hostname is used for gropuing both device function (router, switch, Internet router, voice gateway, etc...) and location. Addtional field in the DB is used to identify the region. While the backup manager does not leverage the groupings we added the intelligence thinking forward about standardizing the configurations based on location and function.

