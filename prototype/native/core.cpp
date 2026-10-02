#include "core.h"
#include "ggml-backend.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <iomanip>
#include <memory>
#include <sstream>
#include <stdexcept>
#ifdef __ANDROID__
#include <android/log.h>
// Record only backend-selection diagnostics, never prompts, tensor values or paths.
static void android_backend_log(enum ggml_log_level, const char * text, void *) {
    if(text && std::strstr(text,"kleidiai:"))
        __android_log_write(ANDROID_LOG_INFO,"FocusPilotBackend",text);
}
#endif

using Clock = std::chrono::steady_clock;
static double elapsed(Clock::time_point start) { return std::chrono::duration<double,std::milli>(Clock::now()-start).count(); }

std::string escape_json(const std::string & input) {
    std::ostringstream out;
    out << '"';
    for (unsigned char ch : input) {
        switch(ch) { case '"': out << "\\\""; break; case '\\': out << "\\\\"; break;
            case '\n': out << "\\n"; break; case '\r': out << "\\r"; break; case '\t': out << "\\t"; break;
            default: if(ch < 32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << (int)ch << std::dec;
                else out << ch; }
    }
    out << '"'; return out.str();
}

LocalModel::LocalModel(const std::string & path, int size, int threads) {
    if(size < 512 || size > 1024 || threads < 1 || threads > 8) throw std::runtime_error("Context must be 512-1024 and threads 1-8");
    static std::once_flag backend_once;
    std::call_once(backend_once, [] {
#ifdef __ANDROID__
        llama_log_set(android_backend_log,nullptr);
#endif
        llama_backend_init();
    });
    auto mp = llama_model_default_params();
    static ggml_backend_dev_t cpu_only_devices[] = { nullptr };
    mp.devices = cpu_only_devices;
    mp.n_gpu_layers = 0;
    mp.use_mmap = true;
    model = llama_model_load_from_file(path.c_str(), mp);
    if(!model) throw std::runtime_error("Could not load the local GGUF model");
    auto cp = llama_context_default_params();
    cp.n_ctx = size; cp.n_batch = size; cp.n_ubatch = 256; cp.n_seq_max = 1;
    cp.n_threads = threads; cp.n_threads_batch = threads;
    cp.offload_kqv = false; cp.op_offload = false;
    cp.abort_callback = abort; cp.abort_callback_data = this;
    context_params = cp;
    context = llama_init_from_model(model, context_params);
    if(!context) { llama_model_free(model); model=nullptr; throw std::runtime_error("Could not allocate CPU context"); }
}

void LocalModel::configure_context(bool observed) {
    if(context && context_observed == observed) return;
    // One context at a time, sharing the same loaded weights. The public C API has
    // no eval-callback setter. Recreate on observation-mode changes so normal
    // generation takes the scheduler's callback-free path. Every command already
    // resets recurrent/KV state; no cached session is lost here.
    if(context) { llama_free(context); context = nullptr; }
    auto cp = context_params;
    cp.cb_eval = observed ? observe : nullptr;
    cp.cb_eval_user_data = observed ? this : nullptr;
    context = llama_init_from_model(model, cp);
    if(!context) throw std::runtime_error("Could not allocate CPU context");
    context_observed = observed;
}

LocalModel::~LocalModel() { if(context) llama_free(context); if(model) llama_model_free(model); }
bool LocalModel::abort(void * data) { auto & self=*static_cast<LocalModel *>(data);return self.cancelled.load()||self.closing.load(); }

bool LocalModel::observe(ggml_tensor * tensor, bool ask, void * data) {
    auto & self = *static_cast<LocalModel *>(data);
    const std::string name = ggml_get_name(tensor);
    const bool selected = name == "ffn_out-0" || name == "ffn_out-11" || name == "ffn_out-23" || name == "result_norm";
    const bool wanted = self.capturing && selected && tensor->type == GGML_TYPE_F32
        && ggml_is_contiguous(tensor) && tensor->ne[0] > 0 && tensor->ne[1] > 0;
    if(ask) return wanted;
    if(!wanted) return true;
    // Copy one last-position vector, without mutating the tensor. Callback synchronization
    // and transfer overhead are part of instrumented latency, not the unobserved baseline.
    const size_t width = tensor->ne[0];
    std::vector<float> values(width);
    const size_t offset = static_cast<size_t>(tensor->ne[1]-1) * tensor->nb[1];
    ggml_backend_tensor_get(tensor,values.data(),offset,width*sizeof(float));
    double sum=0,squares=0;
    for(float value:values) { if(!std::isfinite(value)) return true; sum+=value; squares+=value*value; }
    Activation event{name,static_cast<int64_t>(width),tensor->ne[1],sum/width,std::sqrt(squares/width),
        *std::min_element(values.begin(),values.end()),*std::max_element(values.begin(),values.end()),{}};
    event.first_values.assign(values.begin(),values.begin()+std::min<size_t>(8,width));
    // Retain the latest observed vector summary for each selected node. During chunked
    // prefill the last chunk replaces the prior chunk; capture is disabled for generation.
    auto existing=std::find_if(self.activations.begin(),self.activations.end(),[&](const Activation & old){return old.name==name;});
    if(existing==self.activations.end()) self.activations.push_back(event); else *existing=event;
    return true;
}

void LocalModel::prepare() {
    std::unique_lock<std::mutex> lock(generation_mutex,std::try_to_lock);
    if(!lock.owns_lock()) throw std::runtime_error("Generation already active");
    if(closing.load()) throw std::runtime_error("Model is closing");
    cancelled.store(false);
}

std::string LocalModel::generate(const std::string & prompt, const std::string & grammar, int maximum, bool capture) {
    std::lock_guard<std::mutex> lock(generation_mutex);
    if(closing.load()) throw std::runtime_error("Model is closing");
    if(cancelled.load()) throw std::runtime_error("Generation cancelled before start");
    if(maximum < 1 || maximum > 128 || prompt.empty() || prompt.size()>12000 || grammar.empty()) throw std::runtime_error("Invalid prompt, grammar or generation bound");
    activations.clear(); capturing=false;
    const auto setup_started = Clock::now();
    configure_context(capture);
    const double context_setup_ms = elapsed(setup_started);
    // Qwen3.5 has recurrent state as well as KV attention. Reset all memory for every
    // command and any later intervention; no history/cache reuse enters this experiment.
    llama_memory_clear(llama_get_memory(context),true);
    const auto * vocab = llama_model_get_vocab(model);
    int count = llama_tokenize(vocab,prompt.data(),prompt.size(),nullptr,0,true,true);
    if(count>=0) throw std::runtime_error("Unexpected tokenizer sizing result");
    std::vector<llama_token> tokens(-count);
    count=llama_tokenize(vocab,prompt.data(),prompt.size(),tokens.data(),tokens.size(),true,true);
    if(count<=0 || count+maximum>static_cast<int>(llama_n_ctx(context))) throw std::runtime_error("Prompt plus generation exceeds context; no silent truncation");
    auto * grammar_sampler=llama_sampler_init_grammar(vocab,grammar.c_str(),"root");
    if(!grammar_sampler) throw std::runtime_error("GBNF grammar could not be parsed");
    auto sp=llama_sampler_chain_default_params();
    std::unique_ptr<llama_sampler,decltype(&llama_sampler_free)> sampler(llama_sampler_chain_init(sp),llama_sampler_free);
    llama_sampler_chain_add(sampler.get(),grammar_sampler);
    llama_sampler_chain_add(sampler.get(),llama_sampler_init_greedy());
    const auto all_started=Clock::now();
    capturing=capture;
    if(llama_decode(context,llama_batch_get_one(tokens.data(),count))!=0) { capturing=false; throw std::runtime_error(cancelled.load()?"Generation cancelled":"Prompt evaluation failed"); }
    llama_synchronize(context);
    capturing=false;
    const double prefill_ms=elapsed(all_started);
    const auto decode_started=Clock::now();
    std::string output;
    int generated=0;
    bool eos=false;
    for(;generated<maximum;++generated) {
        if(cancelled.load()||closing.load()) throw std::runtime_error("Generation cancelled");
        const llama_token token=llama_sampler_sample(sampler.get(),context,-1);
        if(llama_vocab_is_eog(vocab,token)) { eos=true; break; }
        char piece[512];
        const int length=llama_token_to_piece(vocab,token,piece,sizeof(piece),0,false);
        if(length<0) throw std::runtime_error("Token piece exceeds buffer");
        output.append(piece,length);
        llama_token next=token;
        if(llama_decode(context,llama_batch_get_one(&next,1))!=0) throw std::runtime_error(cancelled.load()?"Generation cancelled":"Token evaluation failed");
    }
    std::ostringstream result;
    result<<std::setprecision(8)<<"{\"text\":"<<escape_json(output)<<",\"metrics\":{\"prompt_tokens\":"<<count
        <<",\"generated_tokens\":"<<generated<<",\"prefill_ms\":"<<prefill_ms<<",\"decode_ms\":"<<elapsed(decode_started)
        <<",\"total_ms\":"<<elapsed(all_started)<<",\"reached_eos\":"<<(eos?"true":"false")
        <<",\"context_setup_ms\":"<<context_setup_ms<<",\"cpu_only\":true,\"capture_enabled\":"<<(capture?"true":"false")<<"},\"activations\":[";
    bool first=true;
    for(const auto & event:activations) {
        if(!first) result<<',';first=false;
        result<<"{\"tensor\":"<<escape_json(event.name)<<",\"width\":"<<event.width<<",\"positions_in_chunk\":"<<event.positions
            <<",\"mean\":"<<event.mean<<",\"rms\":"<<event.rms<<",\"min\":"<<event.minimum<<",\"max\":"<<event.maximum<<",\"first_values\":[";
        for(size_t i=0;i<event.first_values.size();++i) {if(i)result<<',';result<<event.first_values[i];}
        result<<"]}";
    }
    result<<"]}"; return result.str();
}
