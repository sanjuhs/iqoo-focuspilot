#pragma once
#include "llama.h"
#include <atomic>
#include <mutex>
#include <string>
#include <vector>

struct Activation {
    std::string name;
    int64_t width;
    int64_t positions;
    double mean;
    double rms;
    double minimum;
    double maximum;
    std::vector<float> first_values;
};

class LocalModel {
public:
    LocalModel(const std::string & path, int context, int threads);
    ~LocalModel();
    std::string generate(const std::string & prompt, const std::string & grammar, int max_tokens, bool capture);
    // Prepare before queueing a request: a later cancel must survive generate entry.
    void prepare();
    void cancel() { cancelled.store(true); }
    void shutdown() { closing.store(true); cancelled.store(true); }
private:
    llama_model * model = nullptr;
    llama_context * context = nullptr;
    llama_context_params context_params{};
    bool context_observed = false;
    void configure_context(bool observed);
    std::atomic<bool> cancelled{false};
    std::atomic<bool> closing{false};
    std::mutex generation_mutex;
    bool capturing = false;
    std::vector<Activation> activations;
    static bool observe(ggml_tensor * tensor, bool ask, void * data);
    static bool abort(void * data);
};

std::string escape_json(const std::string & input);
