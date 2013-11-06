plugins that build for win32 target
---

- dot_draw

- dyn_gw_plain

- httpinfo

- jsoninfo

- mini

- pgraph

- secure

- txtinfo

- watchdog


plugins without current win32 compatibility
---

### arprefresh ###
- missing net/if_arp.h

### bmf ###
- missing netinet/ip.h
- missing syslog.h
- missing linux/if_ether.h
- Notes only supported on Linux and Android

### dnssd ###
- missing netinet/ip.h
- missing ldns/ldns.h
- Notes only supported on Linux

### dyn_gw ###
- various errors and warnings
- finishes with Error 1

### mdns ###
- missing linux/if_ether.h
- missing netinet/ip.h
- missing syslog.h
- Notes only supported on Linux

### mdp ###
- missing poll.h

### nameservice ###
- missing regex.h
- Notes that just needs regex for win32

### p2pd ###
- missing netinet/ip.h
- missing linux/if_ether.h
- Notes only supported on Linux

### pud ###
- missing OlsrdPudWireFormat/wireFormat.h
- missing nmea/info.h
- Notes not supported on win32

### quagga ###
- missing sys/un.h
- Notes quagga itself not supported on windows

### sgwdynspeed ###
- missing regex.h
- Notes not supported on win32


