#include "ip.h"
#include <arpa/inet.h>
namespace ndnfd {

bool IpAddressVerifier::Check(const NetworkAddress& addr) {
  return (addr.wholen == sizeof(sockaddr_in) && addr.family() == AF_INET)
         || (addr.wholen == sizeof(sockaddr_in6) && addr.family() == AF_INET6);
}

NetworkAddress IpAddressVerifier::Normalize(const NetworkAddress& addr) {
  NetworkAddress n; n.wholen = addr.wholen;
  if (addr.wholen == sizeof(sockaddr_in)) {
    const sockaddr_in* src = reinterpret_cast<const sockaddr_in*>(&addr.who);
    sockaddr_in* dst = reinterpret_cast<sockaddr_in*>(&n.who);
    dst->sin_family = AF_INET;
    dst->sin_port = src->sin_port;
    dst->sin_addr.s_addr = src->sin_addr.s_addr;
  } else if (addr.wholen == sizeof(sockaddr_in6)) {
    const sockaddr_in6* src = reinterpret_cast<const sockaddr_in6*>(&addr.who);
    sockaddr_in6* dst = reinterpret_cast<sockaddr_in6*>(&n.who);
    dst->sin6_family = AF_INET6;
    dst->sin6_port = src->sin6_port;
    memcpy(dst->sin6_addr.s6_addr, src->sin6_addr.s6_addr, sizeof(dst->sin6_addr.s6_addr));
  } else {
    assert(false);
  }
  return n;
}

std::string IpAddressVerifier::ToString(const NetworkAddress& addr) {
  char buf[INET6_ADDRSTRLEN];
  std::string r;
  in_port_t port = 0;
  if (addr.wholen == sizeof(sockaddr_in)) {
    const sockaddr_in* sa = reinterpret_cast<const sockaddr_in*>(&addr.who);
    inet_ntop(AF_INET, &sa->sin_addr, buf, sizeof(buf));
    r.append(buf);
    port = sa->sin_port;
  } else if (addr.wholen == sizeof(sockaddr_in6)) {
    const sockaddr_in6* sa = reinterpret_cast<const sockaddr_in6*>(&addr.who);
    inet_ntop(AF_INET6, &sa->sin6_addr, buf, sizeof(buf));
    r.push_back('[');
    r.append(buf);
    r.push_back(']');
    port = sa->sin6_port;
  } else {
    assert(false);
  }
  sprintf(buf, ":%d", be16toh(port));
  r.append(buf);
  return r;
}

std::tuple<bool,NetworkAddress> IpAddressVerifier::Parse(std::string s) {
  NetworkAddress addr;
  size_t port_delim = s.find_last_of(":");
  in_port_t port = 0;
  if (port_delim != std::string::npos) {
    port = htobe16(static_cast<uint16_t>(atoi(s.c_str()+port_delim+1)));
    s.erase(port_delim);
  }
  if (s[0] == '[' && s[s.size()-1] == ']') {
    s.erase(0, 1);
    s.erase(s.size()-1);
    // don't try IPv4 if host is wrapped by [ ]
  } else {
    sockaddr_in* sa4 = reinterpret_cast<sockaddr_in*>(&addr.who);
    if (1 == inet_pton(AF_INET, s.c_str(), &sa4->sin_addr)) {
      sa4->sin_family = AF_INET;
      sa4->sin_port = port;
      addr.wholen = sizeof(*sa4);
      return std::forward_as_tuple(true, addr);
    }
  }
  
  sockaddr_in6* sa6 = reinterpret_cast<sockaddr_in6*>(&addr.who);
  if (1 == inet_pton(AF_INET6, s.c_str(), &sa6->sin6_addr)) {
    sa6->sin6_family = AF_INET6;
    sa6->sin6_port = port;
    addr.wholen = sizeof(*sa6);
    return std::forward_as_tuple(true, addr);
  }
  return std::forward_as_tuple(false, addr);
}

};//namespace ndnfd