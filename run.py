#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
自动更新DNS
@author: New Future
@modified: rufengsuixing
"""
from __future__ import print_function
import argparse
import json
import time
import os
import sys
import tempfile

from util import ip
from util.cache import Cache

CACHE_FILE = os.path.join(tempfile.gettempdir(), 'ddns.cache')


def get_config(key=None, default=None, path="config.json"):
    """
    读取配置
    """
    if not hasattr(get_config, "config"):
        try:
            with open(path) as configfile:
                get_config.config = json.load(configfile)
                get_config.time = os.stat(path).st_mtime
        except IOError:
            print('Config file %s does not appear to exist.' % path)
            with open(path, 'w') as configfile:
                configure = {
                    "id": "your id",
                    "token": "your token",
                    "dns": "dnspod",
                    "ipv4": [
                        "your.domain",
                        "ipv4.yours.domain"
                    ],
                    "ipv6": [
                        "your.domain",
                        "ipv6.your.domain"
                    ],
                    "index4": "default",
                    "index6": "default",
                    "proxy": None
                }
                json.dump(configure, configfile, indent=2, sort_keys=True)
            sys.exit("New template configure file is created!")
        except:
            sys.exit('fail to load config from file: %s' % path)
    if key:
        return get_config.config.get(key, default)
    else:
        return get_config.config


def get_ip(ip_type):
    """
    get IP address
    """
    index = get_config('index' + ip_type) or "default"
    if str(index).isdigit():  # local eth
        value = getattr(ip, "local_v" + ip_type)(index)
    elif any((c in index) for c in '*.:'):  # regex
        value = getattr(ip, "regex_v" + ip_type)(index)
    else:
        value = getattr(ip, index + "_v" + ip_type)()

    return value


def change_dns_record(dns, proxy_list, **kw):

    for proxy in proxy_list:
        if not proxy or (proxy.upper() in ['DIRECT', 'NONE']):
            dns.PROXY = None
        else:
            dns.PROXY = proxy
        record_type, domain = kw['record_type'], kw['domain']
        # print('%s(%s) ==> %s [via %s]' %
        #       (domain, record_type, kw['ip'], proxy))

        print('%+s    [Type: (%s)]  [Proxy: %s]' %
              (domain.rjust(9), record_type, proxy))
        try:
            result = dns.update_record(domain, kw['ip'], record_type=record_type)
            return result;
        except Exception as e:
            print(e)
    return False


def update_ip(ip_type, cache, dns, proxy_list):
    """
    更新IP
    """
    # print ("-" * 25, ip_type, "-" * 25, sep=' ')
    print("[Checking]  [ipV%s]" % (ip_type))
    ipname = 'ipv' + ip_type
    domains = get_config('ipv' + ip_type)
    if not domains:
        return None
    address = get_ip(ip_type)
    if not address:
        return False
    elif cache and (address == cache[ipname]):
        print("[Cache]".rjust(10),"[Same]","[Keeping]",sep="  ") # 缓存命中
        return True
    print("")
    record_type = (ip_type == '4') and 'A' or 'AAAA'
    update_fail = False  # https://github.com/NewFuture/DDNS/issues/16
    for domain in domains:
        index = domains.index(domain)
        print(index)
        if change_dns_record(dns, proxy_list, domain=domain, ip=address, record_type=record_type):
            update_fail = True
    if cache is not False:
        # 如果更新失败删除缓存
        cache[ipname] = update_fail and address


def main():
    """
    更新
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', default="config.json")
    get_config(path=parser.parse_args().c)
    # Dynamicly import the dns module as configuration
    dns_provider = str(get_config('dns', 'dnspod').lower())
    dns = getattr(__import__('dns', fromlist=[dns_provider]), dns_provider)
    dns.ID, dns.TOKEN = get_config('id'), get_config('token')
    dns.DOMAIN = get_config('domain')

    ip.DEBUG = get_config('debug')

    proxy = get_config('proxy') or 'DIRECT'
    proxy_list = proxy.strip('; ') .split(';')


    print ("=" * 26, "=" * len(time.ctime()), "=" * 26, "\n", sep='')

    print(" " * 30, "%s" % (dns.DOMAIN.encode("utf8")).rjust( len(time.ctime())/2 - 2),"\n",sep="")

    print ("=" * 25, time.ctime(), "=" * 25, "\n", sep=' ')


    cache = get_config('cache', True) and Cache(CACHE_FILE)

    print("[OGetting]  [Address]")

    # address = get_ip("4")
    print("[Now]".rjust(10) + "  [" +  get_ip("4") + "]")
    cache = False;

    if cache is False:
        # print("Cache is disabled!")
        print ("[Cache]".rjust(10),"[Disabled]",sep="  ")
    elif len(cache) < 1 or get_config.time >= cache.time:
        cache.clear()
        # print ("=" * 25, time.ctime(), "=" * 25, sep=' ')
        print ("[Cache]".rjust(10),"[Cleared]",sep="  ")

    update_ip('4', cache, dns, proxy_list)
    # update_ip('6', cache, dns, proxy_list)
    print('[Session]'.rjust(10)+"  [End]", end=" ")
    print("\n")
    print ("_" * 25, time.ctime(), "_" * 25, sep=' ')
    print ("_" * 26, "_" * len(time.ctime()), "_" * 26, "\n", sep='')

    print("\n")

if __name__ == '__main__':
    main()

