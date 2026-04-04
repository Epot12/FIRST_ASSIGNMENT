#ifndef DATALOADER_H
#define DATALOADER_H

#include <vector>
#include <string>

using real_t = double;

class DataLoader {
public:
    static std::vector<std::vector<real_t>> load(const std::string& filepath, bool skip_first_column = false);
};

#endif // DATALOADER_H