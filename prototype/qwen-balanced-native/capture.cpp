#include "llama.h"
#include <chrono>
#include <fstream>
#include <iostream>
#include <memory>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <vector>
#include <iomanip>
using Clock=std::chrono::steady_clock;
static double ms(Clock::time_point start){return std::chrono::duration<double,std::milli>(Clock::now()-start).count();}
static std::string quote(const std::string & s){std::ostringstream o;o<<'"';for(unsigned char c:s){switch(c){case '"':o<<"\\\"";break;case '\\':o<<"\\\\";break;case '\n':o<<"\\n";break;case '\r':o<<"\\r";break;case '\t':o<<"\\t";break;default:if(c<32)o<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<(int)c<<std::dec;else o<<c;}}o<<'"';return o.str();}
static const std::string alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
static std::string b64(const std::string&s){std::string r;unsigned v=0;int bits=-6;for(unsigned char c:s){v=(v<<8)+c;bits+=8;while(bits>=0){r+=alphabet[(v>>bits)&63];bits-=6;}}if(bits>-6)r+=alphabet[((v<<8)>>(bits+8))&63];while(r.size()%4)r+='=';return r;}
static std::string unb64(const std::string&s){if(s.empty()||s.size()%4||s.size()>16000)throw std::runtime_error("Invalid base64 size");std::string r;unsigned v=0;int bits=-8;bool ended=false;for(char c:s){if(c=='='){ended=true;continue;}auto p=alphabet.find(c);if(ended||p==std::string::npos)throw std::runtime_error("Invalid base64 encoding");v=(v<<6)+(unsigned)p;bits+=6;if(bits>=0){r+=char((v>>bits)&255);bits-=8;}}if(b64(r)!=s||r.empty()||r.size()>12000||r.find('\0')!=std::string::npos)throw std::runtime_error("Noncanonical bounded base64");return r;}
static std::string read(const char*p,size_t maximum){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("Input unavailable");std::string s((std::istreambuf_iterator<char>(f)),{});if(s.empty()||s.size()>maximum)throw std::runtime_error("Input size exceeded");return s;}
struct Row{std::string id,prompt;};
static std::vector<Row> rows(const char*p){std::string raw=read(p,1024*1024);if(raw.back()!='\n')throw std::runtime_error("Terminal newline required");std::istringstream lines(raw);std::vector<Row> out;std::set<std::string> ids;std::string line;while(std::getline(lines,line)){auto at=line.find('\t');if(at==std::string::npos||line.find('\t',at+1)!=std::string::npos)throw std::runtime_error("Two columns required");std::string id=line.substr(0,at);if(!std::regex_match(id,std::regex("[A-Za-z0-9_-]{1,64}"))||!ids.insert(id).second)throw std::runtime_error("Unique bounded ID required");out.push_back({id,unb64(line.substr(at+1))});}if(out.empty()||out.size()>200)throw std::runtime_error("1-200 rows required");return out;}
int main(int argc,char**argv){try{
 if(argc==3&&std::string(argv[1])=="--check-input"){auto r=rows(argv[2]);std::cout<<r.size()<<"\n";return 0;}
 if(argc!=5)throw std::runtime_error("model, optional adapter or -, prompts, grammar required");
 auto requests=rows(argv[3]);auto grammar=read(argv[4],4096);
 llama_backend_init();auto mp=llama_model_default_params();static ggml_backend_dev_t cpu_only[]={nullptr};mp.devices=cpu_only;mp.n_gpu_layers=0;mp.use_mmap=true;
 auto load_start=Clock::now();
 std::unique_ptr<llama_model,decltype(&llama_model_free)> model(llama_model_load_from_file(argv[1],mp),llama_model_free);if(!model)throw std::runtime_error("Model load failed");
 llama_adapter_lora *adapter=nullptr; if(std::string(argv[2])!="-"){adapter=llama_adapter_lora_init(model.get(),argv[2]);if(!adapter)throw std::runtime_error("Adapter load failed");}
 auto cp=llama_context_default_params();cp.n_ctx=1024;cp.n_batch=1024;cp.n_ubatch=256;cp.n_seq_max=1;cp.n_threads=4;cp.n_threads_batch=4;cp.offload_kqv=false;cp.op_offload=false;cp.cb_eval=nullptr;cp.cb_eval_user_data=nullptr;
 auto *vocab=llama_model_get_vocab(model.get());std::cout<<std::setprecision(10)<<"{\"phase\":\"load\",\"load_ms\":"<<ms(load_start)<<",\"adapter\":"<<(adapter?"true":"false")<<"}\n"<<std::flush;
 for(const auto&row:requests){auto setup=Clock::now();std::unique_ptr<llama_context,decltype(&llama_free)> ctx(llama_init_from_model(model.get(),cp),llama_free);if(!ctx)throw std::runtime_error("Context load failed");if(adapter){float scale=1.0f;if(llama_set_adapters_lora(ctx.get(),&adapter,1,&scale)!=0)throw std::runtime_error("Adapter attachment failed");}double context_setup=ms(setup);llama_memory_clear(llama_get_memory(ctx.get()),true);int count=llama_tokenize(vocab,row.prompt.data(),row.prompt.size(),nullptr,0,true,true);if(count>=0)throw std::runtime_error("Tokenizer sizing failed");std::vector<llama_token> tokens(-count);count=llama_tokenize(vocab,row.prompt.data(),row.prompt.size(),tokens.data(),tokens.size(),true,true);if(count<=0||count+128>(int)llama_n_ctx(ctx.get()))throw std::runtime_error("Context overflow");
 auto*gbnf=llama_sampler_init_grammar(vocab,grammar.c_str(),"root");if(!gbnf)throw std::runtime_error("Grammar parse failed");std::unique_ptr<llama_sampler,decltype(&llama_sampler_free)> sampler(llama_sampler_chain_init(llama_sampler_chain_default_params()),llama_sampler_free);llama_sampler_chain_add(sampler.get(),gbnf);llama_sampler_chain_add(sampler.get(),llama_sampler_init_greedy());
 auto all=Clock::now();if(llama_decode(ctx.get(),llama_batch_get_one(tokens.data(),count))!=0)throw std::runtime_error("Prefill failed");llama_synchronize(ctx.get());double prefill=ms(all);auto decode=Clock::now();std::string output;int generated=0;bool eos=false;
 for(;generated<128;++generated){auto token=llama_sampler_sample(sampler.get(),ctx.get(),-1);if(llama_vocab_is_eog(vocab,token)){eos=true;break;}char piece[512];int n=llama_token_to_piece(vocab,token,piece,sizeof(piece),0,false);if(n<0)throw std::runtime_error("Token piece overflow");output.append(piece,n);if(llama_decode(ctx.get(),llama_batch_get_one(&token,1))!=0)throw std::runtime_error("Decode failed");}
 if(!eos)throw std::runtime_error("Missing real EOS: capture incomplete");
 std::cout<<"{\"id\":"<<quote(row.id)<<",\"text\":"<<quote(output)<<",\"metrics\":{\"prompt_tokens\":"<<count<<",\"generated_tokens\":"<<generated<<",\"prefill_ms\":"<<prefill<<",\"decode_ms\":"<<ms(decode)<<",\"total_ms\":"<<ms(all)<<",\"context_setup_ms\":"<<context_setup<<",\"reached_eos\":true,\"cpu_only\":true,\"capture_enabled\":false}}\n"<<std::flush;
 }
 return 0;
 }catch(const std::exception&e){std::cerr<<"CAPTURE_FAILED: "<<e.what()<<"\n";return 2;}}
