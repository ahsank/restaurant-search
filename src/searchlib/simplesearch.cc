#include <simplesearch.h>
#include <fstream>
#include <stdexcept>

bool iscontain(const std::string& line, const std::string& term) {
    return line.find(term) != std::string::npos;
}

std::vector<std::string> simplesearch(const std::string& filename, const std::string& term) {
    std::vector<std::string> results;
    std::ifstream file(filename);
    if (!file.is_open()) {
        throw std::runtime_error("Error opening file: " + filename);
    }

    std::string line;
    while (std::getline(file, line)) {
        if (iscontain(line, term)) {
            results.push_back(line);
        }
    }

    file.close();
    return results;
}

