import ipaddress


def is_ip_in_whitelist(whitelist: str | list, ip: str) -> bool:
    """
    检查 ip 参数是否在 whitelist 参数代表的白名单当中
    :param whitelist:
    :param ip:
    :return: bool, 当在则返回 True，否则返回 False
    """
    if isinstance(whitelist, str):
        whitelist = whitelist.split(",")

    ip_addr = ipaddress.ip_address(ip)
    for item in whitelist:
        if "/" in item:  # 判断是否为网段
            network = ipaddress.ip_network(item, strict=False)
            if ip_addr in network:
                return True
        else:  # 处理单个IP地址
            if ip_addr == ipaddress.ip_address(item):
                return True

    return False


def is_ip_or_network(string: str) -> bool:
    """
    Check if the given string is a valid IP address or network.

    :param string: str, the string to check.
    :return: bool, True if the string is a valid IP address or network, False otherwise.
    """
    try:
        # Try parsing as an IP address
        ipaddress.ip_address(string)
        return True
    except ValueError:
        pass

    try:
        # Try parsing as an IP network
        ipaddress.ip_network(string, strict=False)
        return True
    except ValueError:
        pass

    return False
