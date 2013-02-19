#ifndef NDNFD_UTIL_LOGGING_H_
#define NDNFD_UTIL_LOGGING_H_
#include "util/defs.h"
namespace ndnfd {

enum LoggingLevel {
  kLLDebug = 10,
  kLLInfo = 20,
  kLLWarn = 30,
  kLLError = 40
};

typedef uint32_t LoggingComponent;
const LoggingComponent kLCPollMgr = 0x0001;
const LoggingComponent kLCScheduler = 0x0002;
const LoggingComponent kLCWireProto = 0x0010;
const LoggingComponent kLCFace = 0x0020;

class Logging {
  public:
    Logging(void);
    LoggingLevel min_level(void) const { return this->min_level_; }
    void set_min_level(LoggingLevel value) { this->min_level_ = value; }
    LoggingComponent components(void) const { return this->components_; }
    void set_components(LoggingComponent value) { this->components_ = value; }
    
    void Log(LoggingLevel level, LoggingComponent component, const char* format, ...);
    void LogVA(LoggingLevel level, LoggingComponent component, const char* format, va_list* args);
    
  private:
    LoggingLevel min_level_;
    LoggingComponent components_;
};


};//namespace ndnfd
#endif//NDNFD_UTIL_LOGGING_H_