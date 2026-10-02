#include "llama.h"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <regex>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
constexpr int MAX_PROMPT_TOKENS = 896;
struct Prompt { std::string id, text; int count = 0; };

static std::vector<Prompt> read_prompts(const fs::path & directory) {
    if (!fs::is_directory(directory) || fs::is_symlink(fs::symlink_status(directory)))
        throw std::runtime_error("Selected real prompt directory required");
    std::vector<Prompt> prompts;
    size_t total_bytes = 0;
    for (const auto & entry : fs::directory_iterator(directory)) {
        const auto path = entry.path();
        if (!fs::is_regular_file(entry.symlink_status()) || path.extension() != ".txt")
            throw std::runtime_error("Directory must contain only direct regular .txt prompts");
        const std::string id = path.stem().string();
        if (!std::regex_match(id, std::regex("[A-Za-z0-9_-]{1,64}")))
            throw std::runtime_error("Bounded ASCII prompt ID required");
        const auto size = entry.file_size();
        if (!size || size > 12000 || (total_bytes += size) > 1024 * 1024)
            throw std::runtime_error("Prompt byte allowance exceeded");
        std::ifstream stream(path, std::ios::binary);
        if (!stream) throw std::runtime_error("Selected prompt unavailable");
        std::string text(static_cast<size_t>(size), '\0');
        stream.read(text.data(), static_cast<std::streamsize>(size));
        if (!stream || stream.peek() != std::char_traits<char>::eof() || text.find('\0') != std::string::npos)
            throw std::runtime_error("Prompt changed during read or contains NUL");
        prompts.push_back({id, std::move(text), 0});
        if (prompts.size() > 200) throw std::runtime_error("At most 200 selected prompts required");
    }
    if (prompts.empty()) throw std::runtime_error("Nonempty selected prompt inventory required");
    std::sort(prompts.begin(), prompts.end(), [](const Prompt & a, const Prompt & b) { return a.id < b.id; });
    return prompts;
}

int main(int argc, char ** argv) {
    try {
        if (argc != 3) throw std::runtime_error("Usage: token_count MODEL PROMPT_DIR");
        auto prompts = read_prompts(argv[2]);
        if (!fs::is_regular_file(argv[1])) throw std::runtime_error("Selected existing model required");
        llama_backend_init();
        struct BackendCleanup { ~BackendCleanup() { llama_backend_free(); } } backend_cleanup;
        auto params = llama_model_default_params();
        static ggml_backend_dev_t cpu_only[] = {nullptr};
        params.devices = cpu_only;
        params.n_gpu_layers = 0;
        params.vocab_only = true;
        params.use_mmap = true;
        std::unique_ptr<llama_model, decltype(&llama_model_free)> model(
                llama_model_load_from_file(argv[1], params), llama_model_free);
        if (!model) throw std::runtime_error("Vocabulary-only model load failed");
        const auto * vocab = llama_model_get_vocab(model.get());
        if (!vocab) throw std::runtime_error("Model vocabulary missing");
        bool all_fit = true;
        for (auto & prompt : prompts) {
            // Match the selected native capture exactly: add_special=true, parse_special=true.
            const int32_t needed = llama_tokenize(vocab, prompt.text.data(),
                    static_cast<int32_t>(prompt.text.size()), nullptr, 0, true, true);
            if (needed >= 0 || needed == std::numeric_limits<int32_t>::min())
                throw std::runtime_error("Tokenizer size query failed");
            std::vector<llama_token> tokens(static_cast<size_t>(-needed));
            const int32_t count = llama_tokenize(vocab, prompt.text.data(),
                    static_cast<int32_t>(prompt.text.size()), tokens.data(),
                    static_cast<int32_t>(tokens.size()), true, true);
            if (count <= 0 || count != -needed) throw std::runtime_error("Tokenizer count changed");
            prompt.count = count;
            all_fit = all_fit && count <= MAX_PROMPT_TOKENS;
        }
        // No partial count inventory is emitted on a load/tokenization failure.
        for (const auto & prompt : prompts) {
            std::cout << "{\"id\":\"" << prompt.id << "\",\"token_count\":" << prompt.count
                << ",\"maximum_prompt_tokens\":" << MAX_PROMPT_TOKENS
                << ",\"within_limit\":" << (prompt.count <= MAX_PROMPT_TOKENS ? "true" : "false")
                << ",\"vocab_only\":true,\"n_gpu_layers\":0,\"add_special\":true,\"parse_special\":true,\"generation_called\":false}\n";
        }
        return all_fit ? 0 : 3;
    } catch (const std::exception & failure) {
        std::cerr << "TOKEN_COUNT_FAILED: " << failure.what() << '\n';
        return 2;
    }
}
