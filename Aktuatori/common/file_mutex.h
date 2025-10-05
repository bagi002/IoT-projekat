#ifndef FILE_MUTEX_H
#define FILE_MUTEX_H

#include <mutex>

// Deklaracija globalnog mutex-a za zaštitu AKTUATORI.json fajla
extern std::mutex aktuatori_file_mutex;

#endif // FILE_MUTEX_H
