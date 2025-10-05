#include "file_mutex.h"

// Definicija globalnog mutex-a za zaštitu AKTUATORI.json fajla
std::mutex aktuatori_file_mutex;
