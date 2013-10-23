ssid=commotionwireless.net 
#Network name (REQUIRED)
bssid=02:CA:FF:EE:BA:BE
#IBSS cell ID, which takes the form of a fake mac address.  If this field is omitted, it will be automatically generated via an md4 hash of the ssid and channel.
channel=5
#2.4 GHz Channel (REQUIRED)
ip=5.0.0.0
#When ipgenerate=true, ip holds the subnet from which the actual ip will be generated.  When ipgenerate=false, ip holds the actual ip that will be used for the connection (REQUIRED)
ipgenerate=true
#See not for ip parameter.  ipgenerate is automatically set to false once a permanent ip has been generated (REQUIRED)
netmask=255.0.0.0
#The subnet mask of the network (REQUIRED)
dns=8.8.8.8
#DNS server (REQUIRED)
psk=Scalio40t1
#The password required to connect to an IBSS-RSN encrypted mesh network.  When connecting to a network with an encrypted backhaul, this parameter is required.  When connecting to a networking without encryption, the parameter should be omitted entirely.  
