netsh wlan add profile filename="{profile_name}.xml"
netsh wlan connect name="{profile_name}" interface="{iface_name}"
olsrd.exe -i "{iface_name}" -f olsrd.conf
