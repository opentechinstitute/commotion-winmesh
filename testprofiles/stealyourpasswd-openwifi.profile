ssid=stealyourpasswd-openwifi
#Network name (REQUIRED)
bssid=01:02:03:04:05:06
#IBSS cell ID, which takes the form of a fake mac address.  If this field is omitted, it will be automatically generated via an md4 hash of the ssid and channel.
channel=11
#2.4 GHz Channel (REQUIRED)
ip=1.2.3.4
#When ipgenerate=true, ip holds the subnet from which the actual ip will be generated.  When ipgenerate=false, ip holds the actual ip that will be used for the connection (REQUIRED)
ipgenerate=false
#See not for ip parameter.  ipgenerate is automatically set to false once a permanent ip has been generated (REQUIRED)
netmask=255.0.0.0
#The subnet mask of the network (REQUIRED)
dns=2.2.2.2
#DNS server (REQUIRED)

