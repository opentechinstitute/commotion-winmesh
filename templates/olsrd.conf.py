
# http://commotionwireless.net/

DebugLevel 0
AllowNoInt yes
IpVersion 4
LinkQualityLevel 2
LinkQualityAlgorithm "etx_ffeth"
SmartGateway yes

Hna4
{{
        {masked_ip} {netmask}
}}

#LoadPlugin "lib/arprefresh/olsrd_arprefresh.dll"
#{{
#}}

#LoadPlugin "lib/dyn_gw/olsrd_dyn_gw.dll"
#{{
#}}

#LoadPlugin "lib/nameservice/olsrd_nameservice.dll"
#{{
#    # you should set this to your own node name
#	PlParam "name" "commotion-7814921"
#	PlParam "sighup-pid-file" "/var/run/dnsmasq.pid"
#	PlParam "suffix" ".mesh"
#}}

#LoadPlugin "lib/p2pd/olsrd_p2pd.dll"
#{{
#	PlParam "NonOlsrIf" "eth0"
#	PlParam "P2pdTtl" "5"
#	PlParam "UdpDestPort" "224.0.0.251 5353"
#}}

LoadPlugin "olsrd_jsoninfo.dll"
{{
#	PlParam "accept" "0.0.0.0"
}}


LoadPlugin "olsrd_txtinfo.dll"
{{
#	PlParam "accept" "0.0.0.0"
}}

InterfaceDefaults
{{
    # if you using this on Mac OS X, then comment this out because Mac OS X
    # does weird things with 255.255.255.255. By commenting this out, olsrd
    # will use the broadcast that's assigned to the network interface
	Ip4Broadcast 255.255.255.255
}}

Interface "{interface_name}"
{{
}}
